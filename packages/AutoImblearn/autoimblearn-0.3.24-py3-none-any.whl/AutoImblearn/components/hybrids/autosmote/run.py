from typing import Optional
from pathlib import Path

import pandas as pd

# from ..model_client.base_model_client import BaseDockerModelClient
from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec
import os


class RunAutoSmote(BaseEstimator):
    def __init__(
        self,
        host_data_root: str,
        result_file_path: Optional[str] = None,
        metric: str = "auroc",
        **kwargs,
    ):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        host_host_data_root = os.path.abspath(host_data_root)
        module_dir = os.path.dirname(os.path.abspath(__file__))
        image_spec = ImageSpec(
            image="autosmote-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name="autosmote_container",
            container_port=8080,
            host_data_root=host_host_data_root,
        )

        self.result_file_path = result_file_path
        self.result_file_name = (
            os.path.basename(result_file_path) if result_file_path else None
        )
        self.metric = metric

    @property
    def payload(self):
        dataset = self.args.dataset
        container_name = self.container_name

        payload = {
            "metric": self.metric,
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
        if hasattr(args, "metric"):
            self.metric = args.metric
        return super().fit(
            args,
            X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
            result_file_name=self.result_file_name,
            result_file_path=self.result_file_path,
        )


if __name__ == "__main__":

    input_csv = "pima-indians-diabetes-missing.csv "
    label_col = "Status"

    runner = RunAutoSmote()

    print("[✓] Training model...")
    runner.fit(input_csv, y_train=label_col)

    print("[✓] Predicting (generating balanced data)...")
    result_df = runner.predict(input_csv)

    output_csv = input_csv.replace(".csv", "_balanced.csv")
    result_df.to_csv(output_csv, index=False)
    print(f"[✓] Saved balanced output to: {output_csv}")
