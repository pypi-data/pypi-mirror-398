"""
EXAMPLE: Refactored survival analysis API using BaseSurvivalEstimatorAPI.

This is an example showing how to convert the raw Flask app to use the
standardized base class pattern.

Benefits:
- Automatic data loading and validation
- Standardized /set, /train, /health, /hyperparameters endpoints
- Model persistence and loading
- Integration with HPO system
- Consistent error handling
"""

import logging
from AutoImblearn.components.api import BaseSurvivalEstimatorAPI

# Import survival models
from sksurv.ensemble import RandomSurvivalForest
from sksurv.linear_model import CoxPHSurvivalAnalysis, CoxnetSurvivalAnalysis
from sksurv.svm import FastSurvivalSVM, FastKernelSurvivalSVM
from sksurv.metrics import concordance_index_censored


# Define hyperparameter search spaces for survival models
SURVIVAL_HYPERPARAMETER_SPACES = {
    'CPH': {
        'alpha': {
            'type': 'float_log',
            'low': 1e-5,
            'high': 1.0,
            'default': 0.0001
        }
    },
    'RSF': {
        'n_estimators': {
            'type': 'int',
            'low': 10,
            'high': 500,
            'default': 100
        },
        'max_depth': {
            'type': 'int',
            'low': 3,
            'high': 30,
            'default': 10
        },
        'min_samples_split': {
            'type': 'int',
            'low': 2,
            'high': 20,
            'default': 6
        },
        'min_samples_leaf': {
            'type': 'int',
            'low': 1,
            'high': 10,
            'default': 3
        }
    },
    'SVM': {
        'alpha': {
            'type': 'float_log',
            'low': 1e-5,
            'high': 1.0,
            'default': 1.0
        }
    },
    'KSVM': {
        'kernel': {
            'type': 'categorical',
            'choices': ['linear', 'poly', 'rbf'],
            'default': 'poly'
        },
        'alpha': {
            'type': 'float_log',
            'low': 1e-5,
            'high': 1.0,
            'default': 1.0
        }
    },
    'LASSO': {
        'l1_ratio': {
            'type': 'float',
            'low': 0.0,
            'high': 1.0,
            'default': 1.0
        },
        'alpha_min_ratio': {
            'type': 'float',
            'low': 0.001,
            'high': 0.1,
            'default': 0.01
        }
    },
    'CSA': {
        'l1_ratio': {
            'type': 'float',
            'low': 0.0,
            'high': 1.0,
            'default': 0.5
        }
    }
}


class RunSkSurvivalAPI(BaseSurvivalEstimatorAPI):
    """
    Survival analysis model API using the standardized base class.

    Supports scikit-survival models:
    - CPH: Cox Proportional Hazards
    - RSF: Random Survival Forest
    - SVM: Fast Survival SVM
    - KSVM: Fast Kernel Survival SVM
    - LASSO: Coxnet with L1 regularization
    - CSA: Coxnet with elastic net
    """

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.model_type = 'supervised'  # All these are supervised models

    def get_hyperparameter_search_space(self) -> dict:
        """
        Return hyperparameter search space for this survival model.

        This enables integration with the HPO system!
        """
        model_name = self.params.get('model', 'CPH')
        return SURVIVAL_HYPERPARAMETER_SPACES.get(model_name, {})

    def _get_model(self, model_name, params=None):
        """
        Factory function to create survival models with hyperparameters.

        Args:
            model_name: Name of the model
            params: Dict of hyperparameters (or None for defaults)

        Returns:
            Instantiated model
        """
        params = params or {}

        models = {
            'CPH': lambda p: CoxPHSurvivalAnalysis(**p),
            'RSF': lambda p: RandomSurvivalForest(random_state=42, n_jobs=-1, **p),
            'KSVM': lambda p: FastKernelSurvivalSVM(random_state=42, **p),
            'SVM': lambda p: FastSurvivalSVM(random_state=42, **p),
            'LASSO': lambda p: CoxnetSurvivalAnalysis(l1_ratio=1, **p),
            'L1': lambda p: CoxnetSurvivalAnalysis(l1_ratio=1, **p),
            'L2': lambda p: CoxnetSurvivalAnalysis(l1_ratio=1e-16, **p),
            'CSA': lambda p: CoxnetSurvivalAnalysis(**p),
        }

        if model_name not in models:
            raise ValueError(f"Unknown model: {model_name}")

        return models[model_name](params)

    def _get_default_params(self, model_name: str) -> dict:
        """Get default hyperparameters for a model."""
        if model_name not in SURVIVAL_HYPERPARAMETER_SPACES:
            return {}

        defaults = {}
        for param_name, param_config in SURVIVAL_HYPERPARAMETER_SPACES[model_name].items():
            if 'default' in param_config:
                defaults[param_name] = param_config['default']
        return defaults

    def _validate_kwargs(self, model_name: str, kwargs: dict):
        """Validate that provided hyperparameters are allowed for this model."""
        if model_name not in SURVIVAL_HYPERPARAMETER_SPACES:
            return  # No validation for models without defined spaces

        allowed = set(SURVIVAL_HYPERPARAMETER_SPACES[model_name].keys())
        unknown = set(kwargs) - allowed
        if unknown:
            raise ValueError(
                f"Unsupported parameters for '{model_name}': {sorted(unknown)}. "
                f"Allowed: {sorted(allowed)}"
            )

    def fit(self, args, X_train, y_train, X_test=None, y_test=None):
        """
        Fit survival model on training data.

        Args:
            args: Arguments object with model name, params, etc.
            X_train: Training features (numpy array)
            y_train: Training survival data (structured array)
            X_test: Test features (optional)
            y_test: Test survival data (optional)

        Returns:
            Fitted model
        """
        model_name = args.model
        self.model_name = model_name

        # Get hyperparameters from args (if provided)
        try:
            model_kwargs = args.params if hasattr(args, 'params') and args.params else {}
        except AttributeError:
            model_kwargs = {}

        # Validate hyperparameters
        self._validate_kwargs(model_name, model_kwargs)

        # Merge with defaults
        final_params = {**self._get_default_params(model_name), **model_kwargs}

        # Create and fit model
        logging.info(f"Training {model_name} with params: {final_params}")
        model = self._get_model(model_name, final_params)
        model.fit(X_train, y_train)
        logging.info(f"✓ Finished training {model_name}")

        # RETURN the fitted model (sklearn pattern!)
        return model

    def predict(self, X_test, y_test):
        """
        Predict and evaluate survival model on test data.

        Args:
            X_test: Test features
            y_test: Test survival data (structured array)

        Returns:
            dict: Evaluation metrics (C-index, Uno's C-index if available)
        """
        # Base class ensures self.fitted_model is loaded - no checking needed!

        # Make predictions (risk scores)
        predictions = self.fitted_model.predict(X_test)

        # Calculate concordance index
        c_index = concordance_index_censored(
            y_test['Status'],
            y_test['Survival_in_days'],
            predictions
        )[0]

        result = {
            'c_index': float(c_index),
            'n_events': int(y_test['Status'].sum()),
            'n_samples': len(y_test)
        }

        logging.info(f"✓ Evaluation complete: C-index = {c_index:.4f}")

        return result


if __name__ == '__main__':
    # Run the API server
    api = RunSkSurvivalAPI()
    api.run(host='0.0.0.0', port=8080, debug=True)
