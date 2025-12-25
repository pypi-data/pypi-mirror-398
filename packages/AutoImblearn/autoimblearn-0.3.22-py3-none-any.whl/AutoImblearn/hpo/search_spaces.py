"""
Hyperparameter Search Spaces for AutoImblearn Components

Defines Optuna-compatible search spaces for all imputers, resamplers,
classifiers, and other components in AutoImblearn.

Space Types:
- float: Continuous numerical parameters
- int: Discrete integer parameters
- categorical: Categorical choices
- float_log: Log-scale floating point (for learning rates, C values, etc.)
"""

# ============================================================================
# IMPUTERS
# ============================================================================

IMPUTER_SPACES = {
    'knn': {
        'n_neighbors': {
            'type': 'int',
            'low': 1,
            'high': 15,
            'default': 5
        },
        'weights': {
            'type': 'categorical',
            'choices': ['uniform', 'distance'],
            'default': 'uniform'
        }
    },
    'iter': {
        'max_iter': {
            'type': 'int',
            'low': 5,
            'high': 50,
            'default': 10
        },
        'tol': {
            'type': 'float_log',
            'low': 1e-5,
            'high': 1e-2,
            'default': 1e-3
        }
    },
    # mean, median have no hyperparameters
    'mean': {},
    'median': {},
}

# ============================================================================
# RESAMPLERS
# ============================================================================

RESAMPLER_SPACES = {
    # Over-sampling methods
    'smote': {
        'k_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 10,
            'default': 5
        }
    },
    'borderline_smote': {
        'k_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 10,
            'default': 5
        },
        'm_neighbors': {
            'type': 'int',
            'low': 5,
            'high': 15,
            'default': 10
        },
        'kind': {
            'type': 'categorical',
            'choices': ['borderline-1', 'borderline-2'],
            'default': 'borderline-1'
        }
    },
    'adasyn': {
        'n_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 10,
            'default': 5
        }
    },
    'kmeans_smote': {
        'k_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 10,
            'default': 5
        },
        'cluster_balance_threshold': {
            'type': 'float',
            'low': 0.0,
            'high': 1.0,
            'default': 0.1
        }
    },

    # Under-sampling methods
    'rus': {
        'replacement': {
            'type': 'categorical',
            'choices': [True, False],
            'default': False
        }
    },
    'nm': {  # NearMiss
        'version': {
            'type': 'int',
            'low': 1,
            'high': 3,
            'default': 1
        },
        'n_neighbors': {
            'type': 'int',
            'low': 3,
            'high': 10,
            'default': 3
        }
    },

    # Simple methods with no hyperparameters
    'ros': {},
    'cnn': {},
    'enn': {},
    'allknn': {},
    'smote_enn': {},
    'smote_tomek': {},
}

# ============================================================================
# CLASSIFIERS
# ============================================================================

