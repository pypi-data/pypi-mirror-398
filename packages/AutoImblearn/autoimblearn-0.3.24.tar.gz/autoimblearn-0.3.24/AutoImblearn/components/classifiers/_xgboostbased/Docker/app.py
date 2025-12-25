import logging

import numpy as np
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, precision_score, recall_score, f1_score, accuracy_score

from xgboost import XGBClassifier

from AutoImblearn.components.api import BaseEstimatorAPI

clfs = {
    "ensemble": XGBClassifier(learning_rate=1.0, max_depth=10, min_child_weight=15, n_estimators=100, n_jobs=1, subsample=0.8, verbosity=0),
}

hyperparameter_search_space = {
    "ensemble": {
        "learning_rate": {
            "type": "float",
            "min": 0.01,
            "max": 1.0,
            "default": 1.0,
            "log_scale": True
        },
        "max_depth": {
            "type": "int",
            "min": 1,
            "max": 20,
            "default": 10
        },
        "min_child_weight": {
            "type": "int",
            "min": 1,
            "max": 30,
            "default": 15
        },
        "n_estimators": {
            "type": "int",
            "min": 10,
            "max": 1000,
            "default": 100
        },
        "subsample": {
            "type": "float",
            "min": 0.5,
            "max": 1.0,
            "default": 0.8
        },
        "colsample_bytree": {
            "type": "float",
            "min": 0.5,
            "max": 1.0,
            "default": 1.0
        },
        "gamma": {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "default": 0.0
        },
        "reg_alpha": {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "default": 0.0
        },
        "reg_lambda": {
            "type": "float",
            "min": 0.0,
            "max": 5.0,
            "default": 1.0
        },
        "n_jobs": {
            "type": "int",
            "min": 1,
            "max": 16,
            "default": 1
        },
        "verbosity": {
            "type": "categorical",
            "choices": [0, 1, 2, 3],
            "default": 0
        }
    }
}

class RunXGBoostClassifierAPI(BaseEstimatorAPI):

    def __init__(self, import_name):
        super().__init__(import_name)
        self.clf_name = None
        self.result_metric = None  # Store the computed metric result
        self.param_space = hyperparameter_search_space
        self.metric = None

    def get_hyperparameter_search_space(self):
        clf = self.params.get("model") if isinstance(self.params, dict) else getattr(self.params, "model", None)
        return self.param_space.get(clf, {})

    def _validate_kwargs(self, clf_name: str, kwargs: dict):
        """Validate that provided hyperparameters are allowed for this classifier."""
        if clf_name not in self.param_space:
            return
        allowed = set(self.param_space[clf_name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{clf_name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )

    def _get_default_params(self, clf_name: str) -> dict:
        """Get default hyperparameters for a classifier."""
        if clf_name not in self.param_space:
            return {}

        defaults = {}
        for param_name, param_config in self.param_space[clf_name].items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        return defaults

    def fit(self, args, X_train, y_train, X_test, y_test):
        clf_name = getattr(args, "model", None)
        if clf_name is None:
            raise ValueError("Classifier model name was not provided in arguments.")
        self.clf_name = clf_name
        self.metric = getattr(args, "metric", None)

        # Get hyperparameters from params (if provided)
        try:
            clf_kwargs = getattr(args, "params", None)
            if not clf_kwargs:
                clf_kwargs = self.params.get("params") if isinstance(self.params, dict) else None
            if clf_kwargs is None:
                clf_kwargs = {}
        except AttributeError:
            clf_kwargs = {}

        # Validate hyperparameters
        self._validate_kwargs(clf_name, clf_kwargs)

        # Merge with defaults
        final_params = {**self._get_default_params(clf_name), **clf_kwargs}

        # Instantiate classifier with hyperparameters
        if clf_name == "ensemble":
            classifier = XGBClassifier(random_state=42, **final_params)
        else:
            # Fallback to old hardcoded dict
            if clf_name in clfs.keys():
                classifier = clfs[clf_name]
            else:
                raise Exception(f"Classifier '{clf_name}' not defined")

        logging.info(f"Training {clf_name} with params: {final_params}")
        classifier.fit(X_train, y_train)
        logging.info("finished classifier training")

        # Compute the metric and store it as result
        # Use classifier directly (not yet in self.fitted_model)
        self.fitted_model = classifier  # Temporarily set for predict() to work
        self.result_metric = self.predict(X_test, y_test)
        self.result = self.result_metric

        # RETURN the fitted model (sklearn pattern!)
        # Base class will assign it to self.fitted_model and save to disk
        return classifier

    def predict(self, X_test, y_test):
        """Evaluate fitted XGBoost classifier and return metrics."""
        if self.fitted_model is None:
            raise ValueError("Fitted model not available for evaluation.")

        metrics = {}

        y_pred = self.fitted_model.predict(X_test)
        metrics["accuracy"] = accuracy_score(y_test, y_pred)
        metrics["precision_macro"] = precision_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["recall_macro"] = recall_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["f1_macro"] = f1_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["macro_f1"] = metrics["f1_macro"]

        try:
            precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average=None, zero_division=0)
            metrics["class_precision"] = precision.tolist()
            metrics["class_recall"] = recall.tolist()
            metrics["class_f1"] = f1.tolist()
            metrics["class_support"] = support.tolist()
        except Exception as exc:
            logging.debug(f"Unable to compute per-class precision/recall: {exc}")

        if hasattr(self.fitted_model, "predict_proba"):
            try:
                y_proba = self.predict_proba(X_test)
                if y_proba.ndim > 1 and y_proba.shape[1] > 1:
                    positive_scores = y_proba[:, 1]
                else:
                    positive_scores = y_proba.ravel()
                metrics["auroc"] = roc_auc_score(y_test, positive_scores)
            except Exception as exc:
                logging.debug(f"Unable to compute AUROC: {exc}")

        selected_metric_name = self.metric or (self.params.get("metric") if isinstance(self.params, dict) else None)
        if selected_metric_name and selected_metric_name in metrics:
            metrics["selected_metric"] = metrics[selected_metric_name]
        elif "auroc" in metrics:
            metrics["selected_metric"] = metrics["auroc"]
        else:
            metrics["selected_metric"] = metrics.get("f1_macro")

        metrics = {
            key: (float(value) if isinstance(value, (np.floating, np.integer)) else value)
            for key, value in metrics.items()
        }

        self.result_metric = metrics.get("selected_metric")
        self.result = metrics
        return metrics

    def predict_proba(self, X_test):
        if self.fitted_model is None:
            raise ValueError("Fitted model not available for probability prediction.")
        if not hasattr(self.fitted_model, "predict_proba"):
            raise NotImplementedError(f"Model {self.clf_name} does not support predict_proba().")
        return self.fitted_model.predict_proba(X_test)


if __name__ == '__main__':
    RunXGBoostClassifierAPI(__name__).run()
