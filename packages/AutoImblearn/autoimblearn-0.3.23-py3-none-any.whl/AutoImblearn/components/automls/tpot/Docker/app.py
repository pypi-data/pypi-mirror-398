import logging
import numpy as np
from tpot import TPOTClassifier
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, accuracy_score

from AutoImblearn.components.api import BaseEstimatorAPI


class RunTPOTAPI(BaseEstimatorAPI):
    """TPOT AutoML API following the standardized BaseEstimatorAPI pattern."""

    def __init__(self, import_name):
        super().__init__(import_name)
        self.tpot_model = None
        self.result_metric = None

    def fit(self, args, X_train, y_train, X_test, y_test):
        """
        Train TPOT AutoML model.

        Args:
            args: Parameters including metric, model settings
            X_train: Training features
            y_train: Training labels
            X_test: Test features (for evaluation)
            y_test: Test labels (for evaluation)

        Returns:
            Fitted TPOT model
        """
        # Set up TPOT based on metric
        if self.params.metric == "auroc":
            scoring = 'roc_auc'
        elif self.params.metric == "macro_f1":
            scoring = 'f1_macro'
        else:
            raise ValueError(f"Metric {self.params.metric} not supported for TPOT")

        # Create TPOT classifier
        model = TPOTClassifier(
            generations=5,
            population_size=50,
            verbosity=2,
            random_state=42,
            scoring=scoring,
            max_time_mins=5,  # 5 minutes max
            n_jobs=1
        )

        # Train the model
        logging.info(f"Starting TPOT AutoML training with metric={scoring}...")
        model.fit(X_train, y_train)
        logging.info("✓ TPOT AutoML training complete")

        self.tpot_model = model

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

        y_pred = self.fitted_model.predict(X_test)
        metrics["accuracy"] = accuracy_score(y_test, y_pred)
        metrics["precision_macro"] = precision_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["recall_macro"] = recall_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["f1_macro"] = f1_score(y_test, y_pred, average='macro', zero_division=0)
        metrics["macro_f1"] = metrics["f1_macro"]

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
            raise NotImplementedError("TPOT model does not support predict_proba().")
        return self.fitted_model.predict_proba(X_test)


if __name__ == '__main__':
    RunTPOTAPI(__name__).run()
