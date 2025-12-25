# AutoImblearn/pipelines/customreduction.py
import json
from pathlib import Path
from typing import Dict, Callable, Any, Optional
import importlib.util

import numpy as np
from sklearn.base import BaseEstimator
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    is_metric_supported,
)

from AutoImblearn.components.unsupervised import RunDimensionalityReduction

try:
    from AutoImblearn.components.model_client.base_model_client import BaseDockerModelClient
except Exception:
    BaseDockerModelClient = None

# Dimensionality reduction models - factory functions
reduction_models: Dict[str, Callable[..., Any]] = {
    'pca': lambda **kw: RunDimensionalityReduction(model='pca', **kw),
    'tsne': lambda **kw: RunDimensionalityReduction(model='tsne', **kw),
    'umap': lambda **kw: RunDimensionalityReduction(model='umap', **kw),
    'svd': lambda **kw: RunDimensionalityReduction(model='svd', **kw),
    'ica': lambda **kw: RunDimensionalityReduction(model='ica', **kw),
    'nmf': lambda **kw: RunDimensionalityReduction(model='nmf', **kw),
}
_BUILTIN_REDUCTION = set(reduction_models.keys())


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

    for entry in load_registry("reduction_models.json"):
        mid = entry.get("id")
        if not mid or mid in reduction_models:
            continue
        target = components_root / "reduction_models" / mid / "run.py"
        if not target.exists():
            target = target.parent / "__init__.py"
        if not target.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.reduction_models.{mid}", target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=mid, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom reduction model {mid} missing build_model/get_model")

        reduction_models[mid] = factory


def reload_custom_components():
    """Reload custom reduction models, clearing previous custom entries first."""
    for key in [k for k in list(reduction_models.keys()) if k not in _BUILTIN_REDUCTION]:
        reduction_models.pop(key, None)
    load_custom_components()


load_custom_components()


class CustomReductionModel(BaseEstimator):
    """Unified dimensionality reduction model wrapper built on registry `reduction_models`."""

    def __init__(self,
                 method: str = "pca",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 metric: str = "silhouette",
                 **model_kwargs: Any):

        self.method = method
        self.registry = reduction_models if registry is None else registry
        self.host_data_root = host_data_root
        self.metric = metric
        self.model_kwargs = dict(model_kwargs)
        self.model_type = "reduction"

        self.reduction_model = self._build_reduction_model()
        self.result = None
        self.pipeline_type = "reduction"

    def fit(self, args, X_train: np.ndarray, y_train: Optional[np.ndarray] = None):
        """Train dimensionality reduction model."""
        self.pipeline_type = getattr(args, "pipeline_type", "reduction")
        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        if isinstance(self.reduction_model, BaseDockerModelClient):
            self.reduction_model.fit(args, X_train, y_train)
        else:
            self.reduction_model.fit(X_train, y_train)

        return self

    def cleanup(self):
        """Release Docker resources held by the model implementation."""
        model = getattr(self, "reduction_model", None)
        if model and hasattr(model, "cleanup"):
            model.cleanup()

    def predict(self, X_test: np.ndarray):
        """Transform features."""
        return self.reduction_model.transform(X_test) if hasattr(self.reduction_model, "transform") else self.reduction_model.predict(X_test)

    def score(self, X_test: np.ndarray, y_test: Optional[np.ndarray] = None):
        """Evaluate the model using the specified metric, if supported."""
        if hasattr(self.reduction_model, "score"):
            return self.reduction_model.score(X_test, y_test)
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
        if deep and hasattr(self.reduction_model, "get_params"):
            for k, v in self.reduction_model.get_params(deep=True).items():
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
        self.reduction_model = self._build_reduction_model()

        return self

    def _build_reduction_model(self):
        """Instantiate the underlying reduction model from the registry."""
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown reduction model '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        self.model_kwargs["host_data_root"] = self.host_data_root
        factory = self.registry[self.method]
        reduction_model = factory(**self.model_kwargs)

        return reduction_model
