"""
Pipeline abstraction for AutoImblearn.

This module provides a flexible, extensible pipeline abstraction that supports:
1. Current pipeline types (Regular, Hybrid, AutoML)
2. Future pipeline structures through composable components
3. Type safety and validation
4. Easy serialization and caching

Architecture:
- PipelineSpec: Immutable specification (hashable, serializable)
- Pipeline: Abstract base with fit/predict interface
- Concrete implementations: RegularPipeline, HybridPipeline, AutoMLPipeline
- ComposablePipeline: For future complex structures
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Protocol, Union
from enum import Enum
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
import hashlib
import json


class PipelineType(Enum):
    """Enumeration of supported pipeline types."""
    REGULAR = "regular"           # 3-step: imputer -> resampler -> classifier
    HYBRID = "hybrid"             # 2-step: imputer -> hybrid_method
    AUTOML = "automl"             # 1-step: automl_system
    COMPOSABLE = "composable"     # N-step: flexible component chain


class ComponentType(Enum):
    """Enumeration of pipeline component types."""
    IMPUTER = "imputer"
    RESAMPLER = "resampler"
    CLASSIFIER = "classifier"
    HYBRID = "hybrid"
    AUTOML = "automl"
    FEATURE_SELECTOR = "feature_selector"      # For future extension
    FEATURE_ENGINEER = "feature_engineer"      # For future extension
    ENSEMBLE = "ensemble"                       # For future extension
    CALIBRATOR = "calibrator"                   # For future extension


class PipelineComponent(Protocol):
    """
    Protocol defining the interface for pipeline components.

    All components should implement either:
    - fit/transform (for transformers like imputers)
    - fit/predict (for estimators like classifiers)
    - fit_resample (for resamplers)
    """

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'PipelineComponent':
        """Fit the component to training data."""
        ...


@dataclass(frozen=True)
class ComponentSpec:
    """
    Specification for a single pipeline component.

    Attributes:
        component_type: Type of component (imputer, resampler, etc.)
        component_name: Specific implementation name (e.g., "median", "smote")
        parameters: Component-specific parameters
    """
    component_type: ComponentType
    component_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        """Make hashable for use in sets/dicts."""
        params_str = json.dumps(self.parameters, sort_keys=True)
        return hash((self.component_type, self.component_name, params_str))


@dataclass(frozen=True)
class PipelineSpec:
    """
    Immutable specification of a pipeline.

    This class represents the "recipe" for a pipeline without containing
    the actual fitted components. It's hashable and can be used as dict keys
    for caching results.

    Attributes:
        pipeline_type: Type of pipeline (regular/hybrid/automl/composable)
        components: Ordered list of component specifications
        metadata: Additional configuration (random_seed, etc.)
    """
    pipeline_type: PipelineType
    components: Tuple[ComponentSpec, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate pipeline specification after creation."""
        if not self.components:
            raise ValueError("Pipeline must have at least one component")

        # Type-specific validation
        if self.pipeline_type == PipelineType.REGULAR:
            if len(self.components) != 3:
                raise ValueError(
                    f"Regular pipeline requires exactly 3 components (imputer, resampler, classifier). "
                    f"Got {len(self.components)}: {self.component_names()}"
                )
            expected = [ComponentType.IMPUTER, ComponentType.RESAMPLER, ComponentType.CLASSIFIER]
            actual = [c.component_type for c in self.components]
            if actual != expected:
                raise ValueError(
                    f"Regular pipeline must be [IMPUTER, RESAMPLER, CLASSIFIER]. "
                    f"Got: {actual}"
                )

        elif self.pipeline_type == PipelineType.HYBRID:
            if len(self.components) != 2:
                raise ValueError(
                    f"Hybrid pipeline requires exactly 2 components (imputer, hybrid). "
                    f"Got {len(self.components)}: {self.component_names()}"
                )
            expected = [ComponentType.IMPUTER, ComponentType.HYBRID]
            actual = [c.component_type for c in self.components]
            if actual != expected:
                raise ValueError(
                    f"Hybrid pipeline must be [IMPUTER, HYBRID]. Got: {actual}"
                )

        elif self.pipeline_type == PipelineType.AUTOML:
            if len(self.components) != 1:
                raise ValueError(
                    f"AutoML pipeline requires exactly 1 component. "
                    f"Got {len(self.components)}: {self.component_names()}"
                )
            if self.components[0].component_type != ComponentType.AUTOML:
                raise ValueError(
                    f"AutoML pipeline must contain AUTOML component. "
                    f"Got: {self.components[0].component_type}"
                )

        # COMPOSABLE type has no rigid structure - validated elsewhere

    def component_names(self) -> List[str]:
        """Get list of component names in order."""
        return [c.component_name for c in self.components]

    def to_list(self) -> List[str]:
        """
        Convert to legacy list format for backward compatibility.

        Returns:
            List of component names in order
        """
        return self.component_names()

    @classmethod
    def from_list(cls, components: List[str], pipeline_type: Optional[PipelineType] = None) -> 'PipelineSpec':
        """
        Create PipelineSpec from legacy list format.

        Args:
            components: List of component names (length determines type if not specified)
            pipeline_type: Optional explicit pipeline type

        Returns:
            PipelineSpec instance

        Raises:
            ValueError: If list length is invalid or components don't match type
        """
        if pipeline_type is None:
            # Infer type from length (backward compatibility)
            if len(components) == 3:
                pipeline_type = PipelineType.REGULAR
            elif len(components) == 2:
                pipeline_type = PipelineType.HYBRID
            elif len(components) == 1:
                pipeline_type = PipelineType.AUTOML
            else:
                raise ValueError(
                    f"Cannot infer pipeline type from {len(components)} components. "
                    f"Expected 1 (automl), 2 (hybrid), or 3 (regular). "
                    f"For custom structures, specify pipeline_type explicitly."
                )

        # Create ComponentSpec objects based on pipeline type
        if pipeline_type == PipelineType.REGULAR:
            component_specs = (
                ComponentSpec(ComponentType.IMPUTER, components[0]),
                ComponentSpec(ComponentType.RESAMPLER, components[1]),
                ComponentSpec(ComponentType.CLASSIFIER, components[2]),
            )
        elif pipeline_type == PipelineType.HYBRID:
            component_specs = (
                ComponentSpec(ComponentType.IMPUTER, components[0]),
                ComponentSpec(ComponentType.HYBRID, components[1]),
            )
        elif pipeline_type == PipelineType.AUTOML:
            component_specs = (
                ComponentSpec(ComponentType.AUTOML, components[0]),
            )
        else:
            raise ValueError(f"Unsupported pipeline type for from_list: {pipeline_type}")

        return cls(pipeline_type=pipeline_type, components=component_specs)

    @classmethod
    def create_regular(cls, imputer: str, resampler: str, classifier: str, **metadata) -> 'PipelineSpec':
        """
        Convenience constructor for regular pipelines.

        Args:
            imputer: Imputer name (e.g., "median", "knn")
            resampler: Resampler name (e.g., "smote", "rus")
            classifier: Classifier name (e.g., "lr", "svm")
            **metadata: Additional metadata

        Returns:
            PipelineSpec for regular pipeline
        """
        return cls(
            pipeline_type=PipelineType.REGULAR,
            components=(
                ComponentSpec(ComponentType.IMPUTER, imputer),
                ComponentSpec(ComponentType.RESAMPLER, resampler),
                ComponentSpec(ComponentType.CLASSIFIER, classifier),
            ),
            metadata=metadata
        )

    @classmethod
    def create_hybrid(cls, imputer: str, hybrid: str, **metadata) -> 'PipelineSpec':
        """
        Convenience constructor for hybrid pipelines.

        Args:
            imputer: Imputer name
            hybrid: Hybrid method name (e.g., "autosmote")
            **metadata: Additional metadata

        Returns:
            PipelineSpec for hybrid pipeline
        """
        return cls(
            pipeline_type=PipelineType.HYBRID,
            components=(
                ComponentSpec(ComponentType.IMPUTER, imputer),
                ComponentSpec(ComponentType.HYBRID, hybrid),
            ),
            metadata=metadata
        )

    @classmethod
    def create_automl(cls, automl: str, **metadata) -> 'PipelineSpec':
        """
        Convenience constructor for AutoML pipelines.

        Args:
            automl: AutoML system name (e.g., "autosklearn", "h2o", "tpot")
            **metadata: Additional metadata

        Returns:
            PipelineSpec for AutoML pipeline
        """
        return cls(
            pipeline_type=PipelineType.AUTOML,
            components=(ComponentSpec(ComponentType.AUTOML, automl),),
            metadata=metadata
        )

    @classmethod
    def create_composable(cls, component_specs: List[ComponentSpec], **metadata) -> 'PipelineSpec':
        """
        Create a flexible composable pipeline with arbitrary component sequence.

        This allows for future extension to complex structures like:
        - Imputer -> FeatureSelector -> Resampler -> Classifier
        - Imputer -> FeatureEngineer -> Resampler -> Ensemble -> Calibrator

        Args:
            component_specs: Ordered list of component specifications
            **metadata: Additional metadata

        Returns:
            PipelineSpec for composable pipeline

        Example:
            >>> specs = [
            ...     ComponentSpec(ComponentType.IMPUTER, "knn"),
            ...     ComponentSpec(ComponentType.FEATURE_SELECTOR, "chi2", {"k": 10}),
            ...     ComponentSpec(ComponentType.RESAMPLER, "smote"),
            ...     ComponentSpec(ComponentType.CLASSIFIER, "rf")
            ... ]
            >>> pipe_spec = PipelineSpec.create_composable(specs)
        """
        return cls(
            pipeline_type=PipelineType.COMPOSABLE,
            components=tuple(component_specs),
            metadata=metadata
        )

    def get_hash(self) -> str:
        """
        Generate a unique hash for this pipeline specification.

        Useful for cache keys and deduplication.

        Returns:
            SHA256 hash string
        """
        # Convert to JSON for stable hashing
        data = {
            'type': self.pipeline_type.value,
            'components': [
                {
                    'type': c.component_type.value,
                    'name': c.component_name,
                    'params': c.parameters
                }
                for c in self.components
            ],
            'metadata': self.metadata
        }
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def __str__(self) -> str:
        """Human-readable string representation."""
        return " -> ".join(self.component_names())

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"PipelineSpec({self.pipeline_type.value}: {str(self)})"

    def __hash__(self):
        """Hash based on all immutable attributes."""
        return hash((self.pipeline_type, self.components, tuple(sorted(self.metadata.items()))))


