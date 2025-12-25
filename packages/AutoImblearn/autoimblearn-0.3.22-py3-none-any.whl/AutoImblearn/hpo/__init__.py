"""
Hyperparameter Optimization (HPO) Module

This module provides Optuna-based hyperparameter optimization for AutoImblearn,
enabling sophisticated Bayesian optimization to find optimal hyperparameters
for imputers, resamplers, and classifiers.

Key Features:
- Bayesian optimization with Optuna
- Pruning for early stopping of bad configurations
- Multi-objective optimization support
- Persistent study storage
- Parallel trial support
"""

from .optimizer import PipelineOptimizer, ComponentOptimizer
from .search_spaces import SEARCH_SPACES

__all__ = [
    'PipelineOptimizer',
    'ComponentOptimizer',
    'SEARCH_SPACES'
]
