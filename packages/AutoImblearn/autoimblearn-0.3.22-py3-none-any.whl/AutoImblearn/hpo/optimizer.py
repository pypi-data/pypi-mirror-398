"""
Optuna-based Hyperparameter Optimization for AutoImblearn

Provides sophisticated Bayesian optimization to find optimal hyperparameters
for pipelines and individual components.
"""

import logging
from typing import Dict, Any, Optional, Callable, List, Tuple
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from .search_spaces import get_search_space, has_hyperparameters


class ComponentOptimizer:
    """
    Optimize hyperparameters for a single component (imputer, resampler, or classifier).

    Uses Optuna's Tree-structured Parzen Estimator (TPE) for Bayesian optimization
    with median pruning for early stopping of unpromising trials.

    Example:
        >>> optimizer = ComponentOptimizer(
        ...     component_type='classifiers',
        ...     component_name='lr',
        ...     objective_func=lambda params: evaluate_lr(params)
        ... )
        >>> best_params, best_score = optimizer.optimize(n_trials=50)
    """

    def __init__(
        self,
        component_type: str,
        component_name: str,
        objective_func: Callable[[Dict[str, Any]], float],
        direction: str = 'maximize',
        study_name: Optional[str] = None,
        storage: Optional[str] = None,
    ):
        """
        Initialize component optimizer.

        Args:
            component_type: Type of component ('imputers', 'resamplers', 'classifiers')
            component_name: Name of component (e.g., 'lr', 'smote')
            objective_func: Function that takes hyperparameters and returns score
            direction: 'maximize' or 'minimize' the objective
            study_name: Optional name for persistent study
            storage: Optional storage URL for persistent study (e.g., 'sqlite:///optuna.db')
        """
        self.component_type = component_type
        self.component_name = component_name
        self.objective_func = objective_func
        self.direction = direction
        self.study_name = study_name or f"{component_type}_{component_name}_study"
        self.storage = storage

        # Get search space
        self.search_space = get_search_space(component_type, component_name)

        if not self.search_space:
            logging.warning(
                f"No hyperparameters defined for {component_type}/{component_name}. "
                f"Using default configuration."
            )

        # Create Optuna study
        self.study = optuna.create_study(
            study_name=self.study_name,
            storage=self.storage,
            direction=self.direction,
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=3),
            load_if_exists=True
        )

    def _suggest_hyperparameters(self, trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for a trial based on search space.

        Args:
            trial: Optuna trial object

        Returns:
            dict: Suggested hyperparameters
        """
        params = {}

        for param_name, param_config in self.search_space.items():
            param_type = param_config['type']

            if param_type == 'int':
                params[param_name] = trial.suggest_int(
                    param_name,
                    param_config['low'],
                    param_config['high']
                )
            elif param_type == 'float':
                params[param_name] = trial.suggest_float(
                    param_name,
                    param_config['low'],
                    param_config['high']
                )
            elif param_type == 'float_log':
                params[param_name] = trial.suggest_float(
                    param_name,
                    param_config['low'],
                    param_config['high'],
                    log=True
                )
            elif param_type == 'categorical':
                params[param_name] = trial.suggest_categorical(
                    param_name,
                    param_config['choices']
                )
            else:
                logging.warning(f"Unknown parameter type: {param_type} for {param_name}")

        return params

    def _objective(self, trial: optuna.Trial) -> float:
        """
        Objective function for Optuna trial.

        Args:
            trial: Optuna trial object

        Returns:
            float: Objective value (score)
        """
        # Get suggested hyperparameters
        params = self._suggest_hyperparameters(trial)

        # Evaluate with objective function
        try:
            score = self.objective_func(params)
            return score
        except Exception as e:
            logging.error(f"Trial {trial.number} failed: {e}")
            # Return worst possible score for failed trials
            return float('-inf') if self.direction == 'maximize' else float('inf')

    def optimize(
        self,
        n_trials: int = 50,
        timeout: Optional[int] = None,
        show_progress_bar: bool = True
    ) -> Tuple[Dict[str, Any], float]:
        """
        Run hyperparameter optimization.

        Args:
            n_trials: Number of trials to run
            timeout: Maximum time in seconds (optional)
            show_progress_bar: Whether to show progress bar

        Returns:
            tuple: (best_params, best_score)
        """
        if not self.search_space:
            # No hyperparameters to optimize, return empty dict
            logging.info(f"No hyperparameters to optimize for {self.component_name}")
            return {}, None

        logging.info(
            f"Starting HPO for {self.component_type}/{self.component_name} "
            f"with {n_trials} trials"
        )

        # Run optimization
        self.study.optimize(
            self._objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=show_progress_bar,
            n_jobs=1  # Sequential for now; can enable parallel later
        )

        # Get best results
        best_params = self.study.best_params
        best_score = self.study.best_value

        logging.info(
            f"HPO complete for {self.component_name}: "
            f"best_score={best_score:.4f}, best_params={best_params}"
        )

        return best_params, best_score

    def get_best_params(self) -> Dict[str, Any]:
        """Get best parameters from completed study."""
        return self.study.best_params if self.study.best_trial else {}

    def get_best_score(self) -> float:
        """Get best score from completed study."""
        return self.study.best_value if self.study.best_trial else None


class PipelineOptimizer:
    """
    Optimize hyperparameters for an entire pipeline.

    Optimizes all components in a pipeline (imputer, resampler, classifier)
    jointly to find the best overall configuration.

    Example:
        >>> optimizer = PipelineOptimizer(
        ...     pipeline=['median', 'smote', 'lr'],
        ...     run_pipe=run_pipe_instance
        ... )
        >>> best_config, best_score = optimizer.optimize(n_trials=100)
    """

    def __init__(
        self,
        pipeline: List[str],
        run_pipe: Any,  # RunPipe instance
        direction: str = 'maximize',
        study_name: Optional[str] = None,
        storage: Optional[str] = None,
    ):
        """
        Initialize pipeline optimizer.

        Args:
            pipeline: Pipeline specification [imputer, resampler, classifier]
            run_pipe: RunPipe instance with loaded data
            direction: 'maximize' or 'minimize' the objective
            study_name: Optional name for persistent study
            storage: Optional storage URL for persistent study
        """
        self.pipeline = pipeline
        self.run_pipe = run_pipe
        self.direction = direction
        self.study_name = study_name or f"pipeline_{'_'.join(pipeline)}_study"
        self.storage = storage

        # Determine pipeline structure
        if len(pipeline) == 3:
            self.imputer, self.resampler, self.classifier = pipeline
            self.component_types = ['imputers', 'resamplers', 'classifiers']
            self.component_names = [self.imputer, self.resampler, self.classifier]
        elif len(pipeline) == 2:
            self.imputer, self.hybrid = pipeline
            self.component_types = ['imputers', 'hybrid_imbalanced_classifiers']
            self.component_names = [self.imputer, self.hybrid]
        elif len(pipeline) == 1:
            # AutoML - no hyperparameters to optimize (they optimize internally)
            self.component_types = []
            self.component_names = []
        else:
            raise ValueError(f"Invalid pipeline length: {len(pipeline)}")

        # Get search spaces for all components
        self.search_spaces = {}
        for comp_type, comp_name in zip(self.component_types, self.component_names):
            space = get_search_space(comp_type, comp_name)
            if space:
                self.search_spaces[comp_name] = {
                    'type': comp_type,
                    'space': space
                }

        if not self.search_spaces:
            logging.warning(
                f"No hyperparameters to optimize in pipeline {pipeline}. "
                f"Using default configurations."
            )

        # Create Optuna study
        self.study = optuna.create_study(
            study_name=self.study_name,
            storage=self.storage,
            direction=self.direction,
            sampler=TPESampler(seed=42, multivariate=True),  # Multivariate for joint optimization
            pruner=MedianPruner(n_startup_trials=10, n_warmup_steps=5),
            load_if_exists=True
        )

    def _suggest_pipeline_hyperparameters(self, trial: optuna.Trial) -> Dict[str, Dict[str, Any]]:
        """
        Suggest hyperparameters for all components in the pipeline.

        Args:
            trial: Optuna trial object

        Returns:
            dict: Hyperparameters for each component
                  e.g., {'lr': {'C': 0.1, 'penalty': 'l2'}, 'smote': {'k_neighbors': 5}}
        """
        all_params = {}

        for comp_name, comp_info in self.search_spaces.items():
            comp_params = {}
            space = comp_info['space']

            for param_name, param_config in space.items():
                # Prefix parameter name with component name to avoid conflicts
                trial_param_name = f"{comp_name}_{param_name}"
                param_type = param_config['type']

                if param_type == 'int':
                    value = trial.suggest_int(
                        trial_param_name,
                        param_config['low'],
                        param_config['high']
                    )
                elif param_type == 'float':
                    value = trial.suggest_float(
                        trial_param_name,
                        param_config['low'],
                        param_config['high']
                    )
                elif param_type == 'float_log':
                    value = trial.suggest_float(
                        trial_param_name,
                        param_config['low'],
                        param_config['high'],
                        log=True
                    )
                elif param_type == 'categorical':
                    value = trial.suggest_categorical(
                        trial_param_name,
                        param_config['choices']
                    )
                else:
                    logging.warning(f"Unknown parameter type: {param_type} for {param_name}")
                    continue

                comp_params[param_name] = value

            if comp_params:
                all_params[comp_name] = comp_params

        return all_params

    def _objective(self, trial: optuna.Trial) -> float:
        """
        Objective function for pipeline optimization.

        Args:
            trial: Optuna trial object

        Returns:
            float: Pipeline score
        """
        # Get suggested hyperparameters for all components
        pipeline_params = self._suggest_pipeline_hyperparameters(trial)

        # TODO: Pass hyperparameters to run_pipe.fit()
        # For now, just evaluate with default parameters
        try:
            score = self.run_pipe.fit(self.pipeline)
            return score
        except Exception as e:
            logging.error(f"Trial {trial.number} failed: {e}")
            return float('-inf') if self.direction == 'maximize' else float('inf')

    def optimize(
        self,
        n_trials: int = 100,
        timeout: Optional[int] = None,
        show_progress_bar: bool = True
    ) -> Tuple[Dict[str, Dict[str, Any]], float]:
        """
        Run hyperparameter optimization for the entire pipeline.

        Args:
            n_trials: Number of trials to run
            timeout: Maximum time in seconds (optional)
            show_progress_bar: Whether to show progress bar

        Returns:
            tuple: (best_params_per_component, best_score)
        """
        if not self.search_spaces:
            logging.info(f"No hyperparameters to optimize for pipeline {self.pipeline}")
            return {}, None

        logging.info(
            f"Starting pipeline HPO for {self.pipeline} with {n_trials} trials"
        )

        # Run optimization
        self.study.optimize(
            self._objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=show_progress_bar,
            n_jobs=1
        )

        # Parse best parameters back into component-specific dicts
        best_params_flat = self.study.best_params
        best_params = {}

        for comp_name in self.search_spaces.keys():
            comp_params = {}
            prefix = f"{comp_name}_"
            for key, value in best_params_flat.items():
                if key.startswith(prefix):
                    param_name = key[len(prefix):]
                    comp_params[param_name] = value
            if comp_params:
                best_params[comp_name] = comp_params

        best_score = self.study.best_value

        logging.info(
            f"Pipeline HPO complete: best_score={best_score:.4f}, "
            f"best_params={best_params}"
        )

        return best_params, best_score

    def get_best_params(self) -> Dict[str, Dict[str, Any]]:
        """Get best parameters from completed study."""
        if not self.study.best_trial:
            return {}

        best_params_flat = self.study.best_params
        best_params = {}

        for comp_name in self.search_spaces.keys():
            comp_params = {}
            prefix = f"{comp_name}_"
            for key, value in best_params_flat.items():
                if key.startswith(prefix):
                    param_name = key[len(prefix):]
                    comp_params[param_name] = value
            if comp_params:
                best_params[comp_name] = comp_params

        return best_params

    def get_best_score(self) -> float:
        """Get best score from completed study."""
        return self.study.best_value if self.study.best_trial else None
