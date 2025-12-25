import os
from typing import Optional
from pathlib import Path

from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec


class RunAutoRSP(BaseEstimator):
    """Client wrapper for the AutoRSP hybrid model."""

    def __init__(
        self,
        host_data_root: str,
        result_file_path: Optional[str] = None,
        result_file_name: Optional[str] = None,
        metric: str = "macro_f1",
        **kwargs,
    ):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        module_dir = os.path.dirname(os.path.abspath(__file__))
        host_host_data_root = os.path.abspath(host_data_root)

        image_spec = ImageSpec(
            image="autorsp-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name="autorsp_container",
            container_port=8083,
            host_data_root=host_host_data_root,
        )

        self.metric = metric
        self.target = None
        self.result_file_path = result_file_path
        if result_file_name:
            self.result_file_name = result_file_name
        elif result_file_path:
            self.result_file_name = os.path.basename(result_file_path)
        else:
            self.result_file_name = "autorsp_result.p"

    @property
    def payload(self):
        dataset = self.args.dataset
        container_name = self.container_name

        payload = {
            "metric": self.metric,
            "target": self.target,
            "dataset_name": dataset,
            "dataset": [
                f"{dataset}/X_train_{container_name}.csv",
                f"{dataset}/y_train_{container_name}.csv",
                f"{dataset}/X_test_{container_name}.csv",
                f"{dataset}/y_test_{container_name}.csv",
            ],
        }

        if self.result_file_name:
            payload["result_file_name"] = self.result_file_name

        return payload

    def fit(self, args, X_train, y_train=None, X_test=None, y_test=None):
        if y_train is None or y_test is None:
            raise ValueError("AutoRSP requires labeled training and test data.")

        target = getattr(args, "target_name", None)
        if not target:
            raise ValueError(
                "AutoRSP requires args.target_name to be set."
            )

        metric = getattr(args, "metric", None) or self.metric
        if metric != "macro_f1":
            raise ValueError("AutoRSP currently supports only the 'macro_f1' metric.")

        self.metric = metric
        self.target = target

        return super().fit(
            args,
            X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            result_file_name=self.result_file_name,
            result_file_path=self.result_file_path,
        )
