# print(__package__)

# if __name__ == "__main__":
#     import os
#     import sys
#     current_path = os.path.dirname(os.path.abspath(__file__))
#     parent_path = os.path.dirname(os.path.dirname(current_path))  # Adjust based on actual layout
#     sys.path.insert(0, parent_path)
#
#     # Optionally set package name for relative imports to work
#     __package__ = "AutoImblearn.api"

import logging
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOSMOTE_DIR = os.path.join(CURRENT_DIR, "autosmote")
if AUTOSMOTE_DIR not in sys.path:
    sys.path.insert(0, AUTOSMOTE_DIR)

from classifiers import get_clf, name2f
from rl.training import train

from AutoImblearn.components.api import BaseEstimatorAPI

import numpy as np


class RunAutosmoteAPI(BaseEstimatorAPI):
    def get_hyperparameter_search_space(self):
        return {
            "seed": {
                "type": "int",
                "min": 0,
                "max": 10000,
                "default": 1
            },
            "device": {
                "type": "categorical",
                "choices": ["cpu", "cuda:0", "cuda:1"],
                "default": "cuda:0"
            },
            "cuda": {
                "type": "categorical",
                "choices": ["0", "1"],
                "default": "0"
            },
            "xpid": {
                "type": "categorical",
                "choices": ["AutoSMOTE"],
                "default": "AutoSMOTE"
            },
            "undersample_ratio": {
                "type": "int",
                "min": 10,
                "max": 300,
                "default": 100
            },
            "num_instance_specific_actions": {
                "type": "int",
                "min": 1,
                "max": 50,
                "default": 10
            },
            "num_max_neighbors": {
                "type": "int",
                "min": 5,
                "max": 100,
                "default": 30
            },
            "cross_instance_scale": {
                "type": "int",
                "min": 1,
                "max": 10,
                "default": 4
            },
            "num_actors": {
                "type": "int",
                "min": 1,
                "max": 100,
                "default": 40
            },
            "total_steps": {
                "type": "int",
                "min": 100,
                "max": 50000,
                "default": 1000
            },
            "batch_size": {
                "type": "int",
                "min": 2,
                "max": 64,
                "default": 8
            },
            "cross_instance_unroll_length": {
                "type": "int",
                "min": 1,
                "max": 20,
                "default": 2
            },
            "instance_specific_unroll_length": {
                "type": "int",
                "min": 50,
                "max": 1000,
                "default": 300
            },
            "low_level_unroll_length": {
                "type": "int",
                "min": 50,
                "max": 1000,
                "default": 300
            },
            "num_buffers": {
                "type": "int",
                "min": 5,
                "max": 100,
                "default": 20
            },
            "entropy_cost": {
                "type": "float",
                "min": 0.0001,
                "max": 0.01,
                "default": 0.0006
            },
            "baseline_cost": {
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.5
            },
            "discounting": {
                "type": "float",
                "min": 0.9,
                "max": 1.0,
                "default": 1.0
            },
            "learning_rate": {
                "type": "float",
                "min": 1e-5,
                "max": 0.1,
                "default": 0.005,
                "log_scale": True
            },
            "grad_norm_clipping": {
                "type": "float",
                "min": 1.0,
                "max": 100.0,
                "default": 40.0
            },
            "clf": {
                "type": "categorical",
                "choices": list(name2f.keys()),
                "default": "svm"
            },
        }


    def fit(self, args, X_train, y_train, X_test, y_test):
        params = self.dict_to_namespace()
        params.metric = args.metric

        size = X_train.shape[0]
        indices = np.arange(size)
        np.random.shuffle(indices)

        val_idx = indices[:int(size * args.val_ratio)]
        train_idx = indices[int(size * args.val_ratio):]

        train_X, val_X = X_train[train_idx], X_train[val_idx]
        train_y, val_y = y_train[train_idx], y_train[val_idx]

        logging.info("finished parameter setting")

        params.ratio_map = [0.0, 0.25, 0.5, 0.75, 1.0]
        clf = get_clf(params.clf)
        return train(params, train_X, train_y, val_X, val_y, X_test, y_test, clf)

    def predict(self, X):
        return self.result

    def predict_proba(self, X):
        raise NotImplementedError("predict_proba is not supported for AutoSMOTE.")
