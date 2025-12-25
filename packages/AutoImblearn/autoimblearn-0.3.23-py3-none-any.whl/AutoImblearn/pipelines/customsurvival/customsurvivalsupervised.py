import importlib.util
import logging
from pathlib import Path
from typing import Dict, Callable, Any, Optional

import os
import pickle
import numpy as np
from sklearn.base import BaseEstimator

from AutoImblearn.components.survival_supv import RunSkSurvivalModel
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    get_default_metric,
    get_metric_family,
    is_metric_supported,
)

try:
    from AutoImblearn.components.model_client.base_model_client import BaseDockerModelClient
    from AutoImblearn.components.model_client.image_spec import DockerImageProvider
except Exception:
    BaseDockerModelClient = None
    DockerImageProvider = None

# Docker-based survival models - factory functions
survival_models: Dict[str, Callable[..., Any]] = {
    'CPH': lambda **kw: RunSkSurvivalModel(model='CPH', **kw),
    'RSF': lambda **kw: RunSkSurvivalModel(model='RSF', **kw),
    'SVM': lambda **kw: RunSkSurvivalModel(model='SVM', **kw),
    'KSVM': lambda **kw: RunSkSurvivalModel(model='KSVM', **kw),
    'LASSO': lambda **kw: RunSkSurvivalModel(model='LASSO', **kw),
    'L1': lambda **kw: RunSkSurvivalModel(model='L1', **kw),
    'L2': lambda **kw: RunSkSurvivalModel(model='L2', **kw),
    'CSA': lambda **kw: RunSkSurvivalModel(model='CSA', **kw),
    'LRSF': lambda **kw: RunSkSurvivalModel(model='LRSF', **kw),
}
_BUILTIN_SURVIVAL_MODELS = set(survival_models.keys())


def load_custom_models():
    registry_root = Path(__file__).resolve().parents[4] / "data" / "models" / "registry"
    components_root = Path(__file__).resolve().parents[1] / "components"

    def load_registry(fname):
        path = registry_root / fname
        if not path.exists():
            return []
        try:
            return json.loads(path.read_text())
        except Exception:
            return []

    import json

    for entry in load_registry("survival_models.json"):
        mid = entry.get("id")
        if not mid or mid in survival_models:
            continue
        target = components_root / "survival_models" / mid / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.survival_models.{mid}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=mid, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom survival model {mid} missing build_model/get_model")

        survival_models[mid] = factory


def reload_custom_models():
    """Reload custom survival models, clearing previous custom entries first."""
    for key in [k for k in list(survival_models.keys()) if k not in _BUILTIN_SURVIVAL_MODELS]:
        survival_models.pop(key, None)
    load_custom_models()


load_custom_models()


def get_survival_model_provider(method: str) -> Optional[DockerImageProvider]:
    if DockerImageProvider is None:
        return None
    if method in survival_models:
        return RunSkSurvivalModel
    return None


class CustomSurvivalModel(BaseEstimator):
    """Unified survival model wrapper built on registry `survival_models`."""

    def __init__(self,
                 method: str = "CPH",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 metric: str = "c_index",
                 **model_kwargs: Any):

        self.method = method
        self.registry = survival_models if registry is None else registry
        self.host_data_root = host_data_root
        self.dataset_name = model_kwargs.pop("dataset_name", None)
        self.metric = metric
        self.model_kwargs = dict(model_kwargs)
        self.container_data_root = model_kwargs.pop("container_data_root", None)

        self._survival_clf = self._build_survival_clf()
        self.result = None
        self.pipeline_type = "survival_classification"
        self._last_args = None

    def fit(self,
            args,
            X_train: np.ndarray,
            y_train: np.ndarray,
            X_test: Optional[np.ndarray] = None,
            y_test: Optional[np.ndarray] = None,
            ):
        """
        Train survival model.

        Args:
            args: Arguments object with .path for host_data_root
            X_train: Training features
            y_train: Training labels
            X_test: Test features
            y_test: Test labels

        Returns:
            self
        """

        self.pipeline_type = getattr(args, "pipeline_type", "survival_classification")
        self.dataset_name = getattr(args, "dataset", self.dataset_name)
        self.container_data_root = getattr(args, "container_data_root", self.container_data_root)
        self._last_args = args

        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        self._survival_clf.fit(args, X_train, y_train, X_test, y_test)
        # if isinstance(self._survival_clf, BaseDockerModelClient):
        #     self._survival_clf.fit(args, X_train, y_train)
        # else:
        #     self._survival_clf.fit(X_train, y_train)

        return self

    def cleanup(self):
        """Release Docker resources held by the survival model implementation."""
        impl = getattr(self, "_survival_clf", None)
        if impl and hasattr(impl, "cleanup"):
            impl.cleanup()

    def predict(self, X_test: np.ndarray):
        """Make risk predictions."""
        return self._survival_clf.predict(X_test)

    def score(self, X_test: np.ndarray, y_test: np.ndarray, y_train: Optional[np.ndarray] = None):
        """Evaluate the survival model using the specified metric."""
        metric = self.metric or get_default_metric(self.pipeline_type)
        # Prefer any result produced by the Docker app during training
        if hasattr(self._survival_clf, "result") and getattr(self._survival_clf, "result") is not None:
            self.result = self._survival_clf.result
            return self._extract_metric_score(metric, self.result)

        # Attempt to load saved result from interim folder
        result = self._load_saved_result()
        if result is not None:
            self.result = result
            return self._extract_metric_score(metric, result)

        # raise ValueError(f"Metric '{metric}' could not be evaluated for survival analysis")

    def get_params(self, deep: bool = True):
        """Get parameters for this estimator."""
        params = {
            "method": self.method,
            "registry": self.registry,
            "host_data_root": self.host_data_root,
            "metric": self.metric,
            **{f"impl__{k}": v for k, v in self.model_kwargs.items()},
        }
        if deep and hasattr(self._survival_clf, "get_params"):
            for k, v in self._survival_clf.get_params(deep=True).items():
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
        if "metric" in params:
            self.metric = params.pop("metric")

        self.model_kwargs.update(params)
        self._survival_clf = self._build_survival_clf()

        return self

    def _build_survival_clf(self):
        """Instantiate the underlying survival model from the registry."""
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown survival model '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        # registry values are factories (lambda **kw)
        self.model_kwargs["host_data_root"] = self.host_data_root
        factory = self.registry[self.method]
        impl = factory(**self.model_kwargs)

        return impl

    def _load_saved_result(self):
        """Load survival result persisted by the Docker app."""
        base_root = None
        if self._last_args:
            base_root = getattr(self._last_args, "container_data_root", None) or getattr(self._last_args, "host_data_root", None)
        if base_root is None:
            base_root = self.container_data_root or self.host_data_root
        if not base_root or not self.dataset_name:
            return None
        result_path = os.path.join(base_root, "interim", self.dataset_name, "survival_result.pkl")
        if not os.path.exists(result_path):
            return None
        try:
            with open(result_path, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None

    def _extract_metric_score(self, metric: str, result: dict):
        """Extract metric score from persisted result dict."""
        if not isinstance(result, dict):
            return result
        if metric in result:
            return result[metric]
        if "score" in result:
            return result["score"]
        return result
