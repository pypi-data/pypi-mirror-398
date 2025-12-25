# AutoImblearn/components/model_client/base_model_client.py
import os
import pandas as pd
import numpy as np
import logging
from abc import ABC, abstractmethod

from .image_spec import DockerImageProvider, ImageSpec


class BaseDockerModelClient(DockerImageProvider, ABC):
    """Declarative base for Docker-backed models (no side effects)."""

    def __init__(
        self,
        image_spec: ImageSpec,
        container_name,
        container_port=5000,
        host_data_root=None,
        container_data_root="/data",
        docker_sock="/var/run/docker.sock",
        mount_mode="rw",
        is_transformer=False,
    ):
        if not host_data_root:
            raise ValueError("host_data_root is required for Docker-backed models")

        self._image_spec = image_spec
        self.image_name = image_spec.image
        self.container_name = container_name
        self.container_port = container_port

        self.host_data_root = host_data_root
        self.container_data_root = container_data_root
        self.docker_sock = docker_sock
        self.mount_mode = mount_mode

        self.args = None
        self.container_id = None  # Initialize container_id
        self.is_transformer = is_transformer  # True for imputers/transformers, False for classifiers
        self.allow_runtime_build = bool(int(os.environ.get("AUTOIMBLEARN_ALLOW_RUNTIME_IMAGE_BUILD", "0")))
        self.params = {}

    def get_image_spec(self):
        return self._image_spec

    def get_volume_mounts(self):
        return {
            self.host_data_root: {"bind": self.container_data_root, "mode": self.mount_mode},
            self.docker_sock: {"bind": self.docker_sock, "mode": "rw"},
        }

    @property
    @abstractmethod
    def payload(self):
        """Subclasses must return a dict with key arguments."""
        raise NotImplementedError("Subclass must define 'payload'")

    # The remaining methods here represent execution-side behaviors.
    # They still exist to avoid breaking APIs, but Docker creation/path
    # resolution should be handled in the runner layer.

    def save_result(self):
        # Deprecated in declarative base; execution layer should handle persistence.
        raise NotImplementedError("save_result is deprecated in BaseDockerModelClient")

    def set_params(self, params):
        logging.debug("Parameters:")
        logging.debug(params)
        self.params = params
        return params
