from AutoImblearn.components.model_client.base_transformer import BaseTransformer
from AutoImblearn.components.model_client.image_spec import ImageSpec
from pathlib import Path
import os


class RunSurvivalResampler(BaseTransformer):
    """
    Docker-based survival resampler client.

    Supports resampling methods that preserve survival data structure:
    - rus: Random Under Sampling (preserves censoring info)
    - ros: Random Over Sampling (treats time as feature)
    - smote: SMOTE (treats time as feature, then reconstructs)
    """

    def __init__(self, model="rus", host_data_root=None, result_file_path=None, **resampler_kwargs):
        if host_data_root is None:
            raise ValueError("host_data_root cannot be None")
        self.result_file_path = result_file_path
        self.result_file_name = os.path.basename(self.result_file_path) if self.result_file_path else None
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
        print(host_data_root)
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.model = model

        image_spec = ImageSpec(
            image="survivalresampler-api",
            context=Path(__file__).resolve().parent,
        )

        super().__init__(
            image_spec=image_spec,
            container_name=f"{model}_survival_resampler_container",
            container_port=8080,
            keep_alive=True,
            host_data_root=host_data_root,
        )

    @property
    def payload(self):
        # Survival resamplers only work on training data
        event_col = getattr(self.args, "event_column", None)
        time_col = getattr(self.args, "time_column", None)
        return {
            "metric": self.args.metric,
            "model": self.model,
            "dataset_name": self.args.dataset,
            "dataset": [
                f"{self.args.dataset}/X_train_{self.container_name}.csv",
                f"{self.args.dataset}/y_train_{self.container_name}.csv",
            ],
            "event_column": event_col,
            "time_column": time_col,
            "result_file_name": self.result_file_name,
        }
