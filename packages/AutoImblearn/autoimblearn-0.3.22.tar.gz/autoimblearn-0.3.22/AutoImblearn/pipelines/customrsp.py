# AutoImblearn/pipelines/customrsp.py
import logging
import json
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import importlib.util

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator

from AutoImblearn.components.resamplers import RunSmoteSampler, RunImblearnSampler

try:
    from AutoImblearn.components.model_client.base_transformer import BaseTransformer
    from AutoImblearn.components.model_client.image_spec import DockerImageProvider
except Exception:
    BaseTransformer = None
    DockerImageProvider = None


# Docker-based resamplers - factory functions similar to imputers
rsps: Dict[str, Callable[..., Any]] = {
    'rus': lambda **kw: RunImblearnSampler(model='rus', **kw),
    'ros': lambda **kw: RunImblearnSampler(model='ros', **kw),
    'smote': lambda **kw: RunImblearnSampler(model='smote', **kw),
    'mwmote': lambda **kw: RunSmoteSampler(model='mwmote', **kw),
}
_BUILTIN_RSP = set(rsps.keys())


def load_custom_components():
    registry_path = Path(__file__).resolve().parents[4] / "data" / "models" / "registry" / "resamplers.json"
    if not registry_path.exists():
        registry = []
    else:
        try:
            registry = json.loads(registry_path.read_text())
        except Exception:
            registry = []
    components_root = Path(__file__).resolve().parents[1] / "components"
    for entry in registry:
        model_id = entry.get("id")
        if not model_id or model_id in rsps:
            continue
        target = components_root / "resamplers" / model_id / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.resamplers.{model_id}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=model_id, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom resampler {mid} missing build_model/get_model")

        rsps[model_id] = factory


def reload_custom_components():
    """Reload custom resamplers, clearing previous custom entries first."""
    for key in [k for k in list(rsps.keys()) if k not in _BUILTIN_RSP]:
        rsps.pop(key, None)
    load_custom_components()


load_custom_components()


def get_resampler_provider(method: str) -> Optional[DockerImageProvider]:
    if DockerImageProvider is None:
        return None
    if method in {"rus", "ros", "smote"}:
        return RunImblearnSampler
    if method == "mwmote":
        return RunSmoteSampler
    return None


def value_counter(Y: np.ndarray):
    """Count and log class distribution"""
    values, counts = np.unique(Y, return_counts=True)
    for value, count in zip(values, counts):
        dist = count / Y.shape[0] * 100
        logging.info("\t\t Class={}, n={},\t ({:.2f}%)".format(value, count, dist))


class CustomResamplar(BaseEstimator):
    """Unified resampler wrapper built on registry `rsps`.

    method:            key in `registry` (e.g., 'rus', 'smote', ...).
    registry:          mapping from method name -> factory that returns a resampler.
    host_data_root:       base folder where data is stored.
    dataset_name:      dataset identifier for metadata/caching.
    sampling_strategy: ratio for resampling (None uses resampler defaults).
    **resampler_kwargs: forwarded to the underlying resampler factory.
    """

    def __init__(self,
                 method: str = "smote",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 dataset_name: Optional[str] = None,
                 sampling_strategy: Optional[float] = None,
                 result_file_path: Optional[str] = None,
                 **resampler_kwargs: Any):

        self.method = method
        self.registry = rsps if registry is None else registry
        self.host_data_root = host_data_root
        self.dataset_name = dataset_name
        self.result_file_path = result_file_path
        self.sampling_strategy = sampling_strategy
        self.resampler_kwargs = dict(resampler_kwargs)

        self.resampler = self._build_rsp()

    def fit_resample(self, args, X: np.ndarray, y: np.ndarray):
        """
        Fit and resample the data to address class imbalance.

        Args:
            args: Arguments object with .path for host_data_root
            X: Feature matrix
            y: Labels

        Returns:
            Tuple of (X_resampled, y_resampled)
        """
        logging.info("\t Before Re-Sampling")
        value_counter(y)

        # Update sampling strategy if set
        if self.sampling_strategy is not None and hasattr(self.resampler, 'set_params'):
            self.resampler.set_params(sampling_strategy=self.sampling_strategy)

        # Perform resampling
        if isinstance(self.resampler, BaseTransformer):
            X_res, y_res = self.resampler.fit_resample(args, X, y)
        else:
            # For non-Docker resamplers (if any exist in the future)
            X_res, y_res = self.resampler.fit_resample(X, y)

        logging.info("\t After Re-Sampling")
        value_counter(y_res)

        return X_res, y_res

    def cleanup(self):
        """Release Docker resources held by the resampler implementation."""
        resampler = getattr(self, "resampler", None)
        if resampler and hasattr(resampler, "cleanup"):
            resampler.cleanup()

    def need_resample(self, Y: np.ndarray, samratio: Optional[float] = None):
        """
        Test if resampling is needed based on class imbalance.

        Args:
            Y: Labels array
            samratio: Threshold ratio for resampling decision

        Returns:
            bool: True if resampling is needed
        """
        # If nothing is given, use default settings
        if samratio is None:
            return True

        _, counts = np.unique(Y, return_counts=True)
        if len(counts) < 2:
            return False

        ratio = counts[1] / counts[0]
        return ratio < samratio

    def get_params(self, deep: bool = True):
        """Get parameters for this estimator."""
        params = {
            "method": self.method,
            "registry": self.registry,
            "host_data_root": self.host_data_root,
            "dataset_name": self.dataset_name,
            "sampling_strategy": self.sampling_strategy,
            **{f"impl__{k}": v for k, v in self.resampler_kwargs.items()},
        }
        if deep and hasattr(self.resampler, "get_params"):
            for k, v in self.resampler.get_params(deep=True).items():
                params.setdefault(f"impl__{k}", v)
        return params

    def set_params(self, **params):
        """Set parameters for this estimator."""
        if "method" in params:
            self.method = params.pop("method")
        if "registry" in params:
            self.registry = params.pop("registry")
        if "host_data_root" in params:
            self.host_data_root = params.pop("host_data_root")
        if "dataset_name" in params:
            self.dataset_name = params.pop("dataset_name")
        if "sampling_strategy" in params:
            self.sampling_strategy = params.pop("sampling_strategy")

        self.resampler_kwargs.update(params)
        self.resampler = self._build_rsp()

        return self

    def _build_rsp(self):
        """
        Instantiate the underlying resampler from the registry.

        Looks up `self.method` in the registry and instantiates the factory.
        """
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown resampling method '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        # registry values are factories (lambda **kw)
        self.resampler_kwargs["host_data_root"] = self.host_data_root
        self.resampler_kwargs["result_file_path"] = self.result_file_path
        factory = self.registry[self.method]
        rsp = factory(**self.resampler_kwargs)

        # Set sampling_strategy if provided and supported
        if self.sampling_strategy is not None:
            if hasattr(rsp, "set_params"):
                rsp.set_params(sampling_strategy=self.sampling_strategy)

        return rsp
