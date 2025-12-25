# AutoImblearn/pipelines/customclf.py
import logging
import os
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import importlib.util
import json

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    get_default_metric,
    is_metric_supported,
)

from AutoImblearn.components.classifiers import RunSklearnClf, RunXGBoostClf
from AutoImblearn.components.model_client.image_spec import DockerImageProvider

try:
    from AutoImblearn.components.model_client.base_model_client import BaseDockerModelClient
except Exception:
    BaseDockerModelClient = None


# Docker-based classifiers - factory functions similar to imputers
clfs: Dict[str, Callable[..., Any]] = {
    "lr": lambda **kw: RunSklearnClf(model='lr', **kw),
    "mlp": lambda **kw: RunSklearnClf(model='mlp', **kw),
    "ada": lambda **kw: RunSklearnClf(model='ada', **kw),
    "svm": lambda **kw: RunSklearnClf(model='svm', **kw),
    # "ensemble": lambda **kw: RunXGBoostClf(model='ensemble', **kw),
}
_BUILTIN_CLFS = set(clfs.keys())


def load_custom_components():
    """Load custom classifiers registered via data/models/registry/classifiers.json."""
    registry_path = Path(__file__).resolve().parents[4] / "data" / "models" / "registry" / "classifiers.json"
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
        if not model_id:
            continue
        if model_id in clfs:
            continue
        install_path = components_root / "classifiers" / model_id / "run.py"
        target_file = install_path if install_path.exists() else install_path.parent / "__init__.py"
        if not target_file.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"AutoImblearn.components.classifiers.{model_id}", target_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore

        def factory(mod=module, mid=model_id, **kw):
            if hasattr(mod, "build_model"):
                return mod.build_model(**kw)
            if hasattr(mod, "get_model"):
                return mod.get_model(**kw)
            raise RuntimeError(f"Custom classifier {mid} missing build_model/get_model")

        clfs[model_id] = factory


def reload_custom_components():
    """Reload custom classifiers, clearing previous custom entries first."""
    for key in [k for k in list(clfs.keys()) if k not in _BUILTIN_CLFS]:
        clfs.pop(key, None)
    load_custom_components()


load_custom_components()


def get_classifier_provider(method: str) -> Optional[DockerImageProvider]:
    if method in {"lr", "mlp", "ada", "svm"}:
        return RunSklearnClf
    if method == "ensemble":
        return RunXGBoostClf
    return None


