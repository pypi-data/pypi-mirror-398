from AutoImblearn.components.model_client.base_estimator import BaseEstimator
from AutoImblearn.components.model_client.image_spec import ImageSpec
from pathlib import Path
import os


class RunSkSurvivalModel(BaseEstimator):
    """
    Docker-based survival analysis model client.

    Supports scikit-survival models:
    - CPH: Cox Proportional Hazards
    - RSF: Random Survival Forest
    - SVM: Fast Survival SVM
    - KSVM: Fast Kernel Survival SVM
    - LASSO: Coxnet with L1 regularization
    - L1: Coxnet with full L1
    - L2: Coxnet with full L2
    - CSA: Coxnet with elastic net (l1_ratio=0.5)
    """

    def __init__(self, model="CPH", host_data_root=None, result_file_path=None, result_file_name=None, **kwargs):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")

        self.model = model

        self.result_file_path = result_file_path
        if result_file_name:
            self.result_file_name = result_file_name
        elif result_file_path:
            self.result_file_name = os.path.basename(result_file_path)
        else:
            self.result_file_name = f"model_{model}.p"

        image_spec = ImageSpec(
            image="sksurvival-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_survival_container",
            container_port=8080,
            host_data_root=host_data_root,
        )

    @property
    def payload(self):
        hyperparams = None
        model_name = self.model
        if hasattr(self.args, 'hyperparams') and self.args.hyperparams:
            # args.hyperparams is a dict: {'lr': {'C': 0.1, 'penalty': 'l1'}, 'smote': {...}}
            hyperparams = self.args.hyperparams.get(model_name, None)

        event_col = getattr(self.args, "event_column", None)
        time_col = getattr(self.args, "time_column", None)
        return {
            "metric": self.args.metric,
            "model": self.model,
            "dataset_name": self.args.dataset,
            "dataset": [
                f"{self.args.dataset}/X_train_{self.container_name}.csv",
                f"{self.args.dataset}/y_train_{self.container_name}.csv",
                f"{self.args.dataset}/X_test_{self.container_name}.csv",
                f"{self.args.dataset}/y_test_{self.container_name}.csv"
            ],
            "params": hyperparams,  # Pass hyperparameters (or None for defaults)
            "result_file_name": self.result_file_name,
            "event_column": event_col,
            "time_column": time_col,
        }
