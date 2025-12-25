import os
import json
from types import SimpleNamespace
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import importlib.util

import numpy as np
from sklearn.base import BaseEstimator
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    get_default_metric,
    is_metric_supported,
)

from ..components.hybrids import RunAutoSmote, RunAutoRSP
from AutoImblearn.components.model_client.image_spec import DockerImageProvider


hybrid_factories: Dict[str, Callable[..., Any]] = {
    "autosmote": lambda **kwargs: RunAutoSmote(**kwargs),
    "autorsp": lambda **kwargs: RunAutoRSP(**kwargs),
}
_BUILTIN_HYBRIDS = set(hybrid_factories.keys())


def load_custom_components():
    registry_path = Path(__file__).resolve().parents[4] / "data" / "models" / "registry" / "hybrids.json"
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
        if not model_id or model_id in hybrid_factories:
            continue
        target = components_root / "hybrids" / model_id / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.hybrids.{model_id}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=model_id, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom hybrid {mid} missing build_model/get_model")

        hybrid_factories[model_id] = factory


def reload_custom_components():
    """Reload custom hybrid factories, clearing previous custom entries first."""
    for key in [k for k in list(hybrid_factories.keys()) if k not in _BUILTIN_HYBRIDS]:
        hybrid_factories.pop(key, None)
    load_custom_components()


load_custom_components()


def get_hybrid_provider(method: str) -> Optional[DockerImageProvider]:
    if method == "autosmote":
        return RunAutoSmote
    if method == "autorsp":
        return RunAutoRSP
    return None


class CustomHybrid(BaseEstimator):
    """
    Unified wrapper for hybrid resampler/classifier pipelines.

    The implementation mirrors the style of CustomResamplar and CustomClassifier,
    providing sklearn-like APIs (`fit`, `predict`, `get_params`, `set_params`) while
    managing Docker-backed components under the hood.
    """

    def __init__(
        self,
        method: str = "autosmote",
        registry: Optional[Dict[str, Callable[..., Any]]] = None,
        host_data_root: Optional[str] = None,
        dataset_name: Optional[str] = None,
        metric: str = "auroc",
        result_file_path: Optional[str] = None,
        imputer_method: Optional[str] = None,
        runtime_params: Optional[Dict[str, Any]] = None,
        **hybrid_kwargs: Any,
    ):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")
        if dataset_name is None:
            raise ValueError("dataset_name cannot be None")

        self.method = method
        self.registry = hybrid_factories if registry is None else registry
        self.host_data_root = host_data_root
        self.dataset_name = dataset_name
        self.metric = metric
        self.imputer_method = imputer_method
        self.hybrid_kwargs = dict(hybrid_kwargs)
        self.default_runtime_params = dict(runtime_params or {})

        self.result_file_path = result_file_path
        self.result_file_name = None
        self._ensure_result_path()

        self.hybrid_component = self._build_hybrid_component()
        self.result = None
        self.pipeline_type = "classification"

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: Optional[np.ndarray] = None,
        y_test: Optional[np.ndarray] = None,
        runtime_params: Optional[Dict[str, Any]] = None,
    ):
        """
        Train the hybrid component.

        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Optional validation/test features
            y_test: Optional validation/test labels
            runtime_params: Optional dict of runtime parameters to merge into the
                arguments passed to the underlying component (e.g., val_ratio, device).
        """
        self.pipeline_type = "classification"
        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        args = self._build_runtime_args(runtime_params)
        self.result = self.hybrid_component.fit(
            args,
            X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
        )
        return self

    def predict(self, X_test: np.ndarray, y_test: Optional[np.ndarray] = None):
        """
        Generate predictions or results from the trained hybrid component.
        """
        result = self.hybrid_component.predict(X_test)
        self.result = result
        return result

    def cleanup(self):
        """
        Release Docker resources held by the underlying implementation.
        """
        hybrid = getattr(self, "hybrid_component", None)
        if hybrid and hasattr(hybrid, "cleanup"):
            hybrid.cleanup()

    def get_params(self, deep: bool = True):
        """
        Return estimator parameters for compatibility with sklearn tooling.
        """
        params = {
            "method": self.method,
            "registry": self.registry,
            "host_data_root": self.host_data_root,
            "dataset_name": self.dataset_name,
            "metric": self.metric,
            "result_file_path": self.result_file_path,
            "imputer_method": self.imputer_method,
            "runtime_params": dict(self.default_runtime_params),
            **{f"impl__{k}": v for k, v in self.hybrid_kwargs.items()},
        }
        if deep and hasattr(self.hybrid_component, "get_params"):
            for k, v in self.hybrid_component.get_params(deep=True).items():
                params.setdefault(f"impl__{k}", v)
        return params

    def set_params(self, **params):
        """
        Set estimator parameters and rebuild the underlying implementation when needed.
        """
        if "method" in params:
            self.method = params.pop("method")
        if "registry" in params:
            self.registry = params.pop("registry")
        if "host_data_root" in params:
            self.host_data_root = params.pop("host_data_root")
        if "dataset_name" in params:
            self.dataset_name = params.pop("dataset_name")
        if "metric" in params:
            self.metric = params.pop("metric")
        if "result_file_path" in params:
            self.result_file_path = params.pop("result_file_path")
        if "imputer_method" in params:
            self.imputer_method = params.pop("imputer_method")
        if "runtime_params" in params:
            self.default_runtime_params = dict(params.pop("runtime_params") or {})

        self.hybrid_kwargs.update(params)
        self._ensure_result_path()
        self.hybrid_component = self._build_hybrid_component()

        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_result_path(self):
        """
        Ensure a result path exists and record the file name for downstream use.
        """
        if self.result_file_path is None and self.host_data_root and self.dataset_name:
            self.result_file_path = os.path.join(
                self.host_data_root,
                "interim",
                self.dataset_name,
                f"hybrid_{self.method}.p",
            )

        if self.result_file_path:
            os.makedirs(os.path.dirname(self.result_file_path), exist_ok=True)
            self.result_file_name = os.path.basename(self.result_file_path)

    def _build_hybrid_component(self):
        """
        Instantiate the underlying hybrid implementation from the registry.
        """
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown hybrid method '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        factory = self.registry[self.method]
        factory_kwargs = dict(self.hybrid_kwargs)
        factory_kwargs.setdefault("host_data_root", self.host_data_root)
        factory_kwargs.setdefault("result_file_path", self.result_file_path)
        factory_kwargs.setdefault("metric", self.metric)
        if self.imputer_method is not None:
            factory_kwargs.setdefault("imputer_method", self.imputer_method)

        hybrid_component = factory(**factory_kwargs)
        if hasattr(hybrid_component, "result_file_name") and self.result_file_name:
            hybrid_component.result_file_name = self.result_file_name
        return hybrid_component

    def _build_runtime_args(self, overrides: Optional[Dict[str, Any]] = None):
        """
        Construct a lightweight namespace with runtime arguments for the component.
        """
        args_dict = {
            "dataset": self.dataset_name,
            "path": self.host_data_root,
            "metric": self.metric,
        }
        args_dict.update(self.default_runtime_params)
        if overrides:
            args_dict.update(overrides)
        return SimpleNamespace(**args_dict)