class Pipeline(ABC):
    """
    Abstract base class for all pipeline types.

    A Pipeline represents a complete ML workflow from raw data to predictions.
    It encapsulates the sequence of transformations and the final model.

    Design principles:
    - Immutable specification (PipelineSpec)
    - Mutable state (fitted components)
    - Clear fit/predict interface
    - Support for partial fitting and inspection
    """

    def __init__(self, spec: PipelineSpec):
        """
        Initialize pipeline with a specification.

        Args:
            spec: PipelineSpec defining the pipeline structure
        """
        self.spec = spec
        self._is_fitted = False
        self._fit_metadata: Dict[str, Any] = {}  # Store fit-time information

    @property
    def pipeline_type(self) -> PipelineType:
        """Get the type of this pipeline."""
        return self.spec.pipeline_type

    @property
    def is_fitted(self) -> bool:
        """Check if pipeline has been fitted."""
        return self._is_fitted

    @property
    def fit_metadata(self) -> Dict[str, Any]:
        """Get metadata from fitting process (timing, scores, etc.)."""
        return self._fit_metadata.copy()

    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'Pipeline':
        """
        Fit the pipeline to training data.

        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional arguments for specific components

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions on new data.

        Args:
            X: Test features

        Returns:
            Predicted labels
        """
        pass

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: Test features

        Returns:
            Class probabilities (shape: n_samples x n_classes)
        """
        pass

    @abstractmethod
    def get_components(self) -> Dict[str, Any]:
        """
        Get all fitted components in this pipeline.

        Returns:
            Dictionary mapping component names to instances
        """
        pass

    def cleanup(self) -> None:
        """Release resources held by pipeline components (e.g., Docker containers)."""
        get_components = getattr(self, "get_components", None)
        if not callable(get_components):
            return

        for component in get_components().values():
            if hasattr(component, "cleanup"):
                try:
                    component.cleanup()
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning(
                        "Failed to cleanup component %s: %s",
                        type(component).__name__,
                        exc,
                    )

    def validate(self) -> bool:
        """
        Validate pipeline configuration and state.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Spec validation happens in PipelineSpec.__post_init__
        return True

    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        """
        Get parameters of this pipeline (sklearn-compatible).

        Args:
            deep: If True, include parameters of components

        Returns:
            Parameter dictionary
        """
        params = {'spec': self.spec}
        if deep:
            for name, component in self.get_components().items():
                if hasattr(component, 'get_params'):
                    params[name] = component.get_params()
        return params

    def __str__(self) -> str:
        """String representation showing pipeline structure."""
        fitted_status = "✓ fitted" if self.is_fitted else "✗ unfitted"
        return f"{self.spec} ({fitted_status})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"{self.__class__.__name__}({self.spec})"


