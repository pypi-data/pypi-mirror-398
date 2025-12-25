from abc import abstractmethod
import pickle
import os
import logging

from flask import request, jsonify

from .base_model_api import BaseModelAPI


class BaseTransformerAPI(BaseModelAPI):
    """
    Abstract base class for sklearn-like transformers.

    This class provides automatic persistence of fitted models to disk,
    allowing transform() to work even after container restarts.

    Subclasses should:
    1. Set self.fitted_model = <trained_model> after training in fit()
    2. Set self.columns if needed for column metadata
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fitted_model = None  # Subclasses should set this after training
        self.columns = None  # Optional: column names for DataFrames
        self.app.add_url_rule('/transform', view_func=self.transform_endpoint, methods=['POST'])

    def fit_train(self, params, *args, **kwargs):
        """
        Fit the transformer and return the transformed training data.

        This method automatically saves the fitted model to disk after training.
        """
        # Call subclass's fit method - it RETURNS the fitted model (sklearn pattern!)
        self.fitted_model = self.fit(params, *args, **kwargs)

        # Save the fitted model to disk for persistence
        self._save_fitted_model(params)

        # Transform and return result
        # No need to load - fitted_model is already in memory
        result = self.transform(*args, **kwargs)
        return result

    def _save_fitted_model(self, params):
        """
        Save the fitted model to disk so it persists across container restarts.

        This is called automatically after fit() completes.
        """
        if self.fitted_model is None:
            logging.warning("No fitted_model to save. Skipping persistence.")
            return

        dataset_name = params.dataset_name
        model_dir = os.path.join("/data/interim", dataset_name)

        # Ensure directory exists
        os.makedirs(model_dir, exist_ok=True)

        # Save the fitted model
        model_path = os.path.join(model_dir, "fitted_transformer.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(self.fitted_model, f)

        # Save metadata (columns, etc.)
        metadata = {
            'columns': self.columns,
            'model_class': type(self.fitted_model).__name__
        }
        metadata_path = os.path.join(model_dir, "fitted_transformer_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

        logging.info(f"✓ Saved fitted model to {model_path}")

    def _load_fitted_model(self, params):
        """
        Load the fitted model from disk if it exists.

        This is called automatically before transform() if fitted_model is None.
        """
        dataset_name = params.dataset_name
        model_path = os.path.join("/data/interim", dataset_name, "fitted_transformer.pkl")
        metadata_path = os.path.join("/data/interim", dataset_name, "fitted_transformer_metadata.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Fitted model not found at {model_path}. "
                f"Make sure fit() was called before transform()."
            )

        # Load the fitted model
        with open(model_path, 'rb') as f:
            self.fitted_model = pickle.load(f)

        # Load metadata
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.columns = metadata.get('columns')

        logging.info(f"✓ Loaded fitted model from {model_path}")

    def transform_endpoint(self):
        """
        API endpoint to transform data using a fitted transformer.
        Expects JSON with transform_file and optional result_file_name.
        """
        data = request.get_json(silent=True) or {}
        transform_file = data.get('transform_file')
        result_file_name = (
            data.get('result_file_name')
            or self.params.get('result_file_name')
            or data.get('impute_file_name')
            or self.params.get('impute_file_name')
        )

        if not transform_file:
            return jsonify({"error": "transform_file is required"}), 400
        if not result_file_name:
            return jsonify({"error": "result_file_name not provided"}), 400

        dataset_name = self.params.get('dataset_name')
        if not dataset_name:
            return jsonify({"error": "dataset_name not provided in params"}), 400

        transform_data_path = self._resolve_interim_path(dataset_name, transform_file)

        if not os.path.exists(transform_data_path):
            return jsonify({"error": f"Transform file not found: {transform_file}"}), 404

        # Load the data to transform (without header since we saved without it)
        X_transform = self._load_csv(transform_data_path, header=None)

        # Load fitted model from disk if not in memory
        if hasattr(self, 'fitted_model') and self.fitted_model is None:
            self._load_fitted_model(Arguments(self.params))

        transformed_result = self.transform(data=X_transform)

        result_path = os.path.join("/data/interim", dataset_name, result_file_name)
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        with open(result_path, 'wb') as f:
            pickle.dump(transformed_result, f)

        return {}, 200

    @abstractmethod
    def fit(self, params, *args, **kwargs):
        """
        Fit the transformer on training data.

        Subclasses MUST return the fitted model (sklearn pattern).

        Returns:
            The fitted model/transformer
        """
        pass

    @abstractmethod
    def transform(self, *args, **kwargs):
        """
        Transform data using the fitted model.

        The fitted model is automatically loaded from disk if not in memory.
        """
        pass
