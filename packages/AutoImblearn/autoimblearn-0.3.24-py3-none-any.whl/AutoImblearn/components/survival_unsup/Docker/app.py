"""
Survival unsupervised API using BaseSurvivalEstimatorAPI.

Supports:
- survival_tree: Survival Tree (for subgroup discovery)
- survival_kmeans: KMeans adapted for survival data (clustering on survival times)
"""

import logging
import numpy as np
from AutoImblearn.components.api import BaseSurvivalEstimatorAPI
from sksurv.tree import SurvivalTree
from sklearn.cluster import KMeans
from sksurv.compare import compare_survival
from sklearn.metrics import silhouette_score


# Hyperparameter search spaces
hyperparameter_search_space = {
    'survival_tree': {
        'max_depth': {
            'type': 'int',
            'low': 2,
            'high': 10,
            'default': 3
        },
        'min_samples_split': {
            'type': 'int',
            'low': 10,
            'high': 50,
            'default': 20
        },
        'min_samples_leaf': {
            'type': 'int',
            'low': 5,
            'high': 30,
            'default': 10
        }
    },
    'survival_kmeans': {
        'n_clusters': {
            'type': 'int',
            'low': 2,
            'high': 10,
            'default': 3
        },
        'n_init': {
            'type': 'int',
            'low': 5,
            'high': 20,
            'default': 10
        }
    }
}


class RunSurvivalUnsupervisedAPI(BaseSurvivalEstimatorAPI):
    """Survival unsupervised API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.model_type = 'unsupervised'
        self.param_space = hyperparameter_search_space

    def get_hyperparameter_search_space(self) -> dict:
        """Return hyperparameter search space for HPO integration."""
        model_name = self.params.get('model', 'survival_tree')
        return self.param_space.get(model_name, {})

    def _get_default_params(self, model_name: str) -> dict:
        """Get default hyperparameters."""
        if model_name not in self.param_space:
            return {}
        defaults = {}
        for param_name, param_config in self.param_space[model_name].items():
            if 'default' in param_config:
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

    def fit(self, args, X_train, y_train, X_test=None, y_test=None):
        """Fit survival unsupervised model."""
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

        # Create and fit model
        if model_name == 'survival_tree':
            # Survival tree can directly use structured array
            model = SurvivalTree(**final_params)
            model.fit(X_train, y_train)

        elif model_name == 'survival_kmeans':
            # KMeans on survival times (for uncensored data or treating time as feature)
            # This is a simple approach - cluster based on survival times
            model = KMeans(random_state=42, **final_params)
            survival_times = y_train['Survival_in_days'].reshape(-1, 1)
            model.fit(survival_times)

        else:
            raise ValueError(f"Unknown model: {model_name}")

        logging.info("✓ Finished fitting")
        return model

    def predict(self, X_test, y_test):
        """Predict cluster assignments or risk scores."""
        if self.model_name == 'survival_tree':
            # Predict risk scores (leaf node IDs)
            predictions = self.fitted_model.apply(X_test)

        elif self.model_name == 'survival_kmeans':
            # Predict cluster assignments based on survival times
            survival_times = y_test['Survival_in_days'].reshape(-1, 1)
            predictions = self.fitted_model.predict(survival_times)

        else:
            raise ValueError(f"Unknown model: {self.model_name}")

        # Calculate metrics
        metrics = {}
        unique_clusters = np.unique(predictions)

        if len(unique_clusters) > 1:
            # Calculate log-rank statistic for cluster separation
            try:
                cluster_groups = [y_test[predictions == c] for c in unique_clusters]
                chisq, pvalue = compare_survival(cluster_groups)
                metrics['log_rank_chi2'] = float(chisq)
                metrics['log_rank_pvalue'] = float(pvalue)
            except Exception as e:
                logging.warning(f"Failed to calculate log-rank: {e}")

            # Calculate silhouette score for KMeans
            if self.model_name == 'survival_kmeans':
                try:
                    survival_times = y_test['Survival_in_days'].reshape(-1, 1)
                    silhouette = silhouette_score(survival_times, predictions)
                    metrics['silhouette'] = float(silhouette)
                except Exception as e:
                    logging.warning(f"Failed to calculate silhouette: {e}")

        metrics['n_clusters'] = int(len(unique_clusters))

        result = {
            'predictions': predictions.tolist(),
            'metrics': metrics
        }

        logging.info(f"✓ Clustering complete: {metrics['n_clusters']} clusters")
        return result


if __name__ == '__main__':
    RunSurvivalUnsupervisedAPI().run()