class RegularPipeline(Pipeline):
    """
    Regular 3-step pipeline: Imputer -> Resampler -> Classifier.

    This is the most common pipeline type for imbalanced learning,
    handling missing values, balancing classes, and classification.

    Flow:
    1. Impute missing values in X
    2. Resample both X and y to balance classes
    3. Train classifier on balanced data
    """

    def __init__(
        self,
        spec: PipelineSpec,
        imputer: Any = None,
        resampler: Any = None,
        classifier: Any = None
    ):
        """
        Initialize regular pipeline.

        Args:
            spec: Pipeline specification (must be REGULAR type)
            imputer: Imputation component instance
            resampler: Resampling component instance
            classifier: Classification component instance

        Raises:
            ValueError: If spec is not REGULAR type
        """
        if spec.pipeline_type != PipelineType.REGULAR:
            raise ValueError(f"RegularPipeline requires REGULAR type spec, got {spec.pipeline_type}")

        super().__init__(spec)
        self.imputer = imputer
        self.resampler = resampler
        self.classifier = classifier

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'RegularPipeline':
        """
        Fit the 3-step pipeline.

        Steps:
        1. Fit imputer and transform X
        2. Fit resampler and resample both X and y
        3. Fit classifier on resampled data

        Args:
            X: Training features (may contain missing values)
            y: Training labels
            **kwargs: Additional arguments (e.g., 'args' for custom components)

        Returns:
            Self for method chaining
        """
        if self.imputer is None or self.resampler is None or self.classifier is None:
            raise ValueError("All components (imputer, resampler, classifier) must be set before fitting")

        # Step 1: Imputation
        if hasattr(self.imputer, 'fit_transform'):
            X_imputed = self.imputer.fit_transform(X, y)
        else:
            self.imputer.fit(X, y)
            X_imputed = self.imputer.transform(X)

        # Step 2: Resampling
        if hasattr(self.resampler, 'fit_resample'):
            X_resampled, y_resampled = self.resampler.fit_resample(X_imputed, y)
        else:
            # Custom resamplers might use different interface
            # Pass args if available for backward compatibility
            args = kwargs.get('args')
            X_resampled, y_resampled = self.resampler.resample(args, self.spec.components[1].component_name, None)

        # Step 3: Classification
        self.classifier.fit(X_resampled, y_resampled)

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict labels for test data.

        Note: Resampling is NOT applied at test time (only during training).

        Args:
            X: Test features

        Returns:
            Predicted labels
        """
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        # Apply imputation (resampling not applied at test time)
        X_imputed = self.imputer.transform(X)

        # Classify
        return self.classifier.predict(X_imputed)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities for test data.

        Args:
            X: Test features

        Returns:
            Class probabilities
        """
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        X_imputed = self.imputer.transform(X)
        return self.classifier.predict_proba(X_imputed)

    def get_components(self) -> Dict[str, Any]:
        """Get all components in order."""
        return {
            'imputer': self.imputer,
            'resampler': self.resampler,
            'classifier': self.classifier
        }


