import logging
import numpy as np
import h2o
from h2o.sklearn import H2OAutoMLClassifier
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, accuracy_score

from AutoImblearn.components.api import BaseEstimatorAPI


class RunH2OAPI(BaseEstimatorAPI):
    """H2O AutoML API following the standardized BaseEstimatorAPI pattern."""

    def __init__(self, import_name):
        super().__init__(import_name)
        self.automl_model = None
        self.result_metric = None

    def fit(self, args, X_train, y_train, X_test, y_test):
        """
        Train H2O AutoML model.

        Args:
            args: Parameters including metric, model settings
            X_train: Training features
            y_train: Training labels
            X_test: Test features (for evaluation)
            y_test: Test labels (for evaluation)

        Returns:
            Fitted H2O model
        """
        # Initialize H2O
        try:
            h2o.init(ip="localhost", port=54323)
            logging.info("✓ H2O initialized")
        except Exception as e:
            logging.warning(f"H2O already initialized or init failed: {e}")

        # Set up AutoML based on metric
        if self.params.metric == "auroc":
            model = H2OAutoMLClassifier(
                max_models=10,
                seed=42,
                sort_metric='auc',
                max_runtime_secs=300  # 5 minutes max
            )
        elif self.params.metric == "macro_f1":
            model = H2OAutoMLClassifier(
                max_models=10,
                seed=42,
                sort_metric='mean_per_class_error',
                max_runtime_secs=300
            )
        else:
            raise ValueError(f"Metric {self.params.metric} not supported for H2O AutoML")

        # Train the model
        logging.info("Starting H2O AutoML training...")
        model.fit(X_train, y_train)
        logging.info("✓ H2O AutoML training complete")

        self.automl_model = model

        # Compute metric on test data
        self.fitted_model = model  # Temporarily set for predict() to work
        self.result_metric = self.predict(X_test, y_test)
        self.result = self.result_metric

        # Return fitted model (BaseEstimatorAPI will save it)
        return model

    def predict(self, X_test, y_test):
        """
        Predict and compute metric on test data.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            Metric value (AUROC or F1)
        """
        metrics = {}

        h2o_predictions = self.fitted_model.predict(X_test)
        if hasattr(h2o_predictions, "as_data_frame"):
            predictions_df = h2o_predictions.as_data_frame()
            y_pred = predictions_df[0].to_numpy()
        else:
            y_pred = np.asarray(h2o_predictions)

        metrics["accuracy"] = accuracy_score(y_test, y_pred)
        metrics["precision_macro"] = precision_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["recall_macro"] = recall_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["f1_macro"] = f1_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["macro_f1"] = metrics["f1_macro"]

        try:
            y_proba = self.predict_proba(X_test)
            if isinstance(y_proba, tuple):
                y_proba = y_proba[0]
            if isinstance(y_proba, list):
                y_proba = np.asarray(y_proba)
            if hasattr(y_proba, 'ndim') and y_proba.ndim > 1:
                positive_scores = y_proba[:, 1]
            else:
                positive_scores = np.asarray(y_proba).ravel()
            metrics["auroc"] = roc_auc_score(y_test, positive_scores)
        except Exception as exc:
            logging.debug(f"Unable to compute AUROC: {exc}")

        selected_metric = self.params.metric if hasattr(self.params, 'metric') else None
        if selected_metric and selected_metric in metrics:
            metrics["selected_metric"] = metrics[selected_metric]
        elif "auroc" in metrics:
            metrics["selected_metric"] = metrics["auroc"]
        else:
            metrics["selected_metric"] = metrics.get("f1_macro")

        metrics = {
            key: (float(value) if isinstance(value, (np.floating, np.integer)) else value)
            for key, value in metrics.items()
        }

        self.result = metrics
        return metrics

    def predict_proba(self, X_test):
        if self.fitted_model is None:
            raise ValueError("Fitted model not available for probability prediction.")
        if not hasattr(self.fitted_model, "predict_proba"):
            raise NotImplementedError("H2O AutoML model does not support predict_proba().")
        y_proba = self.fitted_model.predict_proba(X_test)
        if hasattr(y_proba, 'values'):
            return y_proba.values
        return y_proba


if __name__ == '__main__':
    RunH2OAPI(__name__).run()
