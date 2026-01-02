from dataclasses import dataclass
from typing import Any, Literal
import logging
import time
import requests
import zipfile
import os
import subprocess
import sys
import shutil

# TOML parsing:
# - Python 3.11+: `tomllib` (stdlib)
# - Python 3.10 and below: use `tomli` as a drop-in replacement
try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

logger = logging.getLogger("musubitraining")

GPU = Literal[
    "RTX 4090", "RTX 5090", "RTX 6000 Ada", "A40", "H100", "A100", "B200", "H200", "Unknown GPU"
]

class GPUMonitor:
    def __init__(self):
        # GPU monitoring is optional in this project.
        # We import NVML lazily because:
        # - some environments don't have it,
        # - `pynvml` is deprecated and can spam warnings,
        # - most workflows don't need GPU name detection.
        try:
            import pynvml  # type: ignore
        except ModuleNotFoundError as e:  # pragma: no cover
            raise RuntimeError(
                "GPU monitoring requires `pynvml` (or an NVML-compatible setup). "
                "Install it, or avoid using `GPUMonitor`."
            ) from e

        self._pynvml = pynvml

        self._pynvml.nvmlInit()
        self.gpu_count = self._pynvml.nvmlDeviceGetCount()
        self.gpu_name = self.get_gpu_name()
        self._pynvml.nvmlShutdown()

    def get_gpu_name(self) -> GPU:
        handle = self._pynvml.nvmlDeviceGetHandleByIndex(0)  # type: ignore
        name = self._pynvml.nvmlDeviceGetName(handle)  # type: ignore
        if isinstance(name, bytes):
            name = name.decode("utf-8")
        name = str(name)

        match name:
            case _ if "4090" in name:
                return "RTX 4090"
            case _ if "5090" in name:
                return "RTX 5090"
            case _ if "6000 Ada" in name:
                return "RTX 6000 Ada"
            case _ if "A40" in name:
                return "A40"
            case _ if "H100" in name:
                return "H100"
            case _ if "A100" in name:
                return "A100"
            case _ if "B200" in name:
                return "B200"
            case _ if "H200" in name:
                return "H200"
            case _:
                return "Unknown GPU"

@dataclass
class Models:
    ae: str = "ae.safetensors"
    text_encoder: str = "qwen_3_4b.safetensors"
    DiT: str = "z_image_de_turbo_v1_bf16.safetensors"
    base_weights: str = "zimage_turbo_training_adapter_v2.safetensors"

