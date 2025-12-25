from .base_model_api import BaseModelAPI
from abc import abstractmethod
import pickle
import os
import logging
from types import SimpleNamespace

import numpy as np
import pandas as pd
from flask import jsonify, request


class BaseEstimatorAPI(BaseModelAPI):
    """Abstract base class for sklearn-like estimators/classifiers."""

    def __init__(self, import_name):
        super().__init__(import_name)
        self.fitted_model = None  # Standardized attribute name
        self.app.add_url_rule('/predict', view_func=self.predict_endpoint, methods=['POST'])
        self.app.add_url_rule('/predict_proba', view_func=self.predict_proba_endpoint, methods=['POST'])

    def fit_train(self, args, X_train, y_train, X_test, y_test):
        # fit() RETURNS the fitted model (sklearn pattern!)
        self.fitted_model = self.fit(args, X_train, y_train, X_test, y_test)

        # Save to disk automatically
        self._save_fitted_model(args)

        # Predict on test data (model already in memory)
        metrics = self.predict(X_test, y_test)
        if not isinstance(metrics, dict):
            metrics = {self._infer_primary_metric_name(): metrics}

        self.result = metrics
        return metrics

    def _infer_dataset_name(self, dataset_name_hint=None):
        if dataset_name_hint:
            return dataset_name_hint
        if isinstance(self.params, dict):
            return self.params.get('dataset_name')
        return getattr(self.params, 'dataset_name', None)

    def predict_proba_endpoint(self):
        data = request.get_json(silent=True) or {}
        dataset_name, X_input, err = self._load_prediction_payload(data)
        if err:
            return err

        if self.fitted_model is None:
            try:
                self._load_fitted_model(SimpleNamespace(dataset_name=dataset_name))
            except FileNotFoundError as exc:
                return jsonify({"error": str(exc)}), 404

        try:
            probabilities = self.predict_proba(X_input)
        except NotImplementedError as exc:
            return jsonify({"error": str(exc)}), 400

        if isinstance(probabilities, pd.DataFrame):
            probs = probabilities.values.tolist()
        elif isinstance(probabilities, pd.Series):
            probs = probabilities.to_list()
        elif isinstance(probabilities, np.ndarray):
            probs = probabilities.tolist()
        else:
            probs = probabilities

        return jsonify({"probabilities": probs}), 200

    def predict_endpoint(self):
        data = request.get_json(silent=True) or {}
        dataset_name, X_input, err = self._load_prediction_payload(data)
        if err:
            return err

        if self.fitted_model is None:
            try:
                self._load_fitted_model(SimpleNamespace(dataset_name=dataset_name))
            except FileNotFoundError as exc:
                return jsonify({"error": str(exc)}), 404

        try:
            preds = self.predict(X_input)
        except NotImplementedError as exc:
            return jsonify({"error": str(exc)}), 400

        if isinstance(preds, pd.DataFrame):
            payload = preds.to_dict(orient="records")
        elif isinstance(preds, pd.Series):
            payload = preds.to_list()
        elif isinstance(preds, np.ndarray):
            payload = preds.tolist()
        else:
            payload = preds

        return jsonify({"predictions": payload}), 200

    def _load_prediction_payload(self, data):
        """Resolve dataset_name and load predict CSV."""
        dataset_name = self._infer_dataset_name(data.get('dataset_name'))
        predict_file = data.get('predict_file')

        if not dataset_name:
            return None, None, (jsonify({"error": "dataset_name is required"}), 400)
        if not predict_file:
            return None, None, (jsonify({"error": "predict_file is required"}), 400)

        file_path = self._resolve_interim_path(dataset_name, predict_file)
        if not os.path.exists(file_path):
            return None, None, (jsonify({"error": f"Predict file not found: {predict_file}"}), 404)

        X_input = self._load_csv(file_path)
        return dataset_name, X_input, None

    def _save_fitted_model(self, params):
        """Save fitted model to disk for persistence"""
        if self.fitted_model is None:
            logging.warning("No fitted_model to save. Skipping persistence.")
            return

        dataset_name = params.dataset_name
        model_dir = os.path.join("/data/interim", dataset_name)
        os.makedirs(model_dir, exist_ok=True)

        model_path = os.path.join(model_dir, "fitted_estimator.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(self.fitted_model, f)

        logging.info(f"✓ Fitted estimator saved to {model_path}")

        # Save metadata
        metadata = {
            'model_class': type(self.fitted_model).__name__,
            'model_name': getattr(self, 'clf_name', None)
        }
        metadata_path = os.path.join(model_dir, "fitted_estimator_metadata.pkl")
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)

    def _load_fitted_model(self, params):
        """Load fitted model from disk if exists"""
        dataset_name = params.dataset_name
        model_path = os.path.join("/data/interim", dataset_name, "fitted_estimator.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Fitted model not found at {model_path}")

        with open(model_path, 'rb') as f:
            self.fitted_model = pickle.load(f)

        logging.info(f"✓ Fitted estimator loaded from {model_path}")

        # Load metadata
        metadata_path = os.path.join("/data/interim", dataset_name, "fitted_estimator_metadata.pkl")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                if 'model_name' in metadata:
                    self.clf_name = metadata['model_name']

    @abstractmethod
    def fit(self, args, X_train, y_train, X_test=None, y_test=None):
        pass

    @abstractmethod
    def predict(self, X_test, y_test):
        pass

    @abstractmethod
    def predict_proba(self, X_test):
        pass

    def _infer_primary_metric_name(self):
        if isinstance(self.params, dict):
            return self.params.get('metric', 'metric')
        return getattr(self.params, 'metric', 'metric')