class CustomClassifier(BaseEstimator):
    """Unified classifier wrapper built on registry `clfs`.

    method:             key in `registry` (e.g., 'lr', 'mlp', ...).
    registry:           mapping from method name -> factory that returns a classifier.
    host_data_root:        base folder where data is stored.
    dataset_name:       dataset identifier for metadata/caching.
    metric:             evaluation metric ('auroc' or 'macro_f1').
    **classifier_kwargs: forwarded to the underlying classifier factory.
    """

    def __init__(self,
                 method: str = "lr",
                 registry: Optional[Dict[str, Callable[..., Any]]] = None,
                 host_data_root: Optional[str] = None,
                 dataset_name: Optional[str] = None,
                 metric: str = "auroc",
                 result_file_path: Optional[str] = None,
                 **classifier_kwargs: Any):

        self.method = method
        self.registry = clfs if registry is None else registry
        self.host_data_root = host_data_root
        self.dataset_name = dataset_name
        self.metric = metric
        self.classifier_kwargs = dict(classifier_kwargs)

        self.result_file_path = result_file_path
        self.result_file_name = None
        self._ensure_result_paths()

        self.classifier_model = self._build_classifier()
        self.result = None
        self.training_metrics = None
        self.pipeline_type = "classification"

    def fit(
        self,
        args,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_eval: Optional[np.ndarray] = None,
        y_eval: Optional[np.ndarray] = None,
    ):
        """
        Train the classifier.

        Args:
            args: Arguments object with .path for host_data_root
            X_train: Training features
            y_train: Training labels
            X_eval: Optional evaluation features (defaults to X_train if not provided)
            y_eval: Optional evaluation labels (defaults to y_train if not provided)

        Returns:
            self
        """
        # Update host_data_root if provided via args
        self.pipeline_type = getattr(args, "pipeline_type", "classification")
        if not is_metric_supported(self.pipeline_type, self.metric):
            allowed = [m["key"] for m in get_metrics_for_pipeline(self.pipeline_type)]
            raise ValueError(f"Unsupported metric '{self.metric}' for pipeline '{self.pipeline_type}'. Allowed: {allowed}")

        # Classifier containers expect evaluation data to compute metrics.
        if X_eval is None or y_eval is None:
            X_eval = X_train
            y_eval = y_train

        # Fit the classifier
        if isinstance(self.classifier_model, BaseDockerModelClient):
            metrics = self.classifier_model.fit(
                args,
                X_train,
                y_train,
                X_eval,
                y_eval,
                result_file_name=self.result_file_name,
                result_file_path=self.result_file_path,
            )
            self.training_metrics = metrics
        else:
            # For non-Docker classifiers (if any exist in the future)
            self.classifier_model.fit(X_train, y_train)

        return self

    def predict(self, X_test: np.ndarray):
        """
        Make predictions.

        Args:
            X_test: Test features

        Returns:
            Predictions
        """
        return self.classifier_model.predict(X_test)

    def predict_proba(self, X_test: np.ndarray):
        """
        Predict class probabilities.

        Args:
            X_test: Test features

        Returns:
            Class probabilities
        """
        if hasattr(self.classifier_model, 'predict_proba'):
            return self.classifier_model.predict_proba(X_test)
        else:
            raise AttributeError(f"Classifier '{self.method}' does not support predict_proba")

    def score(self, X_test: np.ndarray, y_test: np.ndarray):
        """
        Evaluate the classifier using the specified metric.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Evaluation score
        """
        metric = self.metric or get_default_metric(self.pipeline_type)
        if metric == "auroc":
            y_proba = self.predict_proba(X_test)[:, 1]
            score = roc_auc_score(y_test, y_proba)
            self.result = score
            logging.info(f"\t Classifier: {self.method}, AUROC: {score:.4f}")
            return score
        elif metric == "macro_f1":
            y_pred = self.predict(X_test)
            _, _, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
            self.result = f1
            logging.info(f"\t Classifier: {self.method}, Macro F1: {f1:.4f}")
            return f1
        else:
            raise ValueError(f"Metric '{metric}' is not supported for classifier '{self.method}'")

    def get_params(self, deep: bool = True):
        """Get parameters for this estimator."""
        params = {
            "method": self.method,
            "registry": self.registry,
            "host_data_root": self.host_data_root,
            "dataset_name": self.dataset_name,
            "metric": self.metric,
            "result_file_path": self.result_file_path,
            "result_file_name": self.result_file_name,
            **{f"impl__{k}": v for k, v in self.classifier_kwargs.items()},
        }
        if deep and hasattr(self.classifier_model, "get_params"):
            for k, v in self.classifier_model.get_params(deep=True).items():
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
        if "metric" in params:
            self.metric = params.pop("metric")
        if "result_file_path" in params:
            self.result_file_path = params.pop("result_file_path")
        if "result_file_name" in params:
            self.result_file_name = params.pop("result_file_name")

        self._ensure_result_paths()

        self.classifier_kwargs.update(params)
        self.classifier_model = self._build_classifier()

        return self

    def _build_classifier(self):
        """
        Instantiate the underlying classifier from the registry.

        Looks up `self.method` in the registry and instantiates the factory.
        """
        if self.method not in self.registry:
            raise KeyError(
                f"Unknown classifier method '{self.method}'. "
                f"Known methods: {sorted(self.registry.keys())}"
            )

        # registry values are factories (lambda **kw)
        clf_kwargs = {
            **self.classifier_kwargs,
            "host_data_root": self.host_data_root,
        }
        # Remove meta fields so they are not treated as hyperparameters
        clf_kwargs.pop("result_file_path", None)
        clf_kwargs.pop("result_file_name", None)

        factory = self.registry[self.method]
        clf = factory(**clf_kwargs)

        return clf

    def cleanup(self):
        """Release Docker resources held by the classifier implementation."""
        model = getattr(self, "classifier_model", None)
        if model and hasattr(model, "cleanup"):
            model.cleanup()

    def _ensure_result_paths(self):
        """Ensure result file path/name are set consistently."""
        if self.result_file_path is None and self.host_data_root and self.dataset_name:
            self.result_file_path = os.path.join(
                self.host_data_root,
                "interim",
                self.dataset_name,
                f"model_{self.method}.p"
            )

        if self.result_file_path:
            os.makedirs(os.path.dirname(self.result_file_path), exist_ok=True)
            self.result_file_name = os.path.basename(self.result_file_path)
        if self.result_file_name is None:
            self.result_file_name = f"model_{self.method}.p"
