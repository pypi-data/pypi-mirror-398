import pickle
import pandas as pd
import numpy as np
import os
from .base_model_client import BaseDockerModelClient
from AutoImblearn.pipelines.execution import docker_runner


class BaseTransformer(BaseDockerModelClient):
    """ Abstract base class for sklearn-like transformers.

    This class provides a sklearn-compatible interface for Docker-based transformers.

    Workflow:
    1. fit(args, X_train, y=None): Fit the transformer on training data (container stays running)
    2. transform(X): Transform new data using the fitted transformer (calls Docker API, container stays running)
    3. Container cleanup happens when object is deleted or cleanup() is called explicitly

    Note: Container stays alive across multiple transform() calls to avoid rebuild overhead.
    """

    def __init__(self, *args, keep_alive: bool = True, **kwargs):
        # Set is_transformer flag based on keep_alive preference
        super().__init__(*args, **kwargs, is_transformer=keep_alive)
        self.keep_container_alive = keep_alive

    def transform(self, X, y=None):
        """
        Transform the input data X using the fitted transformer.

        This method:
        1. Checks if container is still running (restarts if needed)
        2. Saves X to a temporary CSV file
        3. Calls the Docker container's /transform endpoint
        4. Loads and returns the transformed result

        The container stays running to allow multiple transform() calls.

        Args:
            X: Data to transform (DataFrame or numpy array)
            y: Ignored (for sklearn compatibility)

        Returns:
            Transformed data as DataFrame
        """
        from ..exceptions import DockerContainerError

        try:
            # Check if we ever had a container
            if not hasattr(self, 'args'):
                raise DockerContainerError(
                    "No container running. Call fit() before transform().",
                    container_id=None,
                    image_name=self.image_name,
                    logs=None,
                    operation="transform"
                )

            # Save the data to transform
            transform_csv_name = f"X_transform_{self.container_name}.csv"
            base_root = getattr(self.args, "container_data_root", None)
            if base_root is None:
                raise DockerContainerError(
                    "container_data_root is required for transformer I/O paths",
                    container_id=self.container_id,
                    image_name=self.image_name,
                    operation="transform"
                )
            transform_csv_path = os.path.join(
                base_root, "interim", self.args.dataset, transform_csv_name
            )

            if isinstance(X, pd.DataFrame):
                X.to_csv(transform_csv_path, index=False, header=False)
            else:
                np.savetxt(transform_csv_path, X, delimiter=",")

            # Call the /transform endpoint
            headers = {"Content-Type": "application/json"}
            result_artifact_path = getattr(self, "result_file_path", None)
            if not result_artifact_path:
                raise DockerContainerError(
                    "Transformer missing result file path. Ensure result_file_path is provided during initialization.",
                    container_id=self.container_id,
                    image_name=self.image_name,
                    operation="transform"
                )

            artifact_name = os.path.basename(result_artifact_path)
            transform_artifact_name = artifact_name.replace('.p', '_transform.p')

            payload = {
                "transform_file": transform_csv_name,
                "result_file_name": transform_artifact_name
            }

            docker_runner.run_transform(self, payload)

            # Load the transformed result
            result_path = result_artifact_path.replace('.p', '_transform.p')
            with open(result_path, 'rb') as f:
                result = pickle.load(f)

            return result

        except Exception as e:
            if isinstance(e, DockerContainerError):
                raise
            logs = docker_runner.get_container_logs(self) if self.container_id else None
            raise DockerContainerError(
                f"Transform failed: {str(e)}",
                container_id=self.container_id,
                image_name=self.image_name,
                logs=logs,
                operation="transform"
            ) from e

    def fit_transform(self, args, X, y=None):
        """
        Fit the transformer and return the transformed training data.

        This sklearn-compatible method:
        1. Calls fit(args, X, y) to train the transformer (via Docker API)
        2. Calls transform(X) to get the transformed result

        Args:
            args: Arguments object with path, dataset, etc.
            X: Training data to fit and transform
            y: Labels (optional, for sklearn compatibility)

        Returns:
            Transformed training data
        """
        # Fit the transformer (saves data and triggers remote fit)
        self.fit(args, X, y)
        # Transform the same data
        return self.transform(X)

    def fit(self, args, X, y=None):
        """
        Trigger remote fit via Docker API for transformers.
        """
        from ..exceptions import DockerContainerError
        self.args = args
        try:
            docker_runner.save_training_data(model=self, args=args, X_train=X, y_train=y)
            return docker_runner.run_fit(self)
        except DockerContainerError:
            raise

    def cleanup(self):
        """
        Explicitly cleanup (stop and remove) the Docker container.

        Call this when you're done with all transformations.
        """
        try:
            if self.container_id:
                docker_runner.stop_container(self)
        except Exception as e:
            import logging
            logging.error(f"Failed to cleanup container: {e}")

    def __del__(self):
        """
        Cleanup container when object is garbage collected.
        """
        self.cleanup()

    def fit_resample(self, args, X, y):
        """
        Fit and resample the data (for resampler components).

        This method is for resamplers that transform both X and y.
        It combines fit and transform but returns both X and y.

        Args:
            X: Feature data
            y: Labels

        Returns:
            Tuple of (X_resampled, y_resampled)
        """
        from ..exceptions import DockerContainerError

        try:
            # Call fit with both X and y
            self.fit(args, X, y)

            # The resampler API should save both X and y resampled
            # Load them back from the saved files
            impute_file_path_X = self.result_file_path
            impute_file_path_y = self.result_file_path.replace('.p', '_y.p')

            with open(impute_file_path_X, "rb") as f:
                X_resampled = pickle.load(f)

            with open(impute_file_path_y, "rb") as f:
                y_resampled = pickle.load(f)

            return X_resampled, y_resampled

        except Exception as e:
            logs = docker_runner.get_container_logs(self) if hasattr(self, 'container_id') and self.container_id else None
            raise DockerContainerError(
                f"Fit resample failed: {str(e)}",
                container_id=getattr(self, 'container_id', None),
                image_name=self.image_name,
                logs=logs,
                operation="fit_resample"
            ) from e
