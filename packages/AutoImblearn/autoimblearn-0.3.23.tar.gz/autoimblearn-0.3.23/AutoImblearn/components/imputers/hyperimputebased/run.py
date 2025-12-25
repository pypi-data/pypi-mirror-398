from functools import cached_property
import os
from pathlib import Path

from AutoImblearn.components.model_client.base_transformer import BaseTransformer
from AutoImblearn.components.model_client.image_spec import ImageSpec
import pandas as pd


class RunHyperImpute(BaseTransformer):
    # TODO make model parameter work

    def __init__(self, model="ii", host_data_root=None, categorical_columns=None, result_file_path=None, **imputer_kwargs):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        super().__init__(
            image_spec=ImageSpec(
                image="hyperimpute-api",
                context=Path(__file__).resolve().parent,
            ),
            container_name=f"{model}_container",
            container_port=8080,
            host_data_root=host_data_root,
        )

        self.model = model
        self.categorical_columns = categorical_columns
        self.result_file_path = result_file_path
        self.result_file_name = os.path.basename(self.result_file_path) if self.result_file_path else None
        self.imputer_kwargs = imputer_kwargs

    @cached_property
    def payload(self):
        # Imputers only need X_train (features) during fit()
        # Imputation is unsupervised - it fills missing values based on feature patterns
        # Additional data is transformed via the /transform endpoint
        # Files are saved to /data/interim/{dataset_name}/
        return {
            "model": self.model,
            "metric": self.args.metric,
            "dataset_name": self.args.dataset,
            "dataset": [
                f"{self.args.dataset}/X_train_{self.container_name}.csv",
            ],
            "categorical_columns": self.categorical_columns,
            "imputer_kwargs": self.imputer_kwargs,
            "result_file_name": self.result_file_name
        }
