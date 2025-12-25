# AutoImblearn/pipelines/customanomaly.py
import json
from pathlib import Path
from typing import Dict, Callable, Any, Optional
import importlib.util

import numpy as np
from sklearn.base import BaseEstimator

from AutoImblearn.components.unsupervised import RunAnomalyDetection
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    is_metric_supported,
)

try:
    from AutoImblearn.components.model_client.base_model_client import BaseDockerModelClient
except Exception:
    BaseDockerModelClient = None

# Anomaly detection models - factory functions
anomaly_models: Dict[str, Callable[..., Any]] = {
    'isoforest': lambda **kw: RunAnomalyDetection(model='isoforest', **kw),
    'ocsvm': lambda **kw: RunAnomalyDetection(model='ocsvm', **kw),
    'lof': lambda **kw: RunAnomalyDetection(model='lof', **kw),
    'elliptic': lambda **kw: RunAnomalyDetection(model='elliptic', **kw),
}
_BUILTIN_ANOMALY = set(anomaly_models.keys())


def load_custom_components():
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

    for entry in load_registry("anomaly_models.json"):
        mid = entry.get("id")
        if not mid or mid in anomaly_models:
            continue
        target = components_root / "anomaly_models" / mid / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.anomaly_models.{mid}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=mid, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom anomaly model {mid} missing build_model/get_model")

        anomaly_models[mid] = factory


def reload_custom_components():
    """Reload custom anomaly models, clearing previous custom entries first."""
    for key in [k for k in list(anomaly_models.keys()) if k not in _BUILTIN_ANOMALY]:
        anomaly_models.pop(key, None)
    load_custom_components()


load_custom_components()


class CustomAnomalyModel(BaseEstimator):
    """Unified anomaly model wrapper built on registry `anomaly_models`."""

    def __init__(self,
                 method: str = "isoforest",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 metric: str = "anomaly_score",
                 **model_kwargs: Any):

        self.method = method
        self.registry = anomaly_models if registry is None else registry
        self.host_data_root = host_data_root
        self.metric = metric
        self.model_kwargs = dict(model_kwargs)
        self.model_type = "anomaly"

        self.anomaly_model = self._build_anomaly_model()
        self.result = None
        self.pipeline_type = "anomaly"

    def fit(self, args, X_train: np.ndarray, y_train: Optional[np.ndarray] = None):
        """Train anomaly detection model."""
        self.pipeline_type = getattr(args, "pipeline_type", "anomaly")
        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        if isinstance(self.anomaly_model, BaseDockerModelClient):
            self.anomaly_model.fit(args, X_train, y_train)
        else:
            self.anomaly_model.fit(X_train, y_train)

        return self

    def cleanup(self):
        """Release Docker resources held by the model implementation."""
        model = getattr(self, "anomaly_model", None)
        if model and hasattr(model, "cleanup"):
            model.cleanup()

    def predict(self, X_test: np.ndarray):
        """Make predictions/labels."""
        return self.anomaly_model.predict(X_test)

    def score(self, X_test: np.ndarray, y_test: Optional[np.ndarray] = None):
        """Evaluate the model using the specified metric, if supported."""
        if hasattr(self.anomaly_model, "score"):
            return self.anomaly_model.score(X_test, y_test)
        return None

    def get_params(self, deep: bool = True):
        """Get parameters for this estimator."""
        params = {
            "method": self.method,
            "registry": self.registry,
            "host_data_root": self.host_data_root,
            "metric": self.metric,
            **{f"impl__{k}": v for k, v in self.model_kwargs.items()},
        }
        if deep and hasattr(self.anomaly_model, "get_params"):
            for k, v in self.anomaly_model.get_params(deep=True).items():
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
        self.anomaly_model = self._build_anomaly_model()

        return self

    def _build_anomaly_model(self):
        """Instantiate the underlying anomaly model from the registry."""
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown anomaly model '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        self.model_kwargs["host_data_root"] = self.host_data_root
        factory = self.registry[self.method]
        anomaly_model = factory(**self.model_kwargs)

        return anomaly_model
