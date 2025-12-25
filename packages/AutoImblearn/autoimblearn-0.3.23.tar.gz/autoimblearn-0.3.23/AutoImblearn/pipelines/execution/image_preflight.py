import logging
import inspect
from typing import Iterable, List, Optional, Set

from AutoImblearn.components.model_client.image_spec import ImageSpec, DockerImageProvider
from .image_registry import image_exists
from .image_builder import build_image

logger = logging.getLogger("autoimblearn.preflight")


def _collect_specs(providers: Iterable[DockerImageProvider]) -> List[ImageSpec]:
    specs: List[ImageSpec] = []
    for provider in providers:
        if not provider:
            continue
        instance = provider
        if inspect.isclass(provider):
            instance = _instantiate_provider(provider)
        if not instance:
            continue
        try:
            spec = instance.get_image_spec()
        except Exception:
            continue
        if spec:
            specs.append(spec)
    return specs


def _instantiate_provider(cls):
    attempts = [
        lambda: cls(host_data_root="."),
        lambda: cls("."),
        lambda: cls(),
    ]
    for attempt in attempts:
        try:
            return attempt()
        except TypeError:
            continue
        except Exception:
            continue
    return None


def _dedupe_specs(specs: List[ImageSpec]) -> List[ImageSpec]:
    seen: Set[str] = set()
    unique: List[ImageSpec] = []
    for spec in specs:
        key = f"{spec.image}:{spec.tag}" if spec.tag else spec.image
        if key in seen:
            continue
        seen.add(key)
        unique.append(spec)
    return unique


def prepare_images(providers: Iterable[DockerImageProvider], allow_build: bool = True) -> None:
    """Ensure all required images exist before execution."""
    specs = _dedupe_specs(_collect_specs(providers))
    for spec in specs:
        tag = f"{spec.image}:{spec.tag}" if spec.tag else spec.image
        if image_exists(spec):
            logger.info("[preflight] image present: %s", tag)
            continue
        if not allow_build:
            raise RuntimeError(f"Docker image '{tag}' missing. Preflight cannot continue.")
        build_image(spec)
