from AutoImblearn.components.api import BaseTransformerAPI
from imblearn.over_sampling import SMOTE, RandomOverSampler, ADASYN, BorderlineSMOTE
from imblearn.under_sampling import RandomUnderSampler, TomekLinks, EditedNearestNeighbours
from imblearn.combine import SMOTEENN, SMOTETomek
import numpy as np
import pandas as pd
import logging


rsps = {
    'rus': RandomUnderSampler(random_state=42),
    'ros': RandomOverSampler(random_state=42),
    'smote': SMOTE(random_state=42),
    'adasyn': ADASYN(random_state=42),
    'borderline_smote': BorderlineSMOTE(random_state=42),
    'tomek': TomekLinks(),
    'enn': EditedNearestNeighbours(),
    'smoteenn': SMOTEENN(random_state=42),
    'smotetomek': SMOTETomek(random_state=42),
}


class RunImblearnSamplerAPI(BaseTransformerAPI):
    def __init__(self):
        self.resampler = None  # Store the resampler instance
        self.result_X = None  # Store resampled X
        self.result_y = None  # Store resampled y
        super().__init__(__name__)

        # Define hyperparameter search space
        self.param_space = {
            "rus": {
                "replacement": {
                    "type": "categorical",
                    "choices": [True, False],
                    "default": False
                }
            },
            "ros": {
                "sampling_strategy": {
                    "type": "float",
                    "min": 0.5,
                    "max": 1.0,
                    "default": 1.0
                }
            },
            "smote": {
                "k_neighbors": {
                    "type": "int", "min": 3, "max": 15, "default": 5
                },
                "sampling_strategy": {
                    "type": "float",
                    "min": 0.5,
                    "max": 1.0,
                    "default": 1.0
                }
            },
            "adasyn": {
                "n_neighbors": {
                    "type": "int", "min": 3, "max": 15, "default": 5
                },
                "sampling_strategy": {
                    "type": "float",
                    "min": 0.5,
                    "max": 1.0,
                    "default": 1.0
                }
            },
            "borderline_smote": {
                "k_neighbors": {
                    "type": "int", "min": 3, "max": 15, "default": 5
                },
                "m_neighbors": {
                    "type": "int", "min": 3, "max": 15, "default": 10
                },
                "sampling_strategy": {
                    "type": "float",
                    "min": 0.5,
                    "max": 1.0,
                    "default": 1.0
                }
            },
            "tomek": {},
            "enn": {
                "n_neighbors": {
                    "type": "int", "min": 1, "max": 10, "default": 3
                }
            },
            "smoteenn": {},
            "smotetomek": {},
        }

    def get_hyperparameter_search_space(self):
        return self.param_space

    def _validate_kwargs(self, model_name: str, kwargs: dict):
        """Validate that provided hyperparameters are allowed for this resampler."""
        if model_name not in self.param_space:
            return
        allowed = set(self.param_space[model_name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{model_name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )

    def _get_default_params(self, model_name: str) -> dict:
        """Get default hyperparameters for a resampler."""
        if model_name not in self.param_space:
            return {}

        defaults = {}
        for param_name, param_config in self.param_space[model_name].items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        return defaults

    def fit(self, params, *args, **kwargs):
        """Fit and resample the data"""
        model_name = params.model

        # Get hyperparameters from params (if provided)
        try:
            rsp_kwargs = params.resampler_kwargs if hasattr(params, 'resampler_kwargs') and params.resampler_kwargs else {}
        except AttributeError:
            rsp_kwargs = {}

        # Validate hyperparameters
        self._validate_kwargs(model_name, rsp_kwargs)

        # Merge with defaults
        final_params = {**self._get_default_params(model_name), **rsp_kwargs}

        if 'data' in kwargs:
            # data is X with y as the last column (from save_data_2_volume)
            full_data = kwargs.get('data')
            # Separate X and y
            X = full_data.iloc[:, :-1]  # All columns except last
            y = full_data.iloc[:, -1]   # Last column is y
        elif 'X_train' in kwargs and 'y_train' in kwargs:
            # New format: separate X_train and y_train
            X = kwargs.get('X_train')
            y = kwargs.get('y_train')
        else:
            raise ValueError("No data passed in (expected 'data' or 'X_train'+'y_train')")

        # Instantiate resampler with hyperparameters
        if model_name == 'rus':
            resampler = RandomUnderSampler(random_state=42, **final_params)
        elif model_name == 'ros':
            resampler = RandomOverSampler(random_state=42, **final_params)
        elif model_name == 'smote':
            resampler = SMOTE(random_state=42, **final_params)
        elif model_name == 'adasyn':
            resampler = ADASYN(random_state=42, **final_params)
        elif model_name == 'borderline_smote':
            resampler = BorderlineSMOTE(random_state=42, **final_params)
        elif model_name == 'tomek':
            resampler = TomekLinks(**final_params)
        elif model_name == 'enn':
            resampler = EditedNearestNeighbours(**final_params)
        elif model_name == 'smoteenn':
            resampler = SMOTEENN(random_state=42, **final_params)
        elif model_name == 'smotetomek':
            resampler = SMOTETomek(random_state=42, **final_params)
        else:
            # Fallback to old hardcoded dict
            if model_name in rsps:
                resampler = rsps[model_name]
            else:
                raise ValueError(f"Resampler {model_name} not defined")

        logging.info(f"Resampling with {model_name} using params: {final_params}")

        # Perform resampling
        X_resampled, y_resampled = resampler.fit_resample(X, y)

        # Convert back to DataFrame/Series
        if not isinstance(X_resampled, pd.DataFrame):
            X_resampled = pd.DataFrame(X_resampled, columns=X.columns)

        if not isinstance(y_resampled, pd.Series):
            y_resampled = pd.Series(y_resampled, name=y.name if hasattr(y, 'name') else 'target')

        self.result_X = X_resampled
        self.result_y = y_resampled

        # Store in self.result for BaseModelAPI compatibility
        self.result = self.result_X

        logging.info(f"Resampling complete: {X.shape} -> {X_resampled.shape}")

        # RETURN the fitted resampler (sklearn pattern!)
        # Base class will assign it to self.fitted_model and save to disk
        return resampler

    def transform(self, *args, **kwargs):
        """Return the resampled X (for compatibility)"""
        return self.result_X


RunImblearnSamplerAPI().run()
