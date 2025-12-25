
"""
Survival analysis API using BaseSurvivalEstimatorAPI.

Supports scikit-survival models:
- CPH: Cox Proportional Hazards
- RSF: Random Survival Forest
- SVM: Fast Survival SVM
- KSVM: Fast Kernel Survival SVM
- LASSO, L1, L2, CSA: Coxnet variants
"""

import logging

import pandas as pd
import numpy as np

from AutoImblearn.components.api import BaseSurvivalEstimatorAPI
from AutoImblearn.metrics import (
    get_metrics_for_pipeline,
    get_default_metric,
    is_metric_supported,
)
from sksurv.ensemble import RandomSurvivalForest
from sksurv.linear_model import CoxPHSurvivalAnalysis, CoxnetSurvivalAnalysis
from sksurv.svm import FastSurvivalSVM, FastKernelSurvivalSVM
from sksurv.metrics import (
    concordance_index_censored,
    concordance_index_ipcw,
    integrated_brier_score,
    brier_score,
    cumulative_dynamic_auc,
)
from sksurv.util import Surv


# Hyperparameter search spaces
hyperparameter_search_space = {
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
            'low': 0.8,
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
    'L1': {
        'l1_ratio': {
            'type': 'float',
            'low': 0.8,
            'high': 1.0,
            'default': 1.0
        }
    },
    'L2': {
        'l1_ratio': {
            'type': 'float',
            'low': 0.0,
            'high': 0.2,
            'default': 1e-16
        }
    },
    'CSA': {
        'l1_ratio': {
            'type': 'float',
            'low': 0.0,
            'high': 1.0,
            'default': 0.5
        }
    },
    'LRSF': {
        'max_depth': {
            'type': 'int',
            'low': 5,
            'high': 20,
            'default': 10
        },
        'n_estimators': {
            'type': 'int',
            'low': 10,
            'high': 100,
            'default': 20
        },
        'max_samples': {
            'type': 'float',
            'low': 0.2,
            'high': 0.8,
            'default': 0.4
        }
    }
}


