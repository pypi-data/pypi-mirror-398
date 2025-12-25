from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec
from pathlib import Path
import os


class RunSurvivalUnsupervised(BaseEstimator):
    """
    Docker client for survival unsupervised learning models.

    Args:
        model: Model name (e.g., 'survival_tree', 'survival_kmeans')
        host_data_root: Path to data folder for volume mounting
    """

    def __init__(self, model="survival_tree", host_data_root=None):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")
        self.model = model

        image_spec = ImageSpec(
            image="survival-unsupervised-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_survival_unsupervised_container",
            container_port=8080,
            host_data_root=host_data_root,
        )

    @property
    def payload(self):
        # TODO write payload
        pass

        #     self.model_name = model
        # self.supported_metrics = [
        #     'log_rank',        # Log-rank statistic for cluster separation
        #     'c_index',         # Within-cluster C-index
        #     'silhouette',      # Silhouette score adapted for survival
        # ]