class MusubiTraining:
    def __init__(self, absolute_path_models: str, models_for_training: Models, 
                       absolute_path_training_folder: str, absolute_path_output: str, absolute_path_musubi_tuner: str):
        super().__init__()

        # If the user did not configure logging, set a simple default.
        # This ensures "good logs" by default in container stdout.
        root_logger = logging.getLogger()
        if not root_logger.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            )
        
        self.absolute_path_models = absolute_path_models
        self.models_for_training = models_for_training
        self.absolute_path_training_folder = absolute_path_training_folder
        self.absolute_path_output = absolute_path_output
        self.absolute_path_musubi_tuner = absolute_path_musubi_tuner

        if not os.path.exists(self.absolute_path_models):
            raise FileNotFoundError(f"Models folder not found: {self.absolute_path_models}")
        if not os.path.exists(self.absolute_path_musubi_tuner):
            raise FileNotFoundError(f"Musubi Tuner github project folder not found: {self.absolute_path_musubi_tuner}")
        if not os.path.exists(self.absolute_path_output):
            # We create it early so training can always write outputs.
            os.makedirs(self.absolute_path_output)

    def _run_cmd(self, step: str, cmd: list[str], *, cwd: str) -> None:
        """
        Run a command and stream its output to logs in real-time.

        Why:
        - Training scripts run for a long time.
        - If we only raise an exception at the end, it's impossible to debug from logs.
        """
        t0 = time.time()
        logger.info("[%s] starting", step)
        logger.info("[%s] cwd=%s", step, cwd)
        logger.info("[%s] cmd=%s", step, " ".join(cmd))

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            logger.info("[%s] %s", step, line.rstrip("\n"))

        rc = proc.wait()
        dt = time.time() - t0
        if rc != 0:
            logger.error("[%s] failed (exit_code=%s, duration=%.1fs)", step, rc, dt)
            raise subprocess.CalledProcessError(rc, cmd)

        logger.info("[%s] done (duration=%.1fs)", step, dt)

    def _validate_toml_str(self, toml_content: str) -> dict[str, Any]:
        """
        Validate that a string is valid TOML.

        Why we do this:
        - A plain `f.write(...)` will write *anything*, even invalid TOML.
        - Later, the trainer will fail, but with a confusing error far from here.
        - Parsing early lets us fail fast with a clear message.
        """
        try:
            # `tomllib.loads` raises `tomllib.TOMLDecodeError` if the string is not valid TOML.
            return tomllib.loads(toml_content)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(
                "Invalid TOML provided for `dataset_toml_content`. "
                "Please fix the TOML format (syntax, quotes, brackets)."
            ) from e

    def _prepare_dataset(self, dataset_toml_content: str, images_zip_url: str, trigger_word: str) -> str:
        logger.info("[dataset] preparing dataset folder=%s", self.absolute_path_training_folder)
        abs_images_folder = os.path.join(self.absolute_path_training_folder, "images")
        abs_cache_folder = os.path.join(self.absolute_path_training_folder, "cache")
        abs_dataset_toml = os.path.join(self.absolute_path_training_folder, "dataset.toml")
        abs_images_zip = os.path.join(self.absolute_path_training_folder, "images.zip")
        
        if not os.path.exists(self.absolute_path_training_folder):
            os.makedirs(self.absolute_path_training_folder)

        # Validate TOML BEFORE writing it to disk.
        # This guarantees that `dataset.toml` is always syntactically valid TOML.
        self._validate_toml_str(dataset_toml_content)

        # IMPORTANT (production robustness):
        # Jobs can restart / retry on the same worker. That means old files may still exist under:
        # - /app/training/images
        # - /app/training/cache
        # If we reuse them, we can get non-deterministic behavior (looks like "it fails once then works").
        # So we always start from a clean slate.
        if os.path.exists(abs_images_folder):
            shutil.rmtree(abs_images_folder)
        os.makedirs(abs_images_folder, exist_ok=True)

        if os.path.exists(abs_cache_folder):
            shutil.rmtree(abs_cache_folder)
        os.makedirs(abs_cache_folder, exist_ok=True)

        # Clean any leftover zip from a previous run (partial download, interrupted write, etc.).
        if os.path.exists(abs_images_zip):
            os.remove(abs_images_zip)

        # Create the dataset.toml file
        with open(abs_dataset_toml, "w") as f:
            f.write(dataset_toml_content)
        logger.info("[dataset] wrote dataset.toml=%s", abs_dataset_toml)

        # Be careful: signed URLs can be extremely long; keep logs readable.
        logger.info("[dataset] downloading images zip (url=%s...)", images_zip_url[:120])
        response_zip = requests.get(images_zip_url, timeout=60)
        response_zip.raise_for_status()
        logger.info("[dataset] downloaded zip bytes=%s", len(response_zip.content))

        with open(abs_images_zip, "wb") as f:
            f.write(response_zip.content)

        with zipfile.ZipFile(abs_images_zip, "r") as zip_ref:
            zip_ref.extractall(abs_images_folder)

        kept = 0
        removed = 0
        for file in os.listdir(abs_images_folder):
            # Keep only jpg / jpeg files.
            # NOTE: the previous condition used `or` and was always True, so it deleted everything.
            lower = file.lower()
            if not (lower.endswith(".jpg") or lower.endswith(".jpeg")):
                os.remove(os.path.join(abs_images_folder, file))
                removed += 1
            else:
                # create the caption file
                with open(os.path.join(abs_images_folder, file.replace(".jpg", ".txt").replace(".jpeg", ".txt")), "w") as f:
                    f.write(trigger_word)
                kept += 1
        logger.info("[dataset] images kept=%s removed=%s images_dir=%s", kept, removed, abs_images_folder)

        # Fail fast with a clear error instead of a downstream traceback during pre-caching.
        if kept == 0:
            raise ValueError(
                "Dataset is empty after extraction/filtering. "
                f"images_dir={abs_images_folder}. "
                "This can happen if the zip is empty/corrupt, or if files are not .jpg/.jpeg."
            )

        os.remove(abs_images_zip)

        return abs_dataset_toml

    def _pre_cache(self, dataset_toml_path: str) -> None:
        """
        Pre-cache the text encoder outputs and the latents.
        """

        # Why we avoid `os.system(...)` here:
        # - It does NOT raise on failure (you might silently continue after a crash).
        # - It breaks easily when paths contain spaces (very common on macOS).
        # - Your "\" line continuations are fragile because indentation can add trailing spaces,
        #   which makes the backslash NOT escape the newline in the shell.
        #
        # `subprocess.run([...], check=True)` fixes all of this and keeps the code simple.

        if not os.path.exists(dataset_toml_path):
            raise FileNotFoundError(f"dataset.toml not found: {dataset_toml_path}")

        script_vae_cache = os.path.join(self.absolute_path_musubi_tuner, "zimage_cache_latents.py")
        script_text_cache = os.path.join(self.absolute_path_musubi_tuner, "zimage_cache_text_encoder_outputs.py")
        if not os.path.exists(script_vae_cache):
            raise FileNotFoundError(f"Musubi script not found: {script_vae_cache}")
        if not os.path.exists(script_text_cache):
            raise FileNotFoundError(f"Musubi script not found: {script_text_cache}")

        abs_vae = os.path.join(self.absolute_path_models, self.models_for_training.ae)
        abs_text_encoder = os.path.join(self.absolute_path_models, self.models_for_training.text_encoder)
        if not os.path.exists(abs_vae):
            raise FileNotFoundError(f"VAE weights not found: {abs_vae}")
        if not os.path.exists(abs_text_encoder):
            raise FileNotFoundError(f"Text encoder weights not found: {abs_text_encoder}")

        # PRE-CACHE THE VAE / latents
        self._run_cmd(
            "precache:latents",
            [sys.executable, script_vae_cache, "--dataset_config", dataset_toml_path, "--vae", abs_vae],
            cwd=self.absolute_path_musubi_tuner,
        )

        # PRE CACHE THE TEXT ENCODER OUTPUTS
        self._run_cmd(
            "precache:text_encoder",
            [
                sys.executable,
                script_text_cache,
                "--dataset_config",
                dataset_toml_path,
                "--text_encoder",
                abs_text_encoder,
                "--batch_size",
                "16",
            ],
            cwd=self.absolute_path_musubi_tuner,
        )

        return None

    def _launch_training(
        self,
        dataset_toml_path: str,
        *,
        output_name: str = "output_lora_model",
        max_train_steps: int = 2000,
        seed: int = 42,
    ) -> str:
        """
        Launch the actual training using the official README command.

        Notes:
        - We use `python -m accelerate launch ...` instead of a shell string.
          This makes it robust to spaces in paths and correctly fails on errors.
        - We keep defaults close to the README "ostris-style default".
        """

        # Fail early with clear errors (much nicer than a long stacktrace from deep inside training).
        if not os.path.exists(dataset_toml_path):
            raise FileNotFoundError(f"dataset.toml not found: {dataset_toml_path}")

        # `accelerate` is required by the README command.
        try:
            import accelerate  # type: ignore # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "Missing dependency: `accelerate`. Install it in your environment "
                "(the same python that runs this code) before calling `train()`."
            ) from e

        script_train = os.path.join(self.absolute_path_musubi_tuner, "zimage_train_network.py")
        if not os.path.exists(script_train):
            raise FileNotFoundError(f"Musubi training script not found: {script_train}")

        abs_dit = os.path.join(self.absolute_path_models, self.models_for_training.DiT)
        abs_vae = os.path.join(self.absolute_path_models, self.models_for_training.ae)
        abs_text_encoder = os.path.join(self.absolute_path_models, self.models_for_training.text_encoder)
        abs_base_weights = os.path.join(self.absolute_path_models, self.models_for_training.base_weights)

        for p in (abs_dit, abs_vae, abs_text_encoder, abs_base_weights):
            if not os.path.exists(p):
                raise FileNotFoundError(f"Model weights not found: {p}")

        # `accelerate` CLI is the most compatible way to launch training.
        # Some environments do NOT support `python -m accelerate` because the package has no `accelerate.__main__`.
        accelerate_exe = shutil.which("accelerate")

        # Important:
        # - We pass args as a list (no quoting needed).
        cmd: list[str] = [
            accelerate_exe or sys.executable,
            *([] if accelerate_exe else ["-m", "accelerate.commands.launch"]),
            "launch",
            "--num_cpu_threads_per_process",
            "1",
            "--mixed_precision",
            "bf16",
            script_train,
            "--dit",
            abs_dit,
            "--vae",
            abs_vae,
            "--text_encoder",
            abs_text_encoder,
            "--base_weights",
            abs_base_weights,
            "--dataset_config",
            dataset_toml_path,
            "--sdpa",
            "--mixed_precision",
            "bf16",
            "--timestep_sampling",
            "sigmoid",
            "--weighting_scheme",
            "none",
            "--optimizer_type",
            "adamw8bit",
            "--learning_rate",
            "2e-4",
            "--optimizer_args",
            "weight_decay=0.0001",
            "--gradient_checkpointing",
            "--max_train_steps",
            str(max_train_steps),
            "--seed",
            str(seed),
            "--network_module",
            "networks.lora_zimage",
            "--network_dim",
            "16",
            "--network_alpha",
            "16",
            "--output_dir",
            self.absolute_path_output,
            "--output_name",
            output_name,
        ]

        self._run_cmd("train", cmd, cwd=self.absolute_path_musubi_tuner)

        return os.path.join(self.absolute_path_output, f"{output_name}.safetensors")

    def _convert_for_comfyui(self, model_path: str) -> str:
        """
        Convert a trained z-image LoRA to a ComfyUI-compatible LoRA.

        README reference:
        python3 musubi-tuner/src/musubi_tuner/networks/convert_z_image_lora_to_comfy.py \
            --model_path /workspace/outputs/output_lora_model.safetensors \
            --output_path /workspace/outputs/output_lora_model_comfyui.safetensors
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Trained model not found: {model_path}")

        convert_script = os.path.join(
            self.absolute_path_musubi_tuner,
            "src",
            "musubi_tuner",
            "networks",
            "convert_z_image_lora_to_comfy.py",
        )
        if not os.path.exists(convert_script):
            raise FileNotFoundError(f"Conversion script not found: {convert_script}")

        # Default output next to the input file, with a clear suffix.
        # We keep it simple and predictable for users.
        if model_path.endswith(".safetensors"):
            output_path = model_path.replace(".safetensors", "_comfyui.safetensors")
        else:
            output_path = f"{model_path}_comfyui.safetensors"

        # Some versions of the script require flags, some accept positional args.
        # We try the README-style flags first, then fallback to positional args.
        try:
            self._run_cmd(
                "convert:comfyui",
                [sys.executable, convert_script, "--model_path", model_path, "--output_path", output_path],
                cwd=self.absolute_path_musubi_tuner,
            )
        except subprocess.CalledProcessError:
            self._run_cmd(
                "convert:comfyui",
                [sys.executable, convert_script, model_path, output_path],
                cwd=self.absolute_path_musubi_tuner,
            )

        if not os.path.exists(output_path):
            # Defensive check: if the script succeeded but the file isn't there, something is off.
            raise FileNotFoundError(f"ComfyUI model was not created: {output_path}")

        return output_path

    def train(
        self,
        dataset_toml_content: str,
        images_zip_url: str,
        trigger_word: str,
        *,
        use_pre_cache: bool = True,
        convert_for_comfyui: bool = True,
        output_name: str = "output_lora_model",
        max_train_steps: int = 2000,
        seed: int = 42,
    ) -> str:
        logger.info(
            "[pipeline] start use_pre_cache=%s convert_for_comfyui=%s output_name=%s max_train_steps=%s seed=%s",
            use_pre_cache,
            convert_for_comfyui,
            output_name,
            max_train_steps,
            seed,
        )
        abs_dataset_toml = self._prepare_dataset(dataset_toml_content, images_zip_url, trigger_word)

        if use_pre_cache:
            self._pre_cache(dataset_toml_path=abs_dataset_toml)

        # Start the actual training step (this is the long-running part).
        trained_model_path = self._launch_training(
            dataset_toml_path=abs_dataset_toml,
            output_name=output_name,
            max_train_steps=max_train_steps,
            seed=seed,
        )

        # Optional: convert the final weights for ComfyUI usage.
        if convert_for_comfyui:
            final_path = self._convert_for_comfyui(model_path=trained_model_path)
            logger.info("[pipeline] done final_model=%s", final_path)
            return final_path
        
        else:
            logger.info("[pipeline] done final_model=%s", trained_model_path)
            return trained_model_path