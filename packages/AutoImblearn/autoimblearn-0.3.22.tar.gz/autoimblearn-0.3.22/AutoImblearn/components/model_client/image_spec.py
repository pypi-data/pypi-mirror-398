from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ImageSpec:
    """Immutable Docker image requirement."""
    image: str
    context: Optional[Path]
    dockerfile: Optional[Path] = None
    tag: Optional[str] = None


class DockerImageProvider:
    """Interface for Docker-backed models to declare their image spec."""
    def get_image_spec(self) -> Optional[ImageSpec]:
        raise NotImplementedError
