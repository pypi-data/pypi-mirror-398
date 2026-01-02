### TechTrash_MusubiTraining

Petite librairie Python pour automatiser un training “photo” avec **Musubi Tuner**:

- Prépare un dataset (téléchargement d’un zip d’images + captions).
- Lance le **pre-cache** (VAE latents + text encoder outputs).
- Lance le **training** via `accelerate launch`.
- Convertit optionnellement le LoRA au format **ComfyUI**.

---

### Pour les utilisateurs (simple)

#### Prérequis

- **Python 3.11+**
- Un clone local de **Musubi Tuner** (le repo qui contient `zimage_train_network.py`)
- Les modèles `.safetensors` (DiT / VAE / text encoder / base weights)

Notes:
- Cette lib lance des scripts externes. Donc ton environnement Python doit avoir `accelerate` installé.
- Le code utilise aussi `requests` et `pynvml`.

#### Installation (dev / local)

Depuis `Libs-MusubiTraining/`:

```bash
pip install -e .
```

#### Exemple minimal (init + train)

Tu dois fournir des **chemins absolus**:

- `absolute_path_models`: dossier qui contient tes `.safetensors`
- `absolute_path_training_folder`: dossier de travail (dataset.toml, images/, cache/, etc.)
- `absolute_path_output`: dossier où le training écrit le modèle final
- `absolute_path_musubi_tuner`: dossier du repo Musubi Tuner

Ensuite:

- `dataset_toml_content`: le contenu TOML en string (il est validé avant écriture)
- `images_zip_url`: une URL vers un `.zip` contenant des images
- `trigger_word`: un texte qui sera écrit dans chaque `.txt` (caption)

Exemple:

```python
from musubitraining.main import MusubiTraining, Models

models = Models(
    ae="ae.safetensors",
    text_encoder="qwen_3_4b.safetensors",
    DiT="z_image_de_turbo_v1_bf16.safetensors",
    base_weights="zimage_turbo_training_adapter_v2.safetensors",
)

trainer = MusubiTraining(
    absolute_path_models="/workspace/models",
    models_for_training=models,
    absolute_path_training_folder="/workspace/my-training-run",
    absolute_path_output="/workspace/outputs",
    absolute_path_musubi_tuner="/workspace/musubi-tuner",
)

# IMPORTANT:
# `image_directory` and `cache_directory` MUST match what the code creates:
# - {absolute_path_training_folder}/images
# - {absolute_path_training_folder}/cache
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
image_directory = "{trainer.absolute_path_training_folder}/images"
cache_directory = "{trainer.absolute_path_training_folder}/cache"
"""

model_path = trainer.train(
    dataset_toml_content=dataset_toml_content,
    images_zip_url="https://example.com/my_images.zip",
    trigger_word="my_trigger_word",
    # Par défaut: pre-cache ON, conversion ComfyUI ON
    # use_pre_cache=True,
    # convert_for_comfyui=True,
    output_name="output_lora_model",
    max_train_steps=2000,
    seed=42,
)

print("Model created:", model_path)
```

#### Exemple de `dataset.toml` (valide)

Ce fichier est écrit automatiquement dans:
- `{absolute_path_training_folder}/dataset.toml`

La partie importante: les chemins doivent correspondre à ce que la lib crée:
- `image_directory = "{absolute_path_training_folder}/images"`
- `cache_directory = "{absolute_path_training_folder}/cache"`

Modèle de base (celui-ci est valide TOML):

```toml
# resolution, caption_extension, batch_size, num_repeats, enable_bucket, bucket_no_upscale should be set in either general or datasets
# otherwise, the default values will be used for each item

# general configurations
[general]
resolution = [1024, 1024]
caption_extension = ".txt"
batch_size = 1
enable_bucket = true
bucket_no_upscale = false

[[datasets]]
image_directory = "/ABS/PATH/TO/YOUR/TRAINING_FOLDER/images"
cache_directory = "/ABS/PATH/TO/YOUR/TRAINING_FOLDER/cache"
```

#### Output (ce que retourne `train()`)

- Si `convert_for_comfyui=True` (par défaut): retourne le chemin du fichier:
  - `.../{output_name}_comfyui.safetensors`
- Sinon: retourne le chemin du fichier:
  - `.../{output_name}.safetensors`

---

### Pour les devs (compréhension du projet)

#### Où est le code

- Code principal: `src/musubitraining/main.py`

#### API principale

- **`Models`** (dataclass):
  - Stocke les noms de fichiers `.safetensors` attendus dans `absolute_path_models`.
- **`MusubiTraining`**:
  - `__init__(...)`: stocke les chemins absolus et fait quelques checks.
  - `_prepare_dataset(...)`: crée `dataset.toml`, télécharge et extrait le zip d’images, crée les captions.
  - `_pre_cache(...)`: lance 2 scripts Musubi Tuner pour pré-calculer les caches.
  - `_launch_training(...)`: lance le training via `python -m accelerate launch ...` et retourne le chemin du modèle final `.safetensors`.
  - `_convert_for_comfyui(...)`: convertit un LoRA “z-image” vers un LoRA compatible ComfyUI et retourne le chemin du fichier converti.
  - `train(...)`: orchestre tout et retourne le chemin final.

#### Choix techniques importants

- **Validation TOML “fail fast”**:
  - `_validate_toml_str()` parse le TOML avant écriture.
  - Ça évite de découvrir des erreurs plus tard dans le training.
- **Pas de `os.system`**:
  - On utilise `subprocess.run([...], check=True)` pour:
    - gérer les chemins avec espaces,
    - remonter les erreurs correctement,
    - éviter les commandes multi-lignes fragiles.
- **Exécution dans le bon env**:
  - On utilise `sys.executable` pour exécuter `accelerate` et les scripts.
  - Ça aide à éviter les bugs “pas le bon python”.

#### Limites / points à améliorer (connus)

- `_prepare_dataset()` écrit la même caption (`trigger_word`) pour toutes les images.
  - C’est volontairement simple, mais tu peux l’étendre.
- Si tu veux un vrai “runner” propre, on peut:
  - ajouter des logs,
  - capturer stdout/stderr,
  - ajouter une config plus riche pour les params d’entraînement.


