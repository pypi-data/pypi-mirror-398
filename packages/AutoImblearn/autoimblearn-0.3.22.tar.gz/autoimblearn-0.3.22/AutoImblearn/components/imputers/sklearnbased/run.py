# AutoImblearn/components/imputers/sklearnbased/run.py
from functools import cached_property
import os
from pathlib import Path

from AutoImblearn.components.model_client.base_transformer import BaseTransformer
from AutoImblearn.components.model_client.image_spec import ImageSpec


class RunSklearnImpute(BaseTransformer):
    # TODO make model parameter work

    def __init__(self, model="ii", host_data_root=None, categorical_columns=None, result_file_path=None, **imputer_kwargs):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        super().__init__(
            image_spec=ImageSpec(
                image="sklearnimpute-api",
                context=Path(__file__).resolve().parent,
            ),
            container_name=f"{model}_container",
            # TODO make port dynamic
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
        # Get hyperparameters: first check args.hyperparams, then fall back to self.imputer_kwargs
        imputer_params = self.imputer_kwargs  # From constructor
        if hasattr(self.args, 'hyperparams') and self.args.hyperparams:
            # Override with hyperparams from args if provided
            imputer_params = self.args.hyperparams.get(self.model, imputer_params)

        # Imputers only need X (features), not y (target)
        # Imputation is unsupervised - it fills missing values based on feature patterns
        # Files are saved to /data/interim/{dataset_name}/
        return {
            "metric": self.args.metric,
            "model": self.model,
            "dataset_name": self.args.dataset,
            "dataset": [
                f"{self.args.dataset}/X_train_{self.container_name}.csv",
                # f"{self.args.dataset}/X_test_{self.container_name}.csv"
            ],
            "categorical_columns": self.categorical_columns,
            "imputer_kwargs": imputer_params,  # Pass hyperparameters
            "result_file_name": self.result_file_name
        }
