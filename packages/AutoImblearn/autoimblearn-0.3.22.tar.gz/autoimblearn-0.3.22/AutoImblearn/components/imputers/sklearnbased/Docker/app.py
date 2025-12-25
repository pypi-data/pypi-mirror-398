import logging
import inspect

from AutoImblearn.components.api import BaseTransformerAPI
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.impute import KNNImputer
import numpy as np
import pandas as pd


def safe_factory(cls, fixed):
    sig = inspect.signature(cls.__init__)
    allowed = set(sig.parameters) - {"self"}
    def _build(**kw):
        merged = {**fixed, **kw}
        return cls(**{k: v for k, v in merged.items() if k in allowed})
    return _build

imps = {
    "ii": lambda **kw: IterativeImputer(**{**{"max_iter": 10}, **kw}),
    "knn": lambda **kw: KNNImputer(**{**{"weights": 'distance', "n_neighbors": 1}, **kw}),
}

class RunSklearnImputerAPI(BaseTransformerAPI):
    def __init__(self):
        super().__init__(__name__)
        self.result = None

        # Define hyperparameter search space
        self.param_space = {
            "knn": {
                "n_neighbors": {
                    "type": "int",
                    "min": 1,
                    "max": 15,
                    "default": 5
                },
                "weights": {
                    "type": "categorical",
                    "choices": ["uniform", "distance"],
                    "default": "uniform"
                }
            },
            "ii": {
                "max_iter": {
                    "type": "int",
                    "min": 5,
                    "max": 50,
                    "default": 10
                },
                "tol": {
                    "type": "float",
                    "min": 1e-5,
                    "max": 1e-2,
                    "default": 1e-3,
                    "log_scale": True
                }
            }
        }

    def get_hyperparameter_search_space(self):
        return self.param_space

    def _validate_kwargs(self, model_name: str, kwargs: dict):
        """Validate that provided hyperparameters are allowed for this imputer."""
        if model_name not in self.param_space:
            return
        allowed = set(self.param_space[model_name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{model_name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )

    def fit(self, params, *args, **kwargs):
        model = params.model
        imputer_kwargs = params.imputer_kwargs if hasattr(params, 'imputer_kwargs') and params.imputer_kwargs else {}
        categorical_columns = params.categorical_columns if hasattr(params, 'categorical_columns') else None

        # Validate hyperparameters
        self._validate_kwargs(model, imputer_kwargs)

        # Handle both data formats: full dataset (string) or just X_train
        if 'data' in kwargs:
            # Old format: full dataset as DataFrame
            data = kwargs.get('data')
            X_train = data
        elif 'X_train' in kwargs:
            # New format: X_train only (no y needed - imputation is unsupervised)
            X_train = kwargs.get('X_train')
        else:
            raise ValueError("No data passed in (expected 'data' or 'X_train')")

        # Fit the imputer on training data and transform it
        factory = imps[model]
        imputer = factory(**imputer_kwargs)
        logging.info(f"Imputing with {model} using params: {imputer_kwargs}")
        X_train_imputed = imputer.fit_transform(X_train)

        # Store column info
        if isinstance(X_train, pd.DataFrame):
            self.columns = X_train.columns
        else:
            # X_train is numpy array, create generic column names
            self.columns = [f"feature_{i}" for i in range(X_train_imputed.shape[1])]

        # Store transformed training data
        self.result = pd.DataFrame(X_train_imputed, columns=self.columns)

        logging.info("finished training (fit_transform on X_train)")

        # RETURN the fitted model (sklearn pattern!)
        # Base class will assign it to self.fitted_model and save to disk
        return imputer

    def transform(self, *args, **kwargs):
        # If data is provided, transform it; otherwise return cached result
        if 'data' in kwargs:
            data = kwargs.get('data')

            # Base class handles loading from disk if needed
            # We just use self.fitted_model directly (sklearn pattern!)
            imp_out = self.fitted_model.transform(data)
            return pd.DataFrame(imp_out, columns=self.columns)
        else:
            # Fallback to cached result for backward compatibility
            return self.result

RunSklearnImputerAPI().run()