CLASSIFIER_SPACES = {
    'lr': {
        'C': {
            'type': 'float_log',
            'low': 1e-4,
            'high': 1e4,
            'default': 1.0
        },
        'penalty': {
            'type': 'categorical',
            'choices': ['l1', 'l2', 'elasticnet', 'none'],
            'default': 'l2'
        },
        'solver': {
            'type': 'categorical',
            'choices': ['lbfgs', 'liblinear', 'saga', 'newton-cg', 'sag'],
            'default': 'lbfgs'
        },
        'max_iter': {
            'type': 'int',
            'low': 100,
            'high': 1000,
            'default': 500
        }
    },
    'svm': {
        'C': {
            'type': 'float_log',
            'low': 1e-2,
            'high': 1e3,
            'default': 1.0
        },
        'kernel': {
            'type': 'categorical',
            'choices': ['linear', 'poly', 'rbf', 'sigmoid'],
            'default': 'rbf'
        },
        'degree': {
            'type': 'int',
            'low': 2,
            'high': 5,
            'default': 3
        },
        'gamma': {
            'type': 'categorical',
            'choices': ['scale', 'auto'],
            'default': 'scale'
        }
    },
    'rf': {
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
            'default': 2
        },
        'min_samples_leaf': {
            'type': 'int',
            'low': 1,
            'high': 10,
            'default': 1
        },
        'max_features': {
            'type': 'categorical',
            'choices': ['sqrt', 'log2', None],
            'default': 'sqrt'
        }
    },
    'dt': {
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
            'default': 2
        },
        'min_samples_leaf': {
            'type': 'int',
            'low': 1,
            'high': 10,
            'default': 1
        },
        'criterion': {
            'type': 'categorical',
            'choices': ['gini', 'entropy'],
            'default': 'gini'
        }
    },
    'xgb': {
        'n_estimators': {
            'type': 'int',
            'low': 10,
            'high': 500,
            'default': 100
        },
        'max_depth': {
            'type': 'int',
            'low': 3,
            'high': 20,
            'default': 6
        },
        'learning_rate': {
            'type': 'float_log',
            'low': 1e-3,
            'high': 1.0,
            'default': 0.1
        },
        'subsample': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 0.8
        },
        'colsample_bytree': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 0.8
        },
        'gamma': {
            'type': 'float',
            'low': 0.0,
            'high': 5.0,
            'default': 0.0
        },
        'reg_alpha': {
            'type': 'float',
            'low': 0.0,
            'high': 5.0,
            'default': 0.0
        },
        'reg_lambda': {
            'type': 'float',
            'low': 0.0,
            'high': 5.0,
            'default': 1.0
        }
    },
    'mlp': {
        'hidden_layer_sizes': {
            'type': 'categorical',
            'choices': [(50,), (100,), (100, 50), (100, 100), (200,), (200, 100)],
            'default': (100,)
        },
        'activation': {
            'type': 'categorical',
            'choices': ['relu', 'tanh', 'logistic'],
            'default': 'relu'
        },
        'solver': {
            'type': 'categorical',
            'choices': ['adam', 'sgd', 'lbfgs'],
            'default': 'adam'
        },
        'alpha': {
            'type': 'float_log',
            'low': 1e-5,
            'high': 1.0,
            'default': 1e-4
        },
        'learning_rate': {
            'type': 'categorical',
            'choices': ['constant', 'invscaling', 'adaptive'],
            'default': 'constant'
        },
        'max_iter': {
            'type': 'int',
            'low': 200,
            'high': 2000,
            'default': 1000
        }
    },
    'ada': {
        'n_estimators': {
            'type': 'int',
            'low': 10,
            'high': 500,
            'default': 50
        },
        'learning_rate': {
            'type': 'float_log',
            'low': 1e-2,
            'high': 2.0,
            'default': 1.0
        },
        'algorithm': {
            'type': 'categorical',
            'choices': ['SAMME', 'SAMME.R'],
            'default': 'SAMME.R'
        }
    },
    'gb': {
        'n_estimators': {
            'type': 'int',
            'low': 10,
            'high': 500,
            'default': 100
        },
        'learning_rate': {
            'type': 'float_log',
            'low': 1e-3,
            'high': 1.0,
            'default': 0.1
        },
        'max_depth': {
            'type': 'int',
            'low': 3,
            'high': 20,
            'default': 3
        },
        'subsample': {
            'type': 'float',
            'low': 0.5,
            'high': 1.0,
            'default': 1.0
        }
    },
    'knn_clf': {
        'n_neighbors': {
            'type': 'int',
            'low': 1,
            'high': 30,
            'default': 5
        },
        'weights': {
            'type': 'categorical',
            'choices': ['uniform', 'distance'],
            'default': 'uniform'
        },
        'algorithm': {
            'type': 'categorical',
            'choices': ['auto', 'ball_tree', 'kd_tree', 'brute'],
            'default': 'auto'
        },
        'leaf_size': {
            'type': 'int',
            'low': 10,
            'high': 50,
            'default': 30
        }
    },
    'gnb': {},  # No hyperparameters
    'lda': {
        'solver': {
            'type': 'categorical',
            'choices': ['svd', 'lsqr', 'eigen'],
            'default': 'svd'
        }
    },
    'qda': {
        'reg_param': {
            'type': 'float',
            'low': 0.0,
            'high': 1.0,
            'default': 0.0
        }
    },
}

# ============================================================================
# CONSOLIDATED SEARCH SPACES
# ============================================================================

SEARCH_SPACES = {
    'imputers': IMPUTER_SPACES,
    'resamplers': RESAMPLER_SPACES,
    'classifiers': CLASSIFIER_SPACES,
}


def get_search_space(component_type, component_name):
    """
    Get the hyperparameter search space for a specific component.

    Args:
        component_type: Type of component ('imputers', 'resamplers', 'classifiers')
        component_name: Name of the component (e.g., 'lr', 'smote')

    Returns:
        dict: Search space definition, or empty dict if no hyperparameters

    Example:
        >>> get_search_space('classifiers', 'lr')
        {'C': {'type': 'float_log', 'low': 1e-4, 'high': 1e4, ...}, ...}
    """
    if component_type not in SEARCH_SPACES:
        return {}

    component_spaces = SEARCH_SPACES[component_type]
    return component_spaces.get(component_name, {})


def has_hyperparameters(component_type, component_name):
    """
    Check if a component has tunable hyperparameters.

    Args:
        component_type: Type of component
        component_name: Name of the component

    Returns:
        bool: True if component has hyperparameters to tune
    """
    space = get_search_space(component_type, component_name)
    return len(space) > 0