class RunSkSurvivalAPI(BaseSurvivalEstimatorAPI):
    """Survival analysis API with standardized interface."""

    def __init__(self):
        super().__init__(__name__)
        self.model_name = None
        self.model_type = 'supervised'
        self.param_space = hyperparameter_search_space
        self.y_train_cache = None  # Cache for Uno's C-index calculation
        self.metric = None  # Selected evaluation metric

    def get_hyperparameter_search_space(self) -> dict:
        """Return hyperparameter search space for HPO integration."""
        model_name = self.params.get('model', 'CPH')
        return self.param_space.get(model_name, {})

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

    def fit(self, args, X_train, y_train, X_test=None, y_test=None):
        """Fit survival model."""
        model_name = args.model
        self.model_name = model_name
        pipeline_type = getattr(args, "pipeline_type", "survival_classification")

        # Normalize survival target columns if provided
        event_col = getattr(args, "event_column", None) or getattr(self.params, "event_column", None) or getattr(self.params, "target_name", None)
        time_col = getattr(args, "time_column", None) or getattr(self.params, "time_column", None)
        if event_col and time_col:
            if isinstance(y_train, pd.DataFrame):
                y_train = y_train.rename(columns={time_col: "time", event_col: "event"})
            if isinstance(y_test, pd.DataFrame):
                y_test = y_test.rename(columns={time_col: "time", event_col: "event"})

        if y_train.ndim == 2:
            y_train = np.array(
                list(zip(y_train[:, 0].astype(bool), y_train[:, 1].astype(float))),
                dtype=[('event', bool), ('time', float)]
            )

        # Normalize metric selection
        metric = getattr(args, "metric", None) or self.params.get("metric")
        if not metric:
            metric = get_default_metric(pipeline_type)
        # Allow model-aware validation: survival SVMs cannot do brier/IBS/time-dependent AUC
        family_metrics = {m["key"] for m in get_metrics_for_pipeline(pipeline_type)}
        if metric not in family_metrics:
            allowed = [m["key"] for m in get_metrics_for_pipeline(pipeline_type)]
            raise ValueError(f"Unsupported metric '{metric}' for pipeline '{pipeline_type}'. Allowed: {allowed}")
        if model_name in ("SVM", "KSVM") and metric in {"integrated_brier_score", "brier_score", "time_dependent_auc"}:
            raise ValueError(f"Metric '{metric}' not supported for model '{model_name}' (requires survival functions).")
        self.metric = metric

        # Normalize survival arrays for scikit-survival
        y_train = self._normalize_y(y_train)
        if y_test is not None:
            y_test = self._normalize_y(y_test)

        self.y_train_cache = y_train  # Cache for Uno's C-index or IPCW

        # Get hyperparameters
        try:
            model_kwargs = args.params if hasattr(args, 'params') and args.params else {}
        except AttributeError:
            model_kwargs = {}

        # Validate and merge with defaults
        self._validate_kwargs(model_name, model_kwargs)
        final_params = {**self._get_default_params(model_name), **model_kwargs}

        logging.info(f"Training {model_name} with params: {final_params}")

        # Create model
        if model_name == 'CPH':
            model = CoxPHSurvivalAnalysis(**final_params)
        elif model_name == 'RSF':
            model = RandomSurvivalForest(random_state=42, n_jobs=-1, **final_params)
        elif model_name == 'KSVM':
            model = FastKernelSurvivalSVM(random_state=42, **final_params)
        elif model_name == 'SVM':
            model = FastSurvivalSVM(random_state=42, **final_params)
        elif model_name == 'LASSO':
            model = CoxnetSurvivalAnalysis(l1_ratio=1, **final_params)
        elif model_name == 'L1':
            model = CoxnetSurvivalAnalysis(l1_ratio=1, **final_params)
        elif model_name == 'L2':
            model = CoxnetSurvivalAnalysis(l1_ratio=1e-16, **final_params)
        elif model_name == 'CSA':
            model = CoxnetSurvivalAnalysis(**final_params)
        elif model_name == 'LRSF':
            model = RandomSurvivalForest(random_state=42, **final_params)
        else:
            raise ValueError(f"Unknown model: {model_name}")

        # Fit model
        model.fit(X_train, y_train)
        logging.info("✓ Finished training")

        return model

    def predict(self, X_test, y_test):
        """Predict and evaluate."""

        y_test = self._normalize_y(y_test)
        metric = self.metric or get_default_metric("survival_classification")

        # Make predictions
        predictions = self.fitted_model.predict(X_test)

        # Metric dispatch
        if metric == "c_index":
            score = concordance_index_censored(
                y_test['event'],
                y_test['time'],
                predictions
            )[0]
            result = {'metric': metric, 'score': float(score), 'n_events': int(y_test['event'].sum())}

        elif metric == "c_index_ipcw":
            if self.y_train_cache is None:
                raise ValueError("c_index_ipcw requires cached training survival data")
            score = concordance_index_ipcw(self.y_train_cache, y_test, predictions)[0]
            result = {'metric': metric, 'score': float(score), 'n_events': int(y_test['event'].sum())}

        elif metric == "time_dependent_auc":
            times = self._time_grid(y_test)
            _, aucs = cumulative_dynamic_auc(self.y_train_cache, y_test, predictions, times)
            score = float(np.mean(aucs))
            result = {
                'metric': metric,
                'score': score,
                'times': [float(t) for t in times],
                'aucs': [float(a) for a in aucs],
            }

        elif metric == "integrated_brier_score":
            surv_funcs = self._predict_survival_functions(X_test)
            times = self._time_grid(y_test)
            ibs = integrated_brier_score(self.y_train_cache, y_test, surv_funcs, times)
            # Lower is better; negate so higher is better for selection
            score = float(-ibs)
            result = {
                'metric': metric,
                'score': score,
                'integrated_brier_score': float(ibs),
                'times': [float(t) for t in times],
            }

        elif metric == "brier_score":
            surv_funcs = self._predict_survival_functions(X_test)
            times = self._time_grid(y_test)
            _, brier_values = brier_score(self.y_train_cache, y_test, surv_funcs, times)
            mean_brier = float(np.mean(brier_values))
            score = float(-mean_brier)
            result = {
                'metric': metric,
                'score': score,
                'mean_brier_score': mean_brier,
                'times': [float(t) for t in times],
                'brier_by_time': [float(v) for v in brier_values],
            }

        else:
            raise ValueError(f"Unsupported metric '{metric}' for survival supervised models")

        logging.info(f"✓ {metric}: {result.get('score')}")
        return result

    def _normalize_y(self, y):
        """Normalize various survival label formats to sksurv structured array."""
        if y is None:
            return None

        if isinstance(y, np.ndarray) and y.dtype.names:
            names = {name.lower(): name for name in y.dtype.names}
            event_field = names.get('event') or names.get('status')
            time_field = names.get('time') or names.get('survival_in_days')
            if event_field and time_field:
                events = y[event_field].astype(bool)
                times = y[time_field].astype(float)
                return Surv.from_arrays(event=events, time=times)

        if isinstance(y, pd.DataFrame):
            cols = {c.lower(): c for c in y.columns}
            event_col = cols.get('event') or cols.get('status')
            time_col = cols.get('time') or cols.get('survival_in_days')
            if event_col and time_col:
                return Surv.from_arrays(
                    event=y[event_col].astype(bool).to_numpy(),
                    time=y[time_col].astype(float).to_numpy()
                )

        y_arr = np.asarray(y)
        if y_arr.ndim == 2 and y_arr.shape[1] >= 2:
            return Surv.from_arrays(event=y_arr[:, 0].astype(bool), time=y_arr[:, 1].astype(float))

        raise ValueError("y must contain event/status and time columns for survival analysis")

    def _time_grid(self, y_test):
        """Generate a reasonable time grid for time-dependent metrics."""
        times = np.quantile(y_test["time"], np.linspace(0.1, 0.9, 5))
        times = np.unique(times[times > 0])
        if times.size == 0:
            times = np.array([float(np.median(y_test["time"]))])
        return times

    def _predict_survival_functions(self, X):
        if not hasattr(self.fitted_model, "predict_survival_function"):
            raise ValueError(f"Model '{self.model_name}' does not support survival function prediction required for Brier-based metrics")
        surv_funcs = self.fitted_model.predict_survival_function(X)
        return list(surv_funcs)


if __name__ == '__main__':
    RunSkSurvivalAPI().run()
