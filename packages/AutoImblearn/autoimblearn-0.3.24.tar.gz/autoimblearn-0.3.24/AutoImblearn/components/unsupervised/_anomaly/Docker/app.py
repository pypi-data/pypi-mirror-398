"""
Anomaly Detection API using BaseUnsupervisedEstimatorAPI.

Supports:
- isoforest: Isolation Forest
- ocsvm: One-Class SVM
- lof: Local Outlier Factor
- elliptic: Elliptic Envelope (Robust Covariance)
"""

import logging
import numpy as np
from AutoImblearn.components.api import BaseUnsupervisedEstimatorAPI
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score


# Hyperparameter search spaces
hyperparameter_search_space = {
    'isoforest': {
        'contamination': {
            'type': 'float',
            'low': 0.01,
            'high': 0.5,
            'default': 0.1
        },
        'n_estimators': {
            'type': 'int',
            'low': 50,
            'high': 300,
            'default': 100
        },
        'max_samples': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 1.0
        }
    },
    'ocsvm': {
        'nu': {
            'type': 'float',
            'low': 0.01,
            'high': 0.5,
            'default': 0.1
        },
        'kernel': {
            'type': 'categorical',
            'choices': ['linear', 'poly', 'rbf', 'sigmoid'],
            'default': 'rbf'
        },
        'gamma': {
            'type': 'categorical',
            'choices': ['scale', 'auto'],
            'default': 'scale'
        }
    },
    'lof': {
        'contamination': {
            'type': 'float',
            'low': 0.01,
            'high': 0.5,
            'default': 0.1
        },
        'n_neighbors': {
            'type': 'int',
            'low': 5,
            'high': 50,
            'default': 20
        }
    },
    'elliptic': {
        'contamination': {
            'type': 'float',
            'low': 0.01,
            'high': 0.5,
            'default': 0.1
        },
        'support_fraction': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': None
        }
    }
}


class RunAnomalyDetectionAPI(BaseUnsupervisedEstimatorAPI):
    """Anomaly detection API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.unsupervised_type = 'anomaly'
        self.param_space = hyperparameter_search_space

    def get_hyperparameter_search_space(self) -> dict:
        """Return hyperparameter search space for HPO integration."""
        model_name = self.params.get('model', 'isoforest')
        return self.param_space.get(model_name, {})

    def _get_default_params(self, model_name: str) -> dict:
        """Get default hyperparameters."""
        if model_name not in self.param_space:
            return {}
        defaults = {}
        for param_name, param_config in self.param_space[model_name].items():
            if 'default' in param_config and param_config['default'] is not None:
                defaults[param_name] = param_config['default']
        return defaults

    def _validate_kwargs(self, model_name: str, kwargs: dict):
        """Validate hyperparameters."""
        if model_name not in self.param_space:
            return
        allowed = set(self.param_space[model_name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{model_name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )

    def _calculate_metrics(self, predictions, y_test=None):
        """Calculate anomaly detection metrics."""
        metrics = {}

        # Count anomalies
        n_anomalies = int(np.sum(predictions == -1))
        n_normal = int(np.sum(predictions == 1))

        metrics['n_anomalies'] = n_anomalies
        metrics['n_normal'] = n_normal
        metrics['anomaly_ratio'] = float(n_anomalies / len(predictions))

        # Calculate evaluation metrics if ground truth is provided
        if y_test is not None:
            try:
                # Convert predictions to binary (1 for anomaly, 0 for normal)
                y_pred_binary = (predictions == -1).astype(int)
                y_true_binary = y_test.astype(int)

                metrics['accuracy'] = float(accuracy_score(y_true_binary, y_pred_binary))
                metrics['precision'] = float(precision_score(y_true_binary, y_pred_binary, zero_division=0))
                metrics['recall'] = float(recall_score(y_true_binary, y_pred_binary, zero_division=0))
                metrics['f1'] = float(f1_score(y_true_binary, y_pred_binary, zero_division=0))
            except Exception as e:
                metrics['evaluation_error'] = str(e)

        return metrics

    def fit(self, args, X_train):
        """Fit anomaly detection model."""
        model_name = args.model
        self.model_name = model_name

        # Get hyperparameters
        try:
            model_kwargs = args.params if hasattr(args, 'params') and args.params else {}
        except AttributeError:
            model_kwargs = {}

        # Validate and merge with defaults
        self._validate_kwargs(model_name, model_kwargs)
        final_params = {**self._get_default_params(model_name), **model_kwargs}

        logging.info(f"Fitting {model_name} with params: {final_params}")

        # Create model
        if model_name == 'isoforest':
            from sklearn.ensemble import IsolationForest
            model = IsolationForest(random_state=42, **final_params)
        elif model_name == 'ocsvm':
            from sklearn.svm import OneClassSVM
            model = OneClassSVM(**final_params)
        elif model_name == 'lof':
            from sklearn.neighbors import LocalOutlierFactor
            model = LocalOutlierFactor(novelty=True, **final_params)
        elif model_name == 'elliptic':
            from sklearn.covariance import EllipticEnvelope
            model = EllipticEnvelope(random_state=42, **final_params)
        else:
            raise ValueError(f"Unknown anomaly detection model: {model_name}")

        # Fit model
        model.fit(X_train)
        logging.info("✓ Finished fitting")

        return model

    def predict(self, X):
        """Predict anomalies."""
        # Predict
        predictions = self.fitted_model.predict(X)

        # Get anomaly scores
        anomaly_scores = None
        if hasattr(self.fitted_model, 'score_samples'):
            anomaly_scores = self.fitted_model.score_samples(X)
        elif hasattr(self.fitted_model, 'decision_function'):
            anomaly_scores = self.fitted_model.decision_function(X)

        # Calculate metrics (no y_test in unsupervised mode)
        metrics = self._calculate_metrics(predictions)

        logging.info(
            f"✓ Anomaly detection: {metrics['n_anomalies']} anomalies "
            f"({metrics['anomaly_ratio']:.2%})"
        )

        result = {
            'predictions': predictions.tolist(),
            'metrics': metrics
        }

        if anomaly_scores is not None:
            result['anomaly_scores'] = anomaly_scores.tolist()

        return result


if __name__ == '__main__':
    RunAnomalyDetectionAPI().run()