class HybridPipeline(Pipeline):
    """
    Hybrid 2-step pipeline: Imputer -> Hybrid Method.

    Hybrid methods (e.g., AutoSMOTE, SPE) combine resampling and classification
    into a single integrated component that jointly optimizes both tasks.

    Flow:
    1. Impute missing values in X
    2. Apply hybrid method (resampling + classification together)
    """

    def __init__(
        self,
        spec: PipelineSpec,
        imputer: Any = None,
        hybrid_method: Any = None
    ):
        """
        Initialize hybrid pipeline.

        Args:
            spec: Pipeline specification (must be HYBRID type)
            imputer: Imputation component instance
            hybrid_method: Hybrid resampler+classifier instance

        Raises:
            ValueError: If spec is not HYBRID type
        """
        if spec.pipeline_type != PipelineType.HYBRID:
            raise ValueError(f"HybridPipeline requires HYBRID type spec, got {spec.pipeline_type}")

        super().__init__(spec)
        self.imputer = imputer
        self.hybrid_method = hybrid_method

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'HybridPipeline':
        """
        Fit the 2-step hybrid pipeline.

        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional arguments for hybrid method

        Returns:
            Self for method chaining
        """
        if self.imputer is None or self.hybrid_method is None:
            raise ValueError("Both imputer and hybrid_method must be set before fitting")

        # Step 1: Imputation
        if hasattr(self.imputer, 'fit_transform'):
            X_imputed = self.imputer.fit_transform(X, y)
        else:
            self.imputer.fit(X, y)
            X_imputed = self.imputer.transform(X)

        # Step 2: Hybrid method (handles resampling + classification internally)
        self.hybrid_method.fit(X_imputed, y, **kwargs)

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict labels."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        X_imputed = self.imputer.transform(X)
        return self.hybrid_method.predict(X_imputed)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        X_imputed = self.imputer.transform(X)
        return self.hybrid_method.predict_proba(X_imputed)

    def get_components(self) -> Dict[str, Any]:
        """Get all components."""
        return {
            'imputer': self.imputer,
            'hybrid_method': self.hybrid_method
        }


