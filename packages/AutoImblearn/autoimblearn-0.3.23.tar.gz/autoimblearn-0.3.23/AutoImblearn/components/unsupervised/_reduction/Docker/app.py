"""
Dimensionality Reduction API using BaseUnsupervisedEstimatorAPI.

Supports:
- pca: Principal Component Analysis
- tsne: t-SNE
- umap: UMAP
- svd: Truncated SVD
- ica: Independent Component Analysis
- nmf: Non-negative Matrix Factorization
"""

import logging
import numpy as np
from AutoImblearn.components.api import BaseUnsupervisedEstimatorAPI


# Hyperparameter search spaces
hyperparameter_search_space = {
    'pca': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 50,
            'default': 2
        },
        'whiten': {
            'type': 'categorical',
            'choices': [True, False],
            'default': False
        }
    },
    'tsne': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 3,
            'default': 2
        },
        'perplexity': {
            'type': 'float',
            'low': 5.0,
            'high': 50.0,
            'default': 30.0
        },
        'learning_rate': {
            'type': 'float',
            'low': 10.0,
            'high': 1000.0,
            'default': 200.0
        },
        'n_iter': {
            'type': 'int',
            'low': 250,
            'high': 2000,
            'default': 1000
        }
    },
    'umap': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 50,
            'default': 2
        },
        'n_neighbors': {
            'type': 'int',
            'low': 5,
            'high': 50,
            'default': 15
        },
        'min_dist': {
            'type': 'float',
            'low': 0.0,
            'high': 0.99,
            'default': 0.1
        }
    },
    'svd': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 50,
            'default': 2
        }
    },
    'ica': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 50,
            'default': 2
        },
        'max_iter': {
            'type': 'int',
            'low': 100,
            'high': 500,
            'default': 200
        }
    },
    'nmf': {
        'n_components': {
            'type': 'int',
            'low': 2,
            'high': 50,
            'default': 2
        },
        'init': {
            'type': 'categorical',
            'choices': ['random', 'nndsvda', 'nndsvd'],
            'default': 'nndsvda'
        },
        'max_iter': {
            'type': 'int',
            'low': 100,
            'high': 500,
            'default': 200
        }
    }
}


class RunDimensionalityReductionAPI(BaseUnsupervisedEstimatorAPI):
    """Dimensionality reduction API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.unsupervised_type = 'reduction'
        self.param_space = hyperparameter_search_space
        self.X_train_cache = None

    def get_hyperparameter_search_space(self) -> dict:
        """Return hyperparameter search space for HPO integration."""
        model_name = self.params.get('model', 'pca')
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

    def _calculate_metrics(self, X_transformed):
        """Calculate dimensionality reduction metrics."""
        metrics = {}

        # Reconstruction error (for models that support inverse_transform)
        if hasattr(self.fitted_model, 'inverse_transform') and self.X_train_cache is not None:
            try:
                X_reconstructed = self.fitted_model.inverse_transform(X_transformed)
                reconstruction_error = np.mean((self.X_train_cache - X_reconstructed) ** 2)
                metrics['reconstruction_error'] = float(reconstruction_error)
            except:
                pass

        # Explained variance
        if hasattr(self.fitted_model, 'explained_variance_ratio_'):
            metrics['explained_variance_ratio'] = self.fitted_model.explained_variance_ratio_.tolist()
            metrics['cumulative_variance'] = float(np.sum(self.fitted_model.explained_variance_ratio_))

        # KL divergence (t-SNE)
        if hasattr(self.fitted_model, 'kl_divergence_'):
            metrics['kl_divergence'] = float(self.fitted_model.kl_divergence_)

        metrics['n_components'] = X_transformed.shape[1]

        return metrics

    def fit(self, args, X_train):
        """Fit dimensionality reduction model."""
        model_name = args.model
        self.model_name = model_name
        self.X_train_cache = X_train  # Cache for reconstruction error

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
        if model_name == 'pca':
            from sklearn.decomposition import PCA
            model = PCA(random_state=42, **final_params)
        elif model_name == 'tsne':
            from sklearn.manifold import TSNE
            model = TSNE(random_state=42, **final_params)
        elif model_name == 'umap':
            try:
                import umap
                model = umap.UMAP(random_state=42, **final_params)
            except ImportError:
                raise ValueError("UMAP not installed. Install with: pip install umap-learn")
        elif model_name == 'svd':
            from sklearn.decomposition import TruncatedSVD
            model = TruncatedSVD(random_state=42, **final_params)
        elif model_name == 'ica':
            from sklearn.decomposition import FastICA
            model = FastICA(random_state=42, **final_params)
        elif model_name == 'nmf':
            from sklearn.decomposition import NMF
            model = NMF(random_state=42, **final_params)
        else:
            raise ValueError(f"Unknown dimensionality reduction model: {model_name}")

        # Fit model
        model.fit(X_train)
        logging.info("✓ Finished fitting")

        return model

    def predict(self, X):
        """Transform data to reduced dimensionality."""
        # For t-SNE/UMAP that don't support transform, use fit_transform
        if self.model_name in ['tsne', 'umap']:
            logging.warning(
                f"{self.model_name} doesn't support transform(). "
                f"Using fit_transform on new data (not ideal)."
            )
            X_transformed = self.fitted_model.fit_transform(X)
        else:
            X_transformed = self.fitted_model.transform(X)

        # Calculate metrics
        metrics = self._calculate_metrics(X_transformed)

        logging.info(
            f"✓ Dimensionality reduction: {X.shape[1]} -> {X_transformed.shape[1]} components, "
            f"explained_var={metrics.get('cumulative_variance', 'N/A')}"
        )

        return {
            'transformed_data': X_transformed.tolist(),
            'metrics': metrics
        }


if __name__ == '__main__':
    RunDimensionalityReductionAPI().run()
