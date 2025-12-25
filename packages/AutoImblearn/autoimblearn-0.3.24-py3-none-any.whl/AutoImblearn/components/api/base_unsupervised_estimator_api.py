"""
Base class for unsupervised learning models.

Provides standardized API for clustering, dimensionality reduction,
and anomaly detection models.
"""

import os
import logging
import pickle
from abc import abstractmethod
import pandas as pd
import numpy as np
from flask import request, jsonify
from .base_model_api import BaseModelAPI, Arguments


class BaseUnsupervisedEstimatorAPI(BaseModelAPI):
    """
    Abstract base class for unsupervised learning estimators.

    Supports:
    - Clustering: KMeans, DBSCAN, Hierarchical, GMM, etc.
    - Dimensionality Reduction: PCA, t-SNE, UMAP, etc.
    - Anomaly Detection: IsolationForest, One-Class SVM, LOF, etc.

    Key differences from BaseEstimatorAPI:
    - Does not require y_train or y_test
    - Uses unsupervised metrics (silhouette, inertia, explained variance, etc.)
    - Supports both fit/predict and fit/transform patterns
    """

    def __init__(self, import_name):
        super().__init__(import_name)
        self.fitted_model = None  # Standardized attribute name
        self.unsupervised_type = None  # 'clustering', 'reduction', or 'anomaly'
        self.columns = None  # For dimensionality reduction
        self.app.add_url_rule('/transform', view_func=self.transform_data, methods=['POST'])

    def fit_train(self, args, X_train, X_test=None):
        """
        Fit the unsupervised model on training data.

        Args:
            args: Arguments object with dataset_name, metric, etc.
            X_train: Training features (unlabeled data)
            X_test: Test features (optional, for evaluation)

        Returns:
            Evaluation result or transformed data
        """
        # fit() RETURNS the fitted model (sklearn pattern!)
        self.fitted_model = self.fit(args, X_train)

        # Save to disk automatically
        self._save_fitted_model(args)

        # Get result (predictions, transformations, or metrics)
        if X_test is not None:
            result = self.predict(X_test)
        else:
            # For some models, return training predictions/transformations
            result = self.predict(X_train)

        return result

    def _save_fitted_model(self, params):
        """Save fitted unsupervised model to disk for persistence"""
        if self.fitted_model is None:
            logging.warning("No fitted_model to save. Skipping persistence.")
            return

        dataset_name = params.dataset_name
        model_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "fitted_unsupervised_estimator.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(self.fitted_model, f)

        logging.info(f"✓ Fitted unsupervised estimator saved to {model_path}")

        # Save metadata
        metadata = {
            'model_class': type(self.fitted_model).__name__,
            'model_name': getattr(self, 'model_name', None),
            'unsupervised_type': self.unsupervised_type,
            'columns': self.columns  # For dimensionality reduction
        }
        metadata_path = os.path.join(model_dir, "fitted_unsupervised_estimator_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

    def _load_fitted_model(self, params):
        """Load fitted unsupervised model from disk if exists"""
        dataset_name = params.dataset_name
        model_path = os.path.join("/data/interim", dataset_name, "fitted_unsupervised_estimator.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Fitted unsupervised model not found at {model_path}")

        with open(model_path, 'rb') as f:
            self.fitted_model = pickle.load(f)

        logging.info(f"✓ Fitted unsupervised estimator loaded from {model_path}")

        # Load metadata
        metadata_path = os.path.join("/data/interim", dataset_name, "fitted_unsupervised_estimator_metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                if 'model_name' in metadata:
                    self.model_name = metadata['model_name']
                if 'unsupervised_type' in metadata:
                    self.unsupervised_type = metadata['unsupervised_type']
                if 'columns' in metadata:
                    self.columns = metadata['columns']

    def train(self):
        """
        Override train to handle unsupervised data loading.

        Unsupervised data format:
        - 1 file: [X_train.csv] - fit on training data only
        - 2 files: [X_train.csv, X_test.csv] - fit on train, evaluate on test
        """
        args = Arguments(self.params)
        dataset_files = self.params['dataset']

        if not isinstance(dataset_files, list):
            raise ValueError(f"Expected list of dataset files, got {type(dataset_files)}")

        if len(dataset_files) == 1:
            # Fit on training data only
            X_train_path = os.path.join("/data/interim", dataset_files[0])
            X_train = pd.read_csv(X_train_path).to_numpy()

            logging.info(f"Loading unsupervised data: X_train {X_train.shape}")
            self.result = self.fit_train(args, X_train, X_test=None)

        elif len(dataset_files) == 2:
            # Fit on train, evaluate on test
            X_train_path = os.path.join("/data/interim", dataset_files[0])
            X_test_path = os.path.join("/data/interim", dataset_files[1])

            X_train = pd.read_csv(X_train_path).to_numpy()
            X_test = pd.read_csv(X_test_path).to_numpy()

            logging.info(f"Loading unsupervised data: X_train {X_train.shape}, X_test {X_test.shape}")
            self.result = self.fit_train(args, X_train, X_test=X_test)

        else:
            raise ValueError(
                f"Unsupervised models require 1 or 2 dataset files "
                f"[X_train] or [X_train, X_test], got {len(dataset_files)}"
            )

        self.save_result()

        logging.info("Finished unsupervised model training")
        return {}, 200

    def save_result(self):
        """
        Save unsupervised model results.

        For clustering: saves cluster assignments and metrics
        For dimensionality reduction: saves transformed data
        For anomaly detection: saves anomaly scores and predictions
        """
        if self.result is None:
            logging.warning("No result to save.")
            return

        dataset_name = self.params['dataset_name']
        result_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(result_dir, exist_ok=True)

        # Save result
        result_path = os.path.join(result_dir, "unsupervised_result.pkl")
        with open(result_path, 'wb') as f:
            pickle.dump(self.result, f)

        logging.info(f"✓ Unsupervised model result saved to {result_path}")

    def transform_data(self):
        """
        Override transform_data to support dimensionality reduction models.

        Handles both:
        - Standard transform (e.g., PCA, SVD)
        - fit_transform-only models (e.g., t-SNE, UMAP)
        """
        data = request.get_json()

        # If transform_file is provided, load and transform that data
        if data and 'transform_file' in data:
            transform_file = data['transform_file']
            transform_data_path = os.path.join("/data/interim", self.params['dataset_name'], transform_file)

            if os.path.exists(transform_data_path):
                # Load the data to transform (without header since we saved without it)
                X_transform = pd.read_csv(transform_data_path, header=None)

                # CRITICAL: Load fitted model from disk if not in memory
                if hasattr(self, 'fitted_model') and self.fitted_model is None:
                    self._load_fitted_model(Arguments(self.params))

                # Check if model supports transform
                if hasattr(self.fitted_model, 'transform'):
                    # Standard transform (PCA, ICA, NMF, etc.)
                    transformed_result = self.fitted_model.transform(X_transform)
                elif hasattr(self.fitted_model, 'predict'):
                    # Clustering or anomaly detection - use predict
                    transformed_result = self.fitted_model.predict(X_transform)
                else:
                    # Models like t-SNE/UMAP that only support fit_transform
                    logging.warning(
                        f"Model {type(self.fitted_model).__name__} does not support transform(). "
                        f"Using fit_transform on new data (not ideal)."
                    )
                    transformed_result = self.fitted_model.fit_transform(X_transform)

                # Save the transformed result
                result_file = data.get('result_file', 'transformed_result.p')
                result_path = os.path.join("/data/interim", self.params['dataset_name'], result_file)
                with open(result_path, 'wb') as f:
                    pickle.dump(transformed_result, f)

                return {}, 200
            else:
                return jsonify({"error": f"Transform file not found: {transform_file}"}), 404

        # Fallback: just return OK (result already saved from training)
        return {}, 200

    @abstractmethod
    def fit(self, args, X_train):
        """
        Fit the unsupervised model on training data.

        Subclasses MUST return the fitted model (sklearn pattern).

        Args:
            args: Arguments object with parameters
            X_train: Training features (numpy array, unlabeled)

        Returns:
            The fitted model
        """
        pass

    @abstractmethod
    def predict(self, X):
        """
        Apply fitted model to data.

        For clustering: Returns cluster assignments
        For dimensionality reduction: Returns transformed data
        For anomaly detection: Returns anomaly predictions

        Args:
            X: Features to predict/transform

        Returns:
            Predictions, transformations, or metrics
        """
        pass