class AutoMLPipeline(Pipeline):
    """
    AutoML 1-step pipeline: Just the AutoML system.

    AutoML systems (e.g., auto-sklearn, TPOT, H2O) handle the entire
    pipeline construction internally, including:
    - Missing value imputation
    - Feature engineering and selection
    - Model selection
    - Hyperparameter optimization
    - Ensemble creation

    Flow:
    1. Pass data directly to AutoML system
    """

    def __init__(
        self,
        spec: PipelineSpec,
        automl_system: Any = None
    ):
        """
        Initialize AutoML pipeline.

        Args:
            spec: Pipeline specification (must be AUTOML type)
            automl_system: AutoML system instance

        Raises:
            ValueError: If spec is not AUTOML type
        """
        if spec.pipeline_type != PipelineType.AUTOML:
            raise ValueError(f"AutoMLPipeline requires AUTOML type spec, got {spec.pipeline_type}")

        super().__init__(spec)
        self.automl_system = automl_system

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'AutoMLPipeline':
        """
        Fit the AutoML system.

        Args:
            X: Training features
            y: Training labels
            **kwargs: AutoML-specific arguments (time_budget, etc.)

        Returns:
            Self for method chaining
        """
        if self.automl_system is None:
            raise ValueError("automl_system must be set before fitting")

        self.automl_system.fit(X, y, **kwargs)
        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict labels."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        return self.automl_system.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        return self.automl_system.predict_proba(X)

    def get_components(self) -> Dict[str, Any]:
        """Get the AutoML system."""
        return {'automl_system': self.automl_system}


