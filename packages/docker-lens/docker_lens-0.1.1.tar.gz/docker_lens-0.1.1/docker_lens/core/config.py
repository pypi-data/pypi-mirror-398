import os
import yaml

from docker_lens.core.constants import DEFAULT_IMAGES, DEFAULT_IMAGE_PROFILE

CONFIG_PATH = os.path.expanduser("~/.config/docker-lens/config.yaml")

DEFAULT_CONFIG = {
    "default_image": DEFAULT_IMAGES.get(DEFAULT_IMAGE_PROFILE),
}
def load_config() -> str:
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(
                DEFAULT_CONFIG,
                f,
                default_flow_style=False,
                sort_keys=False,
            )

        return DEFAULT_CONFIG.get("default_image")

    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f).get("default_image")

def save_config(image):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(
                {"default_image": image},
                f,
                default_flow_style=False,
                sort_keys=False,
            )
