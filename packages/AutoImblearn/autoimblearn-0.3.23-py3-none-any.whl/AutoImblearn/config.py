"""
Configuration and execution state management for AutoImblearn.

This module separates immutable configuration from mutable execution state,
replacing the problematic ArgsNamespace pattern.

Key improvements:
- Clear separation of concerns
- Type safety with Pydantic
- Immutable configuration (frozen dataclass)
- Serializable for reproducibility
- Backward compatible with ArgsNamespace
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, Dict, Any
from pathlib import Path
import json
import hashlib
from pydantic import BaseModel, Field, field_validator


class AutoMLConfig(BaseModel):
    """
    Immutable configuration for AutoImblearn training.

    This contains all user-specified settings that don't change during execution.
    Can be serialized to JSON for reproducibility.

    Example:
        >>> config = AutoMLConfig(
        ...     dataset="nhanes.csv",
        ...     target="Status",
        ...     metric="auroc"
        ... )
        >>> config_dict = config.model_dump()
        >>> restored = AutoMLConfig(**config_dict)
    """

    # ===== Dataset Configuration =====
    dataset: str = Field(
        default="nhanes.csv",
        description="Name of the dataset file"
    )
    target: str = Field(
        default="Status",
        description="Name of the prediction target column"
    )

    # ===== Preprocessing Configuration =====
    aggregation: Literal["categorical", "binary"] = Field(
        default="binary",
        description="How to aggregate features"
    )
    missing: Literal['median', 'mean', 'dropna', 'knn', 'ii', 'gain', 'MIRACLE', 'MIWAE'] = Field(
        default="median",
        description="Imputation strategy for missing values"
    )

    # ===== Cross-Validation Configuration =====
    n_splits: int = Field(
        default=10,
        ge=2,
        le=50,
        description="Number of folds for K-fold cross-validation"
    )

    # ===== Resampling Configuration =====
    infor_method: Literal["normal", "nothing"] = Field(
        default="normal",
        description="How to handle AUDM"
    )
    resampling: bool = Field(
        default=False,
        description="Whether to apply resampling"
    )
    resample_method: Literal["under", "over", "combined", "herding", "s2sl_mwmote", "MWMOTE", "smote"] = Field(
        default="under",
        description="Resampling strategy"
    )
    samratio: float = Field(
        default=0.4,
        ge=0.0,
        le=1.0,
        description="Target sample ratio for resampling"
    )

    # ===== Model Configuration =====
    T_model: Literal["SVM", "LSVM", "lr", "rf", "mlp", "s2sl", "s2sLR", "ensemble", "ada", "bst"] = Field(
        default="lr",
        description="Traditional model type"
    )
    repeat: int = Field(
        default=0,
        ge=0,
        description="Number of repetitions for training"
    )

    # ===== Feature Engineering =====
    feature_importance: Literal["NA", "lime", "shap"] = Field(
        default="NA",
        description="Feature importance method"
    )
    top_k: int = Field(
        default=-1,
        description="Number of top features to keep (-1 = all)"
    )

    # ===== Hyperparameter Tuning =====
    grid: bool = Field(
        default=False,
        description="Use GridSearchCV for hyperparameter tuning"
    )

    # ===== AutoML Search Configuration =====
    metric: str = Field(
        default="auroc",
        description="Evaluation metric for model selection"
    )
    train_ratio: float = Field(
        default=1.0,
        ge=0.1,
        le=1.0,
        description="Fraction of training data to use (for faster search)"
    )
    exhaustive: bool = Field(
        default=False,
        description="Use exhaustive search instead of greedy search"
    )

    # NEW: Search budget controls
    max_iterations: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of pipeline evaluations (None = no limit)"
    )
    time_budget_seconds: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum search time in seconds (None = no limit)"
    )
    early_stopping_patience: int = Field(
        default=10,
        ge=1,
        description="Stop if no improvement for N iterations"
    )

    # ===== Execution Control =====
    rerun: bool = Field(
        default=False,
        description="Re-run the best pipeline with 100% data"
    )

    # ===== Data Roots =====
    host_data_root: Optional[str] = Field(
        default=None,
        description="Host path to the data folder (bind-mounted into model containers)"
    )
    container_data_root: Optional[str] = Field(
        default=None,
        description="In-container path to the data folder for Celery/Django I/O"
    )

    # ===== Optional Path Override =====
    data_path: Optional[str] = Field(
        default=None,
        description="Deprecated alias for host_data_root; use host_data_root instead"
    )

    model_config = {"frozen": True}  # Make immutable

    def get_hash(self) -> str:
        """
        Get a unique hash for this configuration.

        Useful for:
        - Cache keys
        - Experiment tracking
        - Reproducibility

        Returns:
            SHA256 hash of configuration
        """
        # Sort dict keys for consistent hashing
        config_dict = self.model_dump()
        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def save(self, path: Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            path: Where to save the config
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'AutoMLConfig':
        """
        Load configuration from JSON file.

        Args:
            path: Path to config file

        Returns:
            AutoMLConfig instance
        """
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def to_args_namespace(self) -> 'ArgsNamespace':
        """
        Convert to legacy ArgsNamespace for backward compatibility.

        Returns:
            ArgsNamespace instance
        """
        from .processing.utils import ArgsNamespace

        base_host_root = self.host_data_root
        if base_host_root is None:
            raise ValueError("host_data_root is required to build ArgsNamespace")
        if self.container_data_root is None:
            raise ValueError("container_data_root is required to build ArgsNamespace")
        container_root = self.container_data_root

        return ArgsNamespace(
            dataset=self.dataset,
            target_name=self.target,
            T_model=self.T_model,
            repeat=self.repeat,
            aggregation=self.aggregation,
            missing=self.missing,
            n_splits=self.n_splits,
            infor_method=self.infor_method,
            resampling=self.resampling,
            resample_method=self.resample_method,
            samratio=self.samratio,
            feature_importance=self.feature_importance,
            grid=self.grid,
            top_k=self.top_k,
            train_ratio=self.train_ratio,
            metric=self.metric,
            rerun=self.rerun,
            exhaustive=self.exhaustive,
            host_data_root=base_host_root,
            container_data_root=container_root,
            path=base_host_root,
        )

    @classmethod
    def from_args_namespace(cls, args: 'ArgsNamespace') -> 'AutoMLConfig':
        """
        Create from legacy ArgsNamespace.

        Args:
            args: ArgsNamespace instance

        Returns:
            AutoMLConfig instance
        """
        host_root = getattr(args, "host_data_root", None)
        if host_root is None:
            raise ValueError("host_data_root is required on ArgsNamespace")
        container_root = getattr(args, "container_data_root", None)
        if container_root is None:
            raise ValueError("container_data_root is required on ArgsNamespace")
        target_val = getattr(args, "target_name", None) or "Status"
        return cls(
            dataset=args.dataset,
            target=target_val,
            T_model=args.T_model,
            repeat=args.repeat,
            aggregation=args.aggregation,
            missing=args.missing,
            n_splits=args.n_splits,
            infor_method=args.infor_method,
            resampling=args.resampling,
            resample_method=args.resample_method,
            samratio=args.samratio,
            feature_importance=args.feature_importance,
            grid=args.grid,
            top_k=args.top_k,
            train_ratio=args.train_ratio,
            metric=args.metric,
            rerun=args.rerun,
            exhaustive=args.exhaustive,
            host_data_root=host_root,
            container_data_root=container_root,
            data_path=host_root
        )


@dataclass
class ExecutionState:
    """
    Mutable execution state for AutoImblearn training.

    This contains runtime information that changes during execution:
    - File paths
    - Current results
    - Cache
    - Temporary data

    Separated from config for clarity and testability.
    """

    # Paths (computed from config)
    host_data_root: Path
    container_data_root: Path
    interim_folder: Path
    processed_folder: Path
    raw_folder: Path
    models_folder: Path

    # Current execution state
    current_pipeline: Optional[list] = None
    current_score: float = 0.0

    # Best results so far
    best_pipeline: Optional[list] = None
    best_score: float = 0.0

    # Search statistics
    evaluations_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    # Timing
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    # Results cache
    cached_results: Dict[str, float] = field(default_factory=dict)

    # Model storage
    trained_models: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: AutoMLConfig) -> 'ExecutionState':
        """
        Create execution state from configuration.

        Sets up all necessary folders and paths.

        Args:
            config: AutoML configuration

        Returns:
            ExecutionState instance
        """
        import os

        # Determine data folder
        if config.host_data_root:
            host_data_root = Path(config.host_data_root)
        elif config.data_path:
            host_data_root = Path(config.data_path)
        else:
            raise ValueError("host_data_root is required for ExecutionState")

        if config.container_data_root is None:
            raise ValueError("container_data_root is required for ExecutionState")
        container_data_root = Path(config.container_data_root)

        # Create all necessary folders
        interim_folder = container_data_root / "interim" / config.dataset
        processed_folder = container_data_root / "processed"
        raw_folder = container_data_root / "raw"
        models_folder = interim_folder / "saved_models"

        # Create directories
        for folder in [interim_folder, processed_folder, raw_folder, models_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        return cls(
            host_data_root=host_data_root,
            container_data_root=container_data_root,
            interim_folder=interim_folder,
            processed_folder=processed_folder,
            raw_folder=raw_folder,
            models_folder=models_folder
        )

    def get_model_path(self, model_name: str = "autoimblearn.pkl") -> Path:
        """Get path for saving/loading a model."""
        return self.models_folder / model_name

    def get_cache_path(self, metric: str, train_ratio: float, dataset: str) -> Path:
        """Get path for results cache file."""
        cache_file = f"{dataset}_saved_pipe_{metric}_{train_ratio}.json"
        return self.processed_folder / cache_file

    def update_best(self, pipeline: list, score: float) -> bool:
        """
        Update best pipeline if new score is better.

        Args:
            pipeline: Pipeline specification
            score: Achieved score

        Returns:
            True if best was updated
        """
        if score > self.best_score:
            self.best_pipeline = list(pipeline)
            self.best_score = score
            return True
        return False

    def record_evaluation(self, pipeline: list, score: float, from_cache: bool = False) -> None:
        """
        Record a pipeline evaluation.

        Args:
            pipeline: Pipeline that was evaluated
            score: Score achieved
            from_cache: Whether result was from cache
        """
        self.evaluations_count += 1
        self.current_pipeline = pipeline
        self.current_score = score

        if from_cache:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

        # Update cache
        cache_key = "_".join(pipeline)
        self.cached_results[cache_key] = score

    def get_elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds (None if not started)."""
        if self.start_time is None:
            return None

        end = self.end_time if self.end_time else __import__('time').time()
        return end - self.start_time

    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary with stats
        """
        return {
            'evaluations': self.evaluations_count,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / max(self.evaluations_count, 1),
            'best_score': self.best_score,
            'best_pipeline': self.best_pipeline,
            'elapsed_time': self.get_elapsed_time()
        }

    def save_state(self, path: Path) -> None:
        """
        Save execution state to file.

        Args:
            path: Where to save state
        """
        import pickle

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load_state(cls, path: Path) -> 'ExecutionState':
        """
        Load execution state from file.

        Args:
            path: Path to state file

        Returns:
            ExecutionState instance
        """
        import pickle

        with open(path, 'rb') as f:
            return pickle.load(f)


class AutoMLContext:
    """
    Combined configuration and execution state.

    This provides a clean interface for the entire AutoML execution,
    separating immutable config from mutable state.

    Example:
        >>> config = AutoMLConfig(dataset="nhanes.csv", metric="auroc")
        >>> context = AutoMLContext(config)
        >>> context.state.record_evaluation(["median", "smote", "lr"], 0.85)
        >>> print(context.state.get_stats())
    """

    def __init__(self, config: AutoMLConfig, state: Optional[ExecutionState] = None):
        """
        Initialize context.

        Args:
            config: Immutable configuration
            state: Execution state (created from config if None)
        """
        self.config = config
        self.state = state if state else ExecutionState.from_config(config)

    def save(self, base_path: Path) -> None:
        """
        Save both config and state.

        Args:
            base_path: Base directory for saving
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)

        self.config.save(base_path / "config.json")
        self.state.save_state(base_path / "state.pkl")

    @classmethod
    def load(cls, base_path: Path) -> 'AutoMLContext':
        """
        Load both config and state.

        Args:
            base_path: Base directory

        Returns:
            AutoMLContext instance
        """
        base_path = Path(base_path)

        config = AutoMLConfig.load(base_path / "config.json")
        state = ExecutionState.load_state(base_path / "state.pkl")

        return cls(config, state)

    def get_hash(self) -> str:
        """Get unique hash for this context."""
        return self.config.get_hash()

    def __repr__(self) -> str:
        return (
            f"AutoMLContext(\n"
            f"  dataset={self.config.dataset},\n"
            f"  metric={self.config.metric},\n"
            f"  best_score={self.state.best_score:.4f},\n"
            f"  evaluations={self.state.evaluations_count}\n"
            f")"
        )


# Backward compatibility helper
def create_config_from_kwargs(**kwargs) -> AutoMLConfig:
    """
    Create AutoMLConfig from keyword arguments.

    This is for backward compatibility with the old AutoImblearnTraining.__init__

    Args:
        **kwargs: Configuration parameters

    Returns:
        AutoMLConfig instance
    """
    return AutoMLConfig(**kwargs)
