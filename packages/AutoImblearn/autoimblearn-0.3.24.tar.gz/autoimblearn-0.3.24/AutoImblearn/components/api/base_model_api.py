import os
import logging
import pickle
import traceback
from abc import ABC, abstractmethod
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from types import SimpleNamespace
from typing import Optional

class Arguments:
    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)

class BaseModelAPI(ABC):
    def __init__(self, import_name):
        self.app = Flask(import_name)
        self.params = {}
        self.result = None

        # Register routes
        self.app.add_url_rule('/set', view_func=self.set_params, methods=['POST'])
        self.app.add_url_rule('/train', view_func=self.train, methods=['POST'])
        self.app.add_url_rule('/health', view_func=self.health, methods=['GET'])
        self.app.add_url_rule('/hyperparameters', view_func=self.get_hyperparameters, methods=['GET'])
        self._register_error_handlers()


    def get_hyperparameters(self):
        return jsonify(self.get_hyperparameter_search_space())

    def _register_error_handlers(self):
        @self.app.errorhandler(Exception)
        def _handle_unexpected_error(exc):
            tb = traceback.format_exc()
            logging.exception("Unhandled API error: %s", exc)
            response = {
                "error": str(exc),
                "exception": exc.__class__.__name__,
                "traceback": tb,
            }
            return jsonify(response), 500

    @abstractmethod
    def get_hyperparameter_search_space(self) -> dict:
        # Returns a dictionary that defines the hyperparameters and their ranges/types.
        pass

    def _resolve_interim_path(self, dataset_name: str, filename: str) -> str:
        """Resolve a file path under /data/interim for a dataset."""
        direct_path = os.path.join("/data/interim", filename)
        nested_path = os.path.join("/data/interim", dataset_name, filename)
        if os.path.exists(direct_path):
            return direct_path
        return nested_path

    def _load_csv(self, path: str, header: Optional[int] = 0):
        """Load CSV with optional header handling."""
        return pd.read_csv(path, header=header)

    def save_result(self):
        """
        Save main result (transformed X_train for imputers/resamplers).
        Expect subclasses to set self.result and optionally self.result_y.
        """
        result_file_name = self.params.get('result_file_name')
        if not result_file_name:
            result_file_name = self.params.get('impute_file_name')
        if not result_file_name:
            raise KeyError("result_file_name not provided in parameters")

        result_path = os.path.join("/data/interim", self.params['dataset_name'], result_file_name)
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        with open(result_path, 'wb') as f:
            pickle.dump(self.result, f)

        # For resamplers, also save y if it exists
        if hasattr(self, 'result_y') and self.result_y is not None:
            result_y_path = result_path.replace('.p', '_y.p')
            with open(result_y_path, 'wb') as f:
                pickle.dump(self.result_y, f)

    def dict_to_namespace(self):
        # Parse dict object to python class attributes like object
        def recurse(d):
            ns = {}
            for k, v in d.items():
                if isinstance(v, dict) and "default" in v:
                    ns[k] = v["default"]
                elif isinstance(v, dict):
                    ns[k] = recurse(v)
                else:
                    ns[k] = v  # fallback
            return SimpleNamespace(**ns)
        return recurse(self.params)

    def health(self):
        return "OK", 200

    def set_params(self):
        """Set training parameters"""
        def recursive_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and isinstance(d.get(k), dict):
                    recursive_update(d[k], v)
                else:
                    d[k] = v

        data = request.get_json()

        recursive_update(self.params, data)

        if 'metric' not in self.params:
        # if 'metric' not in self.params
            raise Exception("data not complete, need to include metric")
        if 'dataset_name' not in self.params:
            raise Exception("data not complete, need to include dataset_name")

        # Promote survival-specific params if provided
        evt = self.params.get("event_column")
        time_col = self.params.get("time_column")
        if evt:
            self.params.setdefault("target_name", evt)
            self.params["event_column"] = evt
        if time_col:
            self.params["time_column"] = time_col
        return jsonify(self.params), 201

    @abstractmethod
    def fit_train(self, params, *args, **kwargs):
        """Control the actual model training process"""
        pass

    def train(self):
        args = Arguments(self.params)
        dataset = self.params['dataset']
        if isinstance(dataset, str):
            # Old format: single dataset file from /data/raw
            data = pd.read_csv(os.path.join("/data/raw", dataset))
            self.result = self.fit_train(args, data=data)
        else:
            # List format: split files from /data/interim
            dataset_files = dataset

            if len(dataset_files) == 1:
                # Imputers: [X_train] - fit on training data only
                X_train = pd.read_csv(os.path.join("/data/interim", dataset_files[0]))
                logging.info("Loading imputer data: X_train only")
                self.result = self.fit_train(args, X_train=X_train)

            elif len(dataset_files) == 2:
                # Resamplers: [X_train, y_train] - resample training only
                X_train = pd.read_csv(os.path.join("/data/interim", dataset_files[0]))
                y_train = pd.read_csv(os.path.join("/data/interim", dataset_files[1]))
                if y_train.shape[1] == 1:
                    y_train = y_train.to_numpy().ravel()

                logging.info("Loading resampler data: X_train, y_train")
                self.result = self.fit_train(args, X_train=X_train, y_train=y_train)

            elif len(dataset_files) == 4:
                # Classifiers: [X_train, y_train, X_test, y_test]
                X_train = pd.read_csv(os.path.join("/data/interim", dataset_files[0]))
                y_train = pd.read_csv(os.path.join("/data/interim", dataset_files[1]))
                if y_train.shape[1] == 1:
                    y_train = y_train.to_numpy().ravel()

                X_test = pd.read_csv(os.path.join("/data/interim", dataset_files[2]))
                y_test = pd.read_csv(os.path.join("/data/interim", dataset_files[3]))
                if y_test.shape[1] == 1:
                    y_test = y_test.to_numpy().ravel()
                logging.info("Loading classifier data: X_train, y_train, X_test, y_test")
                self.result = self.fit_train(args, X_train, y_train, X_test, y_test)
            elif len(dataset_files) == 3:
                return jsonify({"error": "Classifier payload missing test labels (expected 4 files: X_train, y_train, X_test, y_test)."}), 400

            else:
                raise ValueError(f"Invalid dataset format: expected 1 (imputers), 2 (resamplers), or 4 (classifiers) files, got {len(dataset_files)}")

        self.save_result()

        logging.info("finished training")
        return {}, 200
        # return jsonify({"result": self.result}), 200

    def run(self, host='0.0.0.0', port=8080, debug=True):
        self.app.run(host=host, port=port, debug=debug)
