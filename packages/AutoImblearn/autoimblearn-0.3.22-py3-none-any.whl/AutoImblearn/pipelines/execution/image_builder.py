import logging
from typing import Optional

import docker

from AutoImblearn.components.model_client.image_spec import ImageSpec

logger = logging.getLogger("autoimblearn.preflight")


def build_image(spec: ImageSpec) -> None:
    client = docker.from_env()
    tag = spec.image if not spec.tag else f"{spec.image}:{spec.tag}"
    context = str(spec.context) if spec.context else "."
    dockerfile = str(spec.dockerfile) if spec.dockerfile else None
    logger.info("[preflight] building image '%s' from %s", tag, context)
    client.images.build(path=context, tag=tag, dockerfile=dockerfile, nocache=True)
    logger.info("[preflight] built image '%s'", tag)
