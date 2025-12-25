import logging
from typing import Optional

import docker
from docker.errors import ImageNotFound

from AutoImblearn.components.model_client.image_spec import ImageSpec

logger = logging.getLogger("autoimblearn.preflight")


def image_exists(spec: ImageSpec) -> bool:
    client = docker.from_env()
    candidates = [spec.image if not spec.tag else f"{spec.image}:{spec.tag}"]
    if not spec.tag:
        candidates.append(f"{spec.image}:latest")
    for candidate in candidates:
        try:
            client.images.get(candidate)
            return True
        except ImageNotFound:
            continue
    return False
