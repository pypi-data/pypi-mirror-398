import os
from pathlib import Path
from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec


class RunTPOT(BaseEstimator):
    """
    TPOT AutoML client using Docker containerization.

    Follows the standardized BaseEstimator pattern with automatic
    Docker lifecycle management, dynamic port allocation, and container pooling support.
    """

    def __init__(self, host_data_root=None):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        image_spec = ImageSpec(
            image="tpot-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name="tpot_container",
            container_port=8080,  # Internal port, external will be dynamic
            host_data_root=host_data_root,
        )

    @property
    def payload(self):
        """
        Create payload for TPOT AutoML training.

        Returns:
            dict: Payload containing metric, dataset info, and file paths
        """
        return {
            "metric": self.args.metric,
            "model": "tpot",  # Identifier for AutoML system
            "dataset_name": self.args.dataset,
            "dataset": [
                f"{self.args.dataset}/X_train_{self.container_name}.csv",
                f"{self.args.dataset}/y_train_{self.container_name}.csv",
                f"{self.args.dataset}/X_test_{self.container_name}.csv",
                f"{self.args.dataset}/y_test_{self.container_name}.csv"
            ],
            "params": None,
        }