class ComposablePipeline(Pipeline):
    """
    Flexible N-step pipeline supporting arbitrary component sequences.

    This enables future extensions like:
    - Imputer -> FeatureSelector -> Resampler -> Classifier
    - Imputer -> FeatureEngineer -> Resampler -> Ensemble -> Calibrator
    - Imputer -> Resampler1 -> Resampler2 -> Classifier (cascade resampling)

    Components are executed in sequence, with each step transforming the data
    for the next step.
    """

    def __init__(self, spec: PipelineSpec, components: Optional[List[Any]] = None):
        """
        Initialize composable pipeline.

        Args:
            spec: Pipeline specification (should be COMPOSABLE type)
            components: Ordered list of component instances (must match spec)

        Raises:
            ValueError: If spec is not COMPOSABLE type or components don't match
        """
        if spec.pipeline_type != PipelineType.COMPOSABLE:
            raise ValueError(f"ComposablePipeline requires COMPOSABLE type spec, got {spec.pipeline_type}")

        super().__init__(spec)
        self.components_list = components or []

        if self.components_list:
            if len(self.components_list) != len(self.spec.components):
                raise ValueError(
                    f"Number of component instances ({len(self.components_list)}) "
                    f"must match spec ({len(self.spec.components)})"
                )

    def set_components(self, components: List[Any]):
        """
        Set the component instances.

        Args:
            components: Ordered list of component instances

        Raises:
            ValueError: If length doesn't match spec
        """
        if len(components) != len(self.spec.components):
            raise ValueError(
                f"Number of component instances ({len(components)}) "
                f"must match spec ({len(self.spec.components)})"
            )
        self.components_list = components

    def fit(self, X: np.ndarray, y: np.ndarray, **kwargs) -> 'ComposablePipeline':
        """
        Fit the composable pipeline by executing components in sequence.

        Each component transforms the data for the next component.
        The final component is typically an estimator (classifier/regressor).

        Args:
            X: Training features
            y: Training labels
            **kwargs: Additional arguments passed to components

        Returns:
            Self for method chaining
        """
        if not self.components_list:
            raise ValueError("Components must be set before fitting")

        X_current = X
        y_current = y

        # Fit all components except the last
        for i, (component, spec) in enumerate(zip(self.components_list[:-1], self.spec.components[:-1])):
            if spec.component_type == ComponentType.RESAMPLER:
                # Resamplers modify both X and y
                if hasattr(component, 'fit_resample'):
                    X_current, y_current = component.fit_resample(X_current, y_current)
                else:
                    # Custom resampler interface
                    args = kwargs.get('args')
                    X_current, y_current = component.resample(args, spec.component_name, None)
            else:
                # Transformers modify only X
                if hasattr(component, 'fit_transform'):
                    X_current = component.fit_transform(X_current, y_current)
                else:
                    component.fit(X_current, y_current)
                    X_current = component.transform(X_current)

        # Fit the final component (typically a classifier/estimator)
        final_component = self.components_list[-1]
        final_component.fit(X_current, y_current)

        self._is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions by passing data through the pipeline.

        Note: Only transformers are applied (resamplers are skipped at test time).

        Args:
            X: Test features

        Returns:
            Predicted labels
        """
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        X_current = X

        # Transform through all components except the last
        for component, spec in zip(self.components_list[:-1], self.spec.components[:-1]):
            if spec.component_type != ComponentType.RESAMPLER:
                # Only apply transformers at test time (skip resamplers)
                X_current = component.transform(X_current)

        # Predict with final component
        return self.components_list[-1].predict(X_current)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted before prediction")

        X_current = X

        for component, spec in zip(self.components_list[:-1], self.spec.components[:-1]):
            if spec.component_type != ComponentType.RESAMPLER:
                X_current = component.transform(X_current)

        return self.components_list[-1].predict_proba(X_current)

    def get_components(self) -> Dict[str, Any]:
        """Get all components as a dictionary."""
        return {
            spec.component_name: component
            for spec, component in zip(self.spec.components, self.components_list)
        }


def create_pipeline_from_list(components: List[str]) -> Pipeline:
    """
    Factory function to create a Pipeline from legacy list format.

    This is for backward compatibility with the old list-based approach.

    Args:
        components: List of component names

    Returns:
        Appropriate Pipeline subclass instance (without fitted components)

    Example:
        >>> pipe = create_pipeline_from_list(["median", "smote", "lr"])
        >>> isinstance(pipe, RegularPipeline)
        True
        >>> str(pipe.spec)
        'median -> smote -> lr'
    """
    spec = PipelineSpec.from_list(components)

    if spec.pipeline_type == PipelineType.REGULAR:
        return RegularPipeline(spec)
    elif spec.pipeline_type == PipelineType.HYBRID:
        return HybridPipeline(spec)
    elif spec.pipeline_type == PipelineType.AUTOML:
        return AutoMLPipeline(spec)
    else:
        raise ValueError(f"Cannot create pipeline for type: {spec.pipeline_type}")


def create_pipeline_from_spec(spec: PipelineSpec) -> Pipeline:
    """
    Factory function to create a Pipeline from a PipelineSpec.

    Args:
        spec: Pipeline specification

    Returns:
        Appropriate Pipeline subclass instance

    Example:
        >>> spec = PipelineSpec.create_regular("knn", "smote", "rf")
        >>> pipe = create_pipeline_from_spec(spec)
        >>> isinstance(pipe, RegularPipeline)
        True
    """
    if spec.pipeline_type == PipelineType.REGULAR:
        return RegularPipeline(spec)
    elif spec.pipeline_type == PipelineType.HYBRID:
        return HybridPipeline(spec)
    elif spec.pipeline_type == PipelineType.AUTOML:
        return AutoMLPipeline(spec)
    elif spec.pipeline_type == PipelineType.COMPOSABLE:
        return ComposablePipeline(spec)
    else:
        raise ValueError(f"Unknown pipeline type: {spec.pipeline_type}")
