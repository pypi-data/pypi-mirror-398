import importlib.util
import logging
from pathlib import Path
from typing import Dict, Callable, Any, Optional

import numpy as np
from sklearn.base import BaseEstimator

from AutoImblearn.components.survival_unsup import RunSurvivalUnsupervised
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    is_metric_supported,
)

try:
    from AutoImblearn.components.model_client.base_model_client import BaseDockerModelClient
    from AutoImblearn.components.model_client.image_spec import DockerImageProvider
except Exception:
    BaseDockerModelClient = None
    DockerImageProvider = None

# Docker-based survival unsupervised models - factory functions
survival_unsupervised_models: Dict[str, Callable[..., Any]] = {
    'survival_tree': lambda **kw: RunSurvivalUnsupervised(model='survival_tree', **kw),
    'survival_kmeans': lambda **kw: RunSurvivalUnsupervised(model='survival_kmeans', **kw),
}
_BUILTIN_SURV_UNSUP = set(survival_unsupervised_models.keys())


def load_custom_unsup_models():
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

    for entry in load_registry("survival_unsupervised_models.json"):
        mid = entry.get("id")
        if not mid or mid in survival_unsupervised_models:
            continue
        target = components_root / "survival_unsupervised_models" / mid / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.survival_unsupervised_models.{mid}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=mid, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom survival unsupervised model {mid} missing build_model/get_model")

        survival_unsupervised_models[mid] = factory


def reload_custom_unsup_models():
    """Reload custom survival unsupervised models, clearing previous custom entries first."""
    for key in [k for k in list(survival_unsupervised_models.keys()) if k not in _BUILTIN_SURV_UNSUP]:
        survival_unsupervised_models.pop(key, None)
    load_custom_unsup_models()


load_custom_unsup_models()


def get_survival_unsupervised_provider(method: str) -> Optional[DockerImageProvider]:
    if DockerImageProvider is None:
        return None
    if method in survival_unsupervised_models:
        return RunSurvivalUnsupervised
    return None


class CustomSurvivalUnsupervisedModel(BaseEstimator):
    """Unified survival unsupervised model wrapper built on registry `survival_unsupervised_models`."""

    def __init__(self,
                 method: str = "survival_tree",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 metric: str = "log_rank",
                 **model_kwargs: Any):

        self.method = method
        self.registry = survival_unsupervised_models if registry is None else registry
        self.host_data_root = host_data_root
        self.metric = metric
        self.model_kwargs = dict(model_kwargs)

        self.survival_unsupervised_model = self._build_survival_unsupervised_model()
        self.result = None
        self.pipeline_type = "survival_clustering"

    def fit(self, args, X_train: np.ndarray, y_train: Optional[np.ndarray] = None):
        """Train survival unsupervised model."""
        self.pipeline_type = getattr(args, "pipeline_type", "survival_clustering")
        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        if isinstance(self.survival_unsupervised_model, BaseDockerModelClient):
            self.survival_unsupervised_model.fit(args, X_train, y_train)
        else:
            self.survival_unsupervised_model.fit(X_train, y_train)

        return self

    def cleanup(self):
        """Release Docker resources held by the model implementation."""
        model = getattr(self, "survival_unsupervised_model", None)
        if model and hasattr(model, "cleanup"):
            model.cleanup()

    def predict(self, X_test: np.ndarray):
        """Generate clustering/assignment predictions."""
        return self.survival_unsupervised_model.predict(X_test)

    def score(self, X_test: np.ndarray, y_test: Optional[np.ndarray] = None):
        """Evaluate the model using the specified metric, if supported."""
        if hasattr(self.survival_unsupervised_model, "score"):
            return self.survival_unsupervised_model.score(X_test, y_test)
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
        if deep and hasattr(self.survival_unsupervised_model, "get_params"):
            for k, v in self.survival_unsupervised_model.get_params(deep=True).items():
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
        self.survival_unsupervised_model = self._build_survival_unsupervised_model()

        return self

    def _build_survival_unsupervised_model(self):
        """Instantiate the underlying survival unsupervised model from the registry."""
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown survival unsupervised model '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        self.model_kwargs["host_data_root"] = self.host_data_root
        factory = self.registry[self.method]
        survival_unsupervised_model = factory(**self.model_kwargs)

        return survival_unsupervised_model
