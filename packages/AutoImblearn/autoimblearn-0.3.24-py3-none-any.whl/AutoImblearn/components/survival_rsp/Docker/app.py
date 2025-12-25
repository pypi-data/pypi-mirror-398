"""
Survival resampler API using BaseTransformerAPI.

Supports resampling methods that preserve survival data structure:
- rus: Random Under Sampling (preserves censoring info via sample indices)
- ros: Random Over Sampling (treats time as feature)
- smote: SMOTE (treats time as feature, then reconstructs)
"""

import logging
import pandas as pd
import numpy as np
from AutoImblearn.components.api import BaseTransformerAPI
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler
from sksurv.util import Surv
from sksurv.datasets import get_x_y


# Hyperparameter search spaces
hyperparameter_search_space = {
    'rus': {
        'replacement': {
            'type': 'categorical',
            'choices': [True, False],
            'default': False
        }
    },
    'ros': {
        'sampling_strategy': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 1.0
        }
    },
    'smote': {
        'k_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 15,
            'default': 5
        },
        'sampling_strategy': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 1.0
        }
    }
}


class RunSurvivalResamplerAPI(BaseTransformerAPI):
    """Survival resampler API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.resampler = None
        self.result_X = None
        self.result_y = None
        self.param_space = hyperparameter_search_space
        self.feature_columns = None

    def get_hyperparameter_search_space(self):
        """Return hyperparameter search space for HPO integration."""
        return self.param_space

    def _get_default_params(self, model_name: str) -> dict:
        """Get default hyperparameters."""
        if model_name not in self.param_space:
            return {}
        defaults = {}
        for param_name, param_config in self.param_space[model_name].items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        return defaults

    def _validate_kwargs(self, model_name: str, kwargs: dict):
        """Validate hyperparameters."""
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
        """
        Fit and resample survival data.

        Handles survival-specific resampling:
        - RUS: Sample based on event, preserve survival times via indices
        - ROS/SMOTE: Treat time as feature, resample, then reconstruct
        """
        model_name = params.model
        event_col = getattr(params, "event_column", None) or getattr(params, "target_name", None) or "event"
        time_col = getattr(params, "time_column", None) or "time"

        # Get hyperparameters
        try:
            rsp_kwargs = params.params if hasattr(params, 'params') and params.params else {}
        except AttributeError:
            rsp_kwargs = {}

        # Validate and merge with defaults
        self._validate_kwargs(model_name, rsp_kwargs)
        final_params = {**self._get_default_params(model_name), **rsp_kwargs}

        # Get data (X_train and y_train)
        if 'X_train' in kwargs and 'y_train' in kwargs:
            X_train = kwargs.get('X_train')  # numpy array
            y_train = kwargs.get('y_train')  # numpy array or DataFrame
            # if hasattr(y_train, "rename"):
            #     y_train = y_train.rename(columns={event_col: "event", time_col: "time"})
        else:
            raise ValueError("Survival resampler requires X_train and y_train")

        # Load feature column names from dataset (for saving later)
        # In survival mode, y_train is a 2D array [status, survival_time]
        # We need to convert to structured array
        try:
            if isinstance(y_train, pd.DataFrame):
                y_train = Surv.from_dataframe("event", "time", y_train)
            if not isinstance(y_train, np.ndarray):
                raise Exception
        except Exception:
            raise ValueError("y_train must be 2D array [event, time].")

        # Create structured array for survival data
        # raise ValueError(f"type :{type(y_train)} \n shape: {y_train.shape} \n dtype: {y_train.dtype}")
        # y_struct = np.array(
        #     [(bool(row['event']), float(row['time'])) for row in y_train],
        #     dtype=[('event', '?'), ('time', '<f8')]
        # )
        y_struct = y_train

        logging.info(f"Resampling with {model_name} using params: {final_params}")

        # Create resampler
        if model_name == 'rus':
            resampler = RandomUnderSampler(random_state=42, **final_params)
        elif model_name == 'ros':
            resampler = RandomOverSampler(random_state=42, **final_params)
        elif model_name == 'smote':
            resampler = SMOTE(random_state=42, **final_params)
        else:
            raise ValueError(f"Resampler {model_name} not defined")

        # Perform survival-aware resampling
        if model_name == 'rus':
            # Undersampling: sample based on event only, preserve survival times
            X_resampled, _ = resampler.fit_resample(X_train, y_struct['event'])
            # Preserve survival times using sample indices
            y_resampled = y_struct[resampler.sample_indices_]

        elif model_name in ['ros', 'smote']:
            # Oversampling/SMOTE: treat time as a feature
            # Append survival time to features
            X_with_time = np.column_stack([X_train, y_struct['time']])

            # Resample based on event status
            X_resampled_with_time, status_resampled = resampler.fit_resample(
                X_with_time, y_struct['event']
            )

            # Separate features and time
            X_resampled = X_resampled_with_time[:, :-1]
            time_resampled = X_resampled_with_time[:, -1]

            # Reconstruct structured array
            y_resampled = np.array(
                [(bool(s), float(t)) for s, t in zip(status_resampled, time_resampled)],
                dtype=[('event', '?'), ('time', '<f8')]
            )

        # Convert to DataFrame/Series for compatibility
        self.result_X = pd.DataFrame(X_resampled)
        # For survival, we need to save y as well
        self.result_y = pd.DataFrame({
            'event': y_resampled['event'],
            'time': y_resampled['time']
        })
        self.result = self.result_X

        logging.info(f"Resampling complete: {X_train.shape} -> {X_resampled.shape}")

        return resampler

    def transform(self, *args, **kwargs):
        """Return the resampled X."""
        return self.result_X


if __name__ == '__main__':
    RunSurvivalResamplerAPI().run()
