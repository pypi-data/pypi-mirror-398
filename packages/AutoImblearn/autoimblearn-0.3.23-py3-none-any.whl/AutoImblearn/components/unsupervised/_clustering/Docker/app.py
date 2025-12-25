"""
Clustering API using BaseUnsupervisedEstimatorAPI.

Supports:
- kmeans: K-Means clustering
- dbscan: Density-Based Spatial Clustering
- hierarchical: Agglomerative Hierarchical Clustering
- gmm: Gaussian Mixture Model
- spectral: Spectral Clustering
- meanshift: Mean Shift Clustering
"""

import logging
import numpy as np
from AutoImblearn.components.api import BaseUnsupervisedEstimatorAPI
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score


# Hyperparameter search spaces
hyperparameter_search_space = {
    'kmeans': {
        'n_clusters': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 3
        },
        'n_init': {
            'type': 'int',
            'low': 5,
            'high': 20,
            'default': 10
        },
        'max_iter': {
            'type': 'int',
            'low': 100,
            'high': 1000,
            'default': 300
        }
    },
    'dbscan': {
        'eps': {
            'type': 'float',
            'low': 0.1,
            'high': 2.0,
            'default': 0.5
        },
        'min_samples': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 5
        }
    },
    'hierarchical': {
        'n_clusters': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 3
        },
        'linkage': {
            'type': 'categorical',
            'choices': ['ward', 'complete', 'average', 'single'],
            'default': 'ward'
        }
    },
    'gmm': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 3
        },
        'covariance_type': {
            'type': 'categorical',
            'choices': ['full', 'tied', 'diag', 'spherical'],
            'default': 'full'
        },
        'max_iter': {
            'type': 'int',
            'low': 50,
            'high': 500,
            'default': 100
        }
    },
    'spectral': {
        'n_clusters': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 3
        },
        'affinity': {
            'type': 'categorical',
            'choices': ['rbf', 'nearest_neighbors'],
            'default': 'rbf'
        }
    },
    'meanshift': {}
}


class RunClusteringAPI(BaseUnsupervisedEstimatorAPI):
    """Clustering API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.unsupervised_type = 'clustering'
        self.param_space = hyperparameter_search_space

    def get_hyperparameter_search_space(self) -> dict:
        """Return hyperparameter search space for HPO integration."""
        model_name = self.params.get('model', 'kmeans')
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

    def _calculate_metrics(self, X, labels):
        """Calculate clustering metrics."""
        metrics = {}
        unique_labels = np.unique(labels)
        n_clusters = len(unique_labels[unique_labels != -1])

        if n_clusters > 1:
            mask = labels != -1
            X_filtered = X[mask]
            labels_filtered = labels[mask]

            if len(np.unique(labels_filtered)) > 1:
                metrics['silhouette'] = float(silhouette_score(X_filtered, labels_filtered))
                metrics['calinski'] = float(calinski_harabasz_score(X_filtered, labels_filtered))
                metrics['davies_bouldin'] = float(davies_bouldin_score(X_filtered, labels_filtered))

            if self.model_name == 'kmeans' and hasattr(self.fitted_model, 'inertia_'):
                metrics['inertia'] = float(self.fitted_model.inertia_)

        metrics['n_clusters'] = int(n_clusters)
        metrics['n_noise'] = int(np.sum(labels == -1))

        return metrics

    def fit(self, args, X_train):
        """Fit clustering model."""
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
        if model_name == 'kmeans':
            from sklearn.cluster import KMeans
            model = KMeans(random_state=42, **final_params)
        elif model_name == 'dbscan':
            from sklearn.cluster import DBSCAN
            model = DBSCAN(**final_params)
        elif model_name == 'hierarchical':
            from sklearn.cluster import AgglomerativeClustering
            model = AgglomerativeClustering(**final_params)
        elif model_name == 'gmm':
            from sklearn.mixture import GaussianMixture
            model = GaussianMixture(random_state=42, **final_params)
        elif model_name == 'meanshift':
            from sklearn.cluster import MeanShift
            model = MeanShift(**final_params)
        elif model_name == 'spectral':
            from sklearn.cluster import SpectralClustering
            model = SpectralClustering(random_state=42, **final_params)
        else:
            raise ValueError(f"Unknown clustering model: {model_name}")

        # Fit model
        model.fit(X_train)
        logging.info("✓ Finished fitting")

        return model

    def predict(self, X):
        """Predict cluster assignments."""
        if self.model_name == 'gmm':
            predictions = self.fitted_model.predict(X)
        elif self.model_name in ['dbscan', 'meanshift']:
            predictions = self.fitted_model.fit_predict(X)
        else:
            predictions = self.fitted_model.predict(X)

        # Calculate metrics
        metrics = self._calculate_metrics(X, predictions)

        logging.info(f"✓ Clustering: {metrics['n_clusters']} clusters, silhouette={metrics.get('silhouette', 'N/A')}")

        return {
            'predictions': predictions.tolist(),
            'metrics': metrics
        }


if __name__ == '__main__':
    RunClusteringAPI().run()
