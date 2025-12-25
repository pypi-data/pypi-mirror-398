import os
import uuid
import pandas as pd
import numpy as np
from .base_model_client import BaseDockerModelClient
from AutoImblearn.pipelines.execution import docker_runner


class BaseEstimator(BaseDockerModelClient):
    """Abstract base class for sklearn-like estimators/classifiers."""

    def payload(self):
        pass
    
    def fit(self, args, X_train, y_train=None, X_eval=None, y_eval=None, **kwargs):
        """
        Fit the estimator by delegating to the Docker runner.

        The concrete subclass should ensure `payload` includes any paths/names
        needed by the remote API.
        """
        from ..exceptions import DockerContainerError
        self.args = args
        try:
            docker_runner.save_training_data(model=self, args=args, X_train=X_train, y_train=y_train, X_test=X_eval, y_test=y_eval)
            return docker_runner.run_fit(self)
        except DockerContainerError:
            raise

    def predict(self, X):
        """Predict with data X"""
        from ..exceptions import DockerContainerError

        if not hasattr(self, "args") or self.args is None:
            raise DockerContainerError(
                "Estimator must be fitted before calling predict().",
                container_id=None,
                image_name=self.image_name,
                logs=None,
                operation="predict",
            )

        base_root = getattr(self.args, "container_data_root", None)
        if base_root is None:
            raise ValueError("container_data_root is required for predict paths")
        inference_dir = os.path.join(base_root, "interim", self.args.dataset)
        os.makedirs(inference_dir, exist_ok=True)
        inference_file_name = f"X_predict_{self.container_name}_{uuid.uuid4().hex}.csv"
        inference_file_path = os.path.join(inference_dir, inference_file_name)

        try:
            if isinstance(X, pd.DataFrame):
                X_to_save = X
            else:
                X_to_save = pd.DataFrame(X)
                if X_to_save.ndim == 1 or X_to_save.shape[1] == 0:
                    X_to_save = X_to_save.to_frame(name="feature_0")
                else:
                    X_to_save.columns = [f"feature_{idx}" for idx in range(X_to_save.shape[1])]

            X_to_save.to_csv(inference_file_path, index=False, header=True)

            payload = {
                "dataset_name": self.args.dataset,
                "predict_file": f"{self.args.dataset}/{inference_file_name}",
            }
            result = docker_runner.run_predict(self, payload, result_key="predictions")
            return pd.DataFrame(result)
        finally:
            try:
                if os.path.exists(inference_file_path):
                    os.remove(inference_file_path)
            except OSError:
                pass
            docker_runner.stop_container(self)

    def predict_proba(self, X):
        """Predict class probabilities for data X."""
        if not hasattr(self, "args") or self.args is None:
            raise RuntimeError("Estimator must be fitted before calling predict_proba().")

        base_root = getattr(self.args, "container_data_root", None)
        if base_root is None:
            raise ValueError("container_data_root is required for predict_proba paths")
        inference_dir = os.path.join(base_root, "interim", self.args.dataset)
        os.makedirs(inference_dir, exist_ok=True)
        inference_file_name = f"X_predict_{self.container_name}_{uuid.uuid4().hex}.csv"
        inference_file_path = os.path.join(inference_dir, inference_file_name)

        try:
            if isinstance(X, pd.DataFrame):
                X_to_save = X
            else:
                X_to_save = pd.DataFrame(X)
                if X_to_save.ndim == 1 or X_to_save.shape[1] == 0:
                    X_to_save = X_to_save.to_frame(name="feature_0")
                else:
                    X_to_save.columns = [f"feature_{idx}" for idx in range(X_to_save.shape[1])]

            X_to_save.to_csv(inference_file_path, index=False, header=True)

            payload = {
                "dataset_name": self.args.dataset,
                "predict_file": f"{self.args.dataset}/{inference_file_name}",
            }

            probabilities = docker_runner.run_predict_proba(self, payload)
            return np.asarray(probabilities)

        finally:
            try:
                if os.path.exists(inference_file_path):
                    os.remove(inference_file_path)
            except OSError:
                pass
            docker_runner.stop_container(self)
