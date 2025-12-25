"""
Docker client for clustering models.

Supports:
- KMeans: Classic centroid-based clustering
- DBSCAN: Density-based clustering
- AgglomerativeClustering: Hierarchical clustering
- GaussianMixture: Probabilistic clustering
- MeanShift: Mode-seeking clustering
- SpectralClustering: Graph-based clustering
"""

from pathlib import Path
import os

from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec


class RunClusteringModel(BaseEstimator):
    """
    Docker client for clustering models.

    Args:
        model: Model name (e.g., 'kmeans', 'dbscan', 'hierarchical', 'gmm')
        host_data_root: Path to data folder for volume mounting
    """

    def __init__(self, model="kmeans", host_data_root=None):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        image_spec = ImageSpec(
            image="clustering-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_clustering_container",
            api_base_url="http://localhost",
            port_bindings={5000: None}  # Random host port
            ,
            host_data_root=host_data_root,
        )

        self.model_name = model
        self.supported_metrics = [
            'silhouette',      # Silhouette score
            'calinski',        # Calinski-Harabasz index
            'davies_bouldin',  # Davies-Bouldin index
            'inertia',         # Within-cluster sum of squares (KMeans)
        ]

# TODO write payload
