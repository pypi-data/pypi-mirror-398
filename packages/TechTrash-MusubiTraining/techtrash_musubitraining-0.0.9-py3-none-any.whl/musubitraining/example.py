"""
Minimal usage example (copy/paste friendly).

Important:
- `image_directory` and `cache_directory` inside `dataset.toml` MUST match what the code creates:
  - {absolute_path_training_folder}/images
  - {absolute_path_training_folder}/cache
"""

from musubitraining.main import MusubiTraining, Models

# ---- Update these paths for your machine / container (use absolute paths) ----
ABS_MODELS_DIR = "/workspace/models"
ABS_TRAINING_DIR = "/workspace/my-training-run"
ABS_OUTPUT_DIR = "/workspace/outputs"
ABS_MUSUBI_TUNER_DIR = "/workspace/musubi-tuner"  # <- clone of Musubi Tuner repo

# ---- Your inputs ----
images_zip_url = "https://example.com/my_images.zip"
trigger_word = "my_trigger_word"

# Your real dataset.toml template (from the Musubi README),
# but with paths aligned to what `_prepare_dataset()` creates.
dataset_toml_content = f"""# resolution, caption_extension, batch_size, num_repeats, enable_bucket, bucket_no_upscale should be set in either general or datasets
# otherwise, the default values will be used for each item

# general configurations
[general]
resolution = [1024, 1024]
caption_extension = ".txt"
batch_size = 1
enable_bucket = true
bucket_no_upscale = false

[[datasets]]
image_directory = "{ABS_TRAINING_DIR}/images"
cache_directory = "{ABS_TRAINING_DIR}/cache"
"""

trainer = MusubiTraining(
    absolute_path_models=ABS_MODELS_DIR,
    models_for_training=Models(),
    absolute_path_training_folder=ABS_TRAINING_DIR,
    absolute_path_output=ABS_OUTPUT_DIR,
    absolute_path_musubi_tuner=ABS_MUSUBI_TUNER_DIR,
)

# Returns a path to the final weights:
# - by default: ".../{output_name}_comfyui.safetensors"
final_model_path = trainer.train(
    dataset_toml_content=dataset_toml_content,
    images_zip_url=images_zip_url,
    trigger_word=trigger_word,
    output_name="output_lora_model",
    max_train_steps=2000,
    seed=42,
)

print("Final model:", final_model_path)