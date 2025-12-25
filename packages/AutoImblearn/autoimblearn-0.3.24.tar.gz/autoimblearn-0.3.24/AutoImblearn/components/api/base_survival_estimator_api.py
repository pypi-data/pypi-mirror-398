"""
Base class for survival analysis models.

Provides standardized API for survival models (Cox, Random Survival Forest, etc.)
with proper handling of censored data and survival-specific metrics.
"""

import os
import logging
import pickle
from abc import abstractmethod
from types import SimpleNamespace

import pandas as pd
from flask import request, jsonify

from .base_model_api import BaseModelAPI, Arguments


class BaseSurvivalEstimatorAPI(BaseModelAPI):
    """
    Abstract base class for survival analysis estimators.

    Supports models like:
    - Cox Proportional Hazards (CPH)
    - Random Survival Forest (RSF)
    - Survival SVM
    - Survival clustering models

    Key differences from BaseEstimatorAPI:
    - Handles survival data (Status, Survival_in_days) as structured arrays
    - Uses survival-specific metrics (C-index, log-rank statistic)
    - Supports both supervised (CPH, RSF) and unsupervised (clustering) survival models
    """

    def __init__(self, import_name):
        super().__init__(import_name)
        self.fitted_model = None  # Standardized attribute name
        self.model_type = None  # 'supervised' or 'unsupervised'
        self.app.add_url_rule('/predict', view_func=self.predict_endpoint, methods=['POST'])

    def load_survival_data(self, filepath):
        """
        Load survival data from CSV.

        Expected format depends on file type:
        - X files: Feature columns only
        - y files: Must have 'Status' (bool/int) and 'Survival_in_days' (float) columns

        Args:
            filepath: Path to CSV file

        Returns:
            - For X files: numpy array of features
            - For y files: structured array with Status and Survival_in_days
        """
        df = pd.read_csv(filepath)

        # Check if this is a survival target file (y)
        if 'Status' in df.columns and 'Survival_in_days' in df.columns:
            # Import here to avoid dependency issues if sksurv not installed
            from sksurv.util import Surv

            # Create structured array for scikit-survival
            y = Surv.from_dataframe('Status', 'Survival_in_days', df)
            return y
        else:
            # This is feature data (X)
            return df.values

    def fit_train(self, args, X_train, y_train, X_test=None, y_test=None):
        """
        Fit the survival model and evaluate on test data.

        Args:
            args: Arguments object with dataset_name, metric, etc.
            X_train: Training features
            y_train: Training survival data (structured array)
            X_test: Test features (optional)
            y_test: Test survival data (optional)

        Returns:
            Evaluation result (C-index, log-rank statistic, etc.)
        """
        # fit() RETURNS the fitted model (sklearn pattern!)
        self.fitted_model = self.fit(args, X_train, y_train, X_test, y_test)

        # Save to disk automatically
        self._save_fitted_model(args)

        # Predict on test data if provided (model already in memory)
        if X_test is not None and y_test is not None:
            result = self.predict(X_test, y_test)
            return result
        else:
            # For unsupervised models, just return success
            return {"status": "fitted"}

    def _save_fitted_model(self, params):
        """Save fitted survival model to disk for persistence"""
        if self.fitted_model is None:
            logging.warning("No fitted_model to save. Skipping persistence.")
            return

        dataset_name = params.dataset_name
        model_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "fitted_survival_estimator.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(self.fitted_model, f)

        logging.info(f"✓ Fitted survival estimator saved to {model_path}")

        # Save metadata
        metadata = {
            'model_class': type(self.fitted_model).__name__,
            'model_name': getattr(self, 'model_name', None),
            'model_type': self.model_type
        }
        metadata_path = os.path.join(model_dir, "fitted_survival_estimator_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

    def _load_fitted_model(self, params):
        """Load fitted survival model from disk if exists"""
        dataset_name = params.dataset_name
        model_path = os.path.join("/data/interim", dataset_name, "fitted_survival_estimator.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Fitted survival model not found at {model_path}")

        with open(model_path, 'rb') as f:
            self.fitted_model = pickle.load(f)

        logging.info(f"✓ Fitted survival estimator loaded from {model_path}")

        # Load metadata
        metadata_path = os.path.join("/data/interim", dataset_name, "fitted_survival_estimator_metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                if 'model_name' in metadata:
                    self.model_name = metadata['model_name']
                if 'model_type' in metadata:
                    self.model_type = metadata['model_type']

    def train(self):
        """
        Override train to handle survival data loading.

        Survival data format:
        - 4 files: [X_train.csv, y_train.csv, X_test.csv, y_test.csv]
        - y files must have Status and Survival_in_days columns
        """
        args = Arguments(self.params)
        dataset_files = self.params['dataset']

        if not isinstance(dataset_files, list) or len(dataset_files) != 4:
            raise ValueError(
                f"Survival models require 4 dataset files "
                f"[X_train, y_train, X_test, y_test], got {len(dataset_files) if isinstance(dataset_files, list) else 'non-list'}"
            )

        # Load training data
        X_train_path = os.path.join("/data/interim", dataset_files[0])
        y_train_path = os.path.join("/data/interim", dataset_files[1])
        X_test_path = os.path.join("/data/interim", dataset_files[2])
        y_test_path = os.path.join("/data/interim", dataset_files[3])

        # Load X files as regular numpy arrays
        X_train = pd.read_csv(X_train_path).to_numpy()
        X_test = pd.read_csv(X_test_path).to_numpy()

        # Load y files with survival data parser
        y_train = self.load_survival_data(y_train_path)
        y_test = self.load_survival_data(y_test_path)

        logging.info(
            f"Loading survival data: X_train {X_train.shape}, "
            f"y_train {y_train.shape}, X_test {X_test.shape}, y_test {y_test.shape}"
        )

        self.result = self.fit_train(args, X_train, y_train, X_test, y_test)
        self.save_result()

        logging.info("Finished survival model training")
        return {}, 200

    def predict_endpoint(self):
        """
        Predict/evaluate on saved interim files.

        Expects JSON with:
        - dataset_name
        - predict_files: list of 4 file names [X_train, y_train, X_test, y_test] (optional)
          If omitted, reuses the dataset files from params.
        """
        data = request.get_json(silent=True) or {}
        dataset_name = data.get("dataset_name") or self.params.get("dataset_name")
        predict_files = data.get("predict_files") or self.params.get("dataset")

        if not dataset_name:
            return jsonify({"error": "dataset_name is required"}), 400
        if not isinstance(predict_files, list) or len(predict_files) != 4:
            return jsonify({"error": "predict_files must be a list of four files [X_train,y_train,X_test,y_test]"}), 400

        X_train_path = self._resolve_interim_path(dataset_name, predict_files[0])
        y_train_path = self._resolve_interim_path(dataset_name, predict_files[1])
        X_test_path = self._resolve_interim_path(dataset_name, predict_files[2])
        y_test_path = self._resolve_interim_path(dataset_name, predict_files[3])

        for p in (X_train_path, y_train_path, X_test_path, y_test_path):
            if not os.path.exists(p):
                return jsonify({"error": f"Predict file not found: {p}"}), 404

        X_train = self._load_csv(X_train_path).to_numpy()
        X_test = self._load_csv(X_test_path).to_numpy()
        y_train = self.load_survival_data(y_train_path)
        y_test = self.load_survival_data(y_test_path)

        params = SimpleNamespace(dataset_name=dataset_name)
        if self.fitted_model is None:
            try:
                self._load_fitted_model(params)
            except FileNotFoundError as exc:
                return jsonify({"error": str(exc)}), 404

        result = self.predict(X_test, y_test)
        # Save result for consistency
        self.result = result
        self.save_result()
        return jsonify({"result": result}), 200

    def save_result(self):
        """
        Save survival model results.

        For supervised models: saves evaluation metrics (C-index, etc.)
        For unsupervised models: saves cluster assignments or risk scores
        """
        if self.result is None:
            logging.warning("No result to save.")
            return

        dataset_name = self.params['dataset_name']
        result_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(result_dir, exist_ok=True)

        # Save result
        result_path = os.path.join(result_dir, "survival_result.pkl")
        with open(result_path, 'wb') as f:
            pickle.dump(self.result, f)

        logging.info(f"✓ Survival model result saved to {result_path}")

    @abstractmethod
    def fit(self, args, X_train, y_train, X_test=None, y_test=None):
        """
        Fit the survival model on training data.

        Subclasses MUST return the fitted model (sklearn pattern).

        Args:
            args: Arguments object with parameters
            X_train: Training features (numpy array)
            y_train: Training survival data (structured array with Status, Survival_in_days)
            X_test: Test features (optional)
            y_test: Test survival data (optional)

        Returns:
            The fitted model
        """
        pass

    @abstractmethod
    def predict(self, X_test, y_test):
        """
        Predict and evaluate survival model on test data.

        For supervised models: Returns C-index or other survival metrics
        For unsupervised models: Returns cluster assignments or risk scores

        Args:
            X_test: Test features
            y_test: Test survival data

        Returns:
            dict: Evaluation results
        """
        pass
