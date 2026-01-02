from main import MusubiTraining
from main import Models

dataset_toml_content = """
[general]
resolution = [1024, 1024]
caption_extension = ".txt"
batch_size = 1
enable_bucket = true
bucket_no_upscale = false
"""

images_zip_url = "https://s3.gra.io.cloud.ovh.net/s3-nextprotocol/photomaintenant/checkface/02868266-199d-4ea3-b0d0-b06e6e70fb65.zip?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ebbe6df1abe7432496a033c81d744cee%2F20251227%2Fgra%2Fs3%2Faws4_request&X-Amz-Date=20251227T122154Z&X-Amz-Expires=604800&X-Amz-SignedHeaders=host&X-Amz-Signature=fda59ff7b494df712f2772b878178955590dde6b1bcf09206867c2f85f5b0c7c"
trigger_word = "ohwx woman"

musubi_training = MusubiTraining(
    absolute_path_models="/Users/wglint/Desktop/NEXTProtocol/Runpod/Training/Pod/models",
    models_for_training=Models(),
    absolute_path_training_folder="training",
    absolute_path_output="output",
    absolute_path_musubi_tuner="/Users/wglint/Desktop/NEXTProtocol/Runpod/Training/Pod/models"
)

musubi_training.train(
    dataset_toml_content=dataset_toml_content,
    images_zip_url=images_zip_url,
    trigger_word=trigger_word
)