"""
Docker client for dimensionality reduction models.

Supports:
- PCA: Principal Component Analysis
- t-SNE: t-Distributed Stochastic Neighbor Embedding
- UMAP: Uniform Manifold Approximation and Projection
- TruncatedSVD: Singular Value Decomposition
- ICA: Independent Component Analysis
- NMF: Non-negative Matrix Factorization
"""

from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec
from pathlib import Path
import os


class RunDimensionalityReduction(BaseEstimator):
    """
    Docker client for dimensionality reduction models.

    Args:
        model: Model name (e.g., 'pca', 'tsne', 'umap')
        host_data_root: Path to data folder for volume mounting
    """

    def __init__(self, model="pca", host_data_root=None):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        image_spec = ImageSpec(
            image="reduction-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_reduction_container",
            host_data_root=host_data_root,
            api_base_url="http://localhost",
            port_bindings={5000: None}  # Random host port
        )

        self.model_name = model
        self.supported_metrics = [
            'reconstruction',  # Reconstruction error
            'explained_var',   # Explained variance ratio (PCA, TruncatedSVD)
            'kl_divergence',   # KL divergence (t-SNE)
        ]
