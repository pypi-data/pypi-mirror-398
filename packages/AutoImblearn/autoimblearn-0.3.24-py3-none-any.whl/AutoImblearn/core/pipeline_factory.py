"""
PipelineFactory for AutoImblearn.

This module provides a centralized component registry and factory for creating
pipeline components and complete pipelines. It replaces the scattered dictionary-based
component lookup with a clean, extensible interface.

Key features:
- Component registration and discovery
- Type-safe component creation
- Lazy loading of heavy components (Docker-based)
- Easy extension with new components
"""

from typing import Dict, Any, List, Optional, Callable, Type
import logging
from dataclasses import dataclass

from .pipeline import (
    Pipeline, PipelineSpec, PipelineType, ComponentType,
    RegularPipeline, HybridPipeline, AutoMLPipeline, ComposablePipeline,
    ComponentSpec
)


logger = logging.getLogger(__name__)


@dataclass
class ComponentRegistration:
    """
    Registration metadata for a pipeline component.

    Attributes:
        name: Component identifier (e.g., "median", "smote", "lr")
        component_type: Type of component (imputer, resampler, etc.)
        factory: Callable that creates the component instance
        description: Human-readable description
        requires_docker: Whether component needs Docker containers
        parameters: Default/allowed parameters for this component
    """
    name: str
    component_type: ComponentType
    factory: Callable[..., Any]
    description: str = ""
    requires_docker: bool = False
    parameters: Dict[str, Any] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class ComponentRegistry:
    """
    Central registry for all pipeline components.

    This class maintains a registry of available components (imputers, resamplers,
    classifiers, hybrids, AutoML systems) and provides methods to query and
    instantiate them.

    Example:
        >>> registry = ComponentRegistry()
        >>> registry.register_imputer("median", lambda: MedianImputer())
        >>> imputer = registry.create("median", ComponentType.IMPUTER)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._registry: Dict[ComponentType, Dict[str, ComponentRegistration]] = {
            ComponentType.IMPUTER: {},
            ComponentType.RESAMPLER: {},
            ComponentType.CLASSIFIER: {},
            ComponentType.HYBRID: {},
            ComponentType.AUTOML: {},
            ComponentType.FEATURE_SELECTOR: {},
            ComponentType.FEATURE_ENGINEER: {},
            ComponentType.ENSEMBLE: {},
            ComponentType.CALIBRATOR: {},
        }

    def register(
        self,
        name: str,
        component_type: ComponentType,
        factory: Callable[..., Any],
        description: str = "",
        requires_docker: bool = False,
        **parameters
    ) -> None:
        """
        Register a new component.

        Args:
            name: Component identifier
            component_type: Type of component
            factory: Callable that creates the component
            description: Human-readable description
            requires_docker: Whether component needs Docker
            **parameters: Default parameters for this component

        Raises:
            ValueError: If component already registered
        """
        if name in self._registry[component_type]:
            logger.warning(f"Component {name} ({component_type.value}) already registered. Overwriting.")

        registration = ComponentRegistration(
            name=name,
            component_type=component_type,
            factory=factory,
            description=description,
            requires_docker=requires_docker,
            parameters=parameters
        )

        self._registry[component_type][name] = registration
        logger.debug(f"Registered component: {name} ({component_type.value})")

    def register_imputer(self, name: str, factory: Callable, **kwargs):
        """Convenience method to register an imputer."""
        self.register(name, ComponentType.IMPUTER, factory, **kwargs)

    def register_resampler(self, name: str, factory: Callable, **kwargs):
        """Convenience method to register a resampler."""
        self.register(name, ComponentType.RESAMPLER, factory, **kwargs)

    def register_classifier(self, name: str, factory: Callable, **kwargs):
        """Convenience method to register a classifier."""
        self.register(name, ComponentType.CLASSIFIER, factory, **kwargs)

    def register_hybrid(self, name: str, factory: Callable, **kwargs):
        """Convenience method to register a hybrid method."""
        self.register(name, ComponentType.HYBRID, factory, **kwargs)

    def register_automl(self, name: str, factory: Callable, **kwargs):
        """Convenience method to register an AutoML system."""
        self.register(name, ComponentType.AUTOML, factory, **kwargs)

    def is_registered(self, name: str, component_type: ComponentType) -> bool:
        """
        Check if a component is registered.

        Args:
            name: Component name
            component_type: Component type

        Returns:
            True if registered
        """
        return name in self._registry[component_type]

    def get_registration(self, name: str, component_type: ComponentType) -> ComponentRegistration:
        """
        Get registration info for a component.

        Args:
            name: Component name
            component_type: Component type

        Returns:
            ComponentRegistration

        Raises:
            KeyError: If component not found
        """
        if not self.is_registered(name, component_type):
            raise KeyError(
                f"Component '{name}' of type {component_type.value} not found. "
                f"Available: {self.list_components(component_type)}"
            )
        return self._registry[component_type][name]

    def create(
        self,
        name: str,
        component_type: ComponentType,
        **kwargs
    ) -> Any:
        """
        Create a component instance.

        Args:
            name: Component name
            component_type: Component type
            **kwargs: Arguments passed to factory

        Returns:
            Component instance

        Raises:
            KeyError: If component not registered
        """
        registration = self.get_registration(name, component_type)

        # Merge default parameters with provided kwargs
        params = {**registration.parameters, **kwargs}

        try:
            component = registration.factory(**params)
            logger.debug(f"Created component: {name} ({component_type.value})")
            return component
        except Exception as e:
            logger.error(f"Failed to create component {name}: {e}")
            raise

    def list_components(self, component_type: ComponentType) -> List[str]:
        """
        List all registered components of a given type.

        Args:
            component_type: Type to filter by

        Returns:
            List of component names
        """
        return list(self._registry[component_type].keys())

    def get_all_components(self, component_type: ComponentType) -> Dict[str, ComponentRegistration]:
        """
        Get all registrations for a component type.

        Args:
            component_type: Type to query

        Returns:
            Dictionary mapping names to registrations
        """
        return self._registry[component_type].copy()


class PipelineFactory:
    """
    Factory for creating complete pipelines with all components instantiated.

    This class uses a ComponentRegistry to instantiate individual components
    and assembles them into complete Pipeline objects.

    Example:
        >>> factory = PipelineFactory()
        >>> pipeline = factory.create_from_list(["median", "smote", "lr"])
        >>> pipeline.fit(X_train, y_train)
    """

    def __init__(self, registry: Optional[ComponentRegistry] = None, args: Any = None):
        """
        Initialize factory.

        Args:
            registry: ComponentRegistry to use (creates default if None)
            args: Global arguments passed to components (for backward compatibility)
        """
        self.registry = registry or self._create_default_registry()
        self.args = args  # For backward compatibility with old code

    def _create_default_registry(self) -> ComponentRegistry:
        """
        Create and populate the default component registry.

        This imports and registers all standard components.

        Returns:
            Populated ComponentRegistry
        """
        registry = ComponentRegistry()

        # Import and register imputers
        try:
            from ..pipelines.customimputation import imps, CustomImputer
            for name in imps:
                registry.register_imputer(
                    name=name,
                    factory=lambda n=name: CustomImputer(
                        method=n,
                        host_data_root=None,  # Set later if needed
                        result_file_path=None
                    ),
                    description=f"{name} imputation method"
                )
        except ImportError as e:
            logger.warning(f"Could not import imputers: {e}")

        # Import and register resamplers
        try:
            from ..pipelines.customrsp import rsps
            for name, resampler_instance in rsps.items():
                # rsps dict already contains instances, so we wrap them
                registry.register_resampler(
                    name=name,
                    factory=lambda inst=resampler_instance: inst,
                    description=f"{name} resampling method",
                    requires_docker=True  # Many use Docker
                )
        except ImportError as e:
            logger.warning(f"Could not import resamplers: {e}")

        # Import and register classifiers
        try:
            from ..pipelines.customclf import clfs
            for name, clf_instance in clfs.items():
                # clfs dict contains sklearn estimators (need cloning for reuse)
                from sklearn.base import clone
                registry.register_classifier(
                    name=name,
                    factory=lambda inst=clf_instance: clone(inst),
                    description=f"{name} classifier"
                )
        except ImportError as e:
            logger.warning(f"Could not import classifiers: {e}")

        # Import and register hybrid methods
        try:
            from ..pipelines.customhbd import hybrid_factories
            for name in hybrid_factories:
                registry.register_hybrid(
                    name=name,
                    factory=lambda: None,  # Will be created by RunPipe
                    description=f"{name} hybrid method",
                    requires_docker=True
                )
        except ImportError as e:
            logger.warning(f"Could not import hybrid methods: {e}")

        # Import and register AutoML systems
        try:
            from ..pipelines.customautoml import automls
            for name in automls:
                registry.register_automl(
                    name=name,
                    factory=lambda: None,  # Will be created by RunPipe
                    description=f"{name} AutoML system",
                    requires_docker=True
                )
        except ImportError as e:
            logger.warning(f"Could not import AutoML systems: {e}")

        return registry

    def create_from_list(
        self,
        components: List[str],
        instantiate: bool = False,
        **kwargs
    ) -> Pipeline:
        """
        Create a Pipeline from legacy list format.

        Args:
            components: List of component names
            instantiate: If True, create and attach component instances
            **kwargs: Additional arguments for component creation

        Returns:
            Pipeline object (with or without instantiated components)

        Example:
            >>> pipe = factory.create_from_list(["knn", "smote", "lr"], instantiate=True)
            >>> pipe.fit(X, y)
        """
        spec = PipelineSpec.from_list(components)
        return self.create_from_spec(spec, instantiate=instantiate, **kwargs)

    def create_from_spec(
        self,
        spec: PipelineSpec,
        instantiate: bool = False,
        **kwargs
    ) -> Pipeline:
        """
        Create a Pipeline from a PipelineSpec.

        Args:
            spec: Pipeline specification
            instantiate: If True, create and attach component instances
            **kwargs: Additional arguments for component creation

        Returns:
            Pipeline object

        Example:
            >>> spec = PipelineSpec.create_regular("median", "rus", "svm")
            >>> pipe = factory.create_from_spec(spec, instantiate=True)
        """
        if spec.pipeline_type == PipelineType.REGULAR:
            return self._create_regular_pipeline(spec, instantiate, **kwargs)
        elif spec.pipeline_type == PipelineType.HYBRID:
            return self._create_hybrid_pipeline(spec, instantiate, **kwargs)
        elif spec.pipeline_type == PipelineType.AUTOML:
            return self._create_automl_pipeline(spec, instantiate, **kwargs)
        elif spec.pipeline_type == PipelineType.COMPOSABLE:
            return self._create_composable_pipeline(spec, instantiate, **kwargs)
        else:
            raise ValueError(f"Unknown pipeline type: {spec.pipeline_type}")

    def _create_regular_pipeline(
        self,
        spec: PipelineSpec,
        instantiate: bool,
        **kwargs
    ) -> RegularPipeline:
        """Create a RegularPipeline."""
        if not instantiate:
            return RegularPipeline(spec)

        # Instantiate components
        imputer_name = spec.components[0].component_name
        resampler_name = spec.components[1].component_name
        classifier_name = spec.components[2].component_name

        # Create imputer
        imputer = self.registry.create(imputer_name, ComponentType.IMPUTER, **kwargs)

        # Create resampler
        resampler = self.registry.create(resampler_name, ComponentType.RESAMPLER, **kwargs)

        # Create classifier
        classifier = self.registry.create(classifier_name, ComponentType.CLASSIFIER, **kwargs)

        return RegularPipeline(
            spec=spec,
            imputer=imputer,
            resampler=resampler,
            classifier=classifier
        )

    def _create_hybrid_pipeline(
        self,
        spec: PipelineSpec,
        instantiate: bool,
        **kwargs
    ) -> HybridPipeline:
        """Create a HybridPipeline."""
        if not instantiate:
            return HybridPipeline(spec)

        imputer_name = spec.components[0].component_name
        hybrid_name = spec.components[1].component_name

        imputer = self.registry.create(imputer_name, ComponentType.IMPUTER, **kwargs)
        hybrid_method = self.registry.create(hybrid_name, ComponentType.HYBRID, **kwargs)

        return HybridPipeline(
            spec=spec,
            imputer=imputer,
            hybrid_method=hybrid_method
        )

    def _create_automl_pipeline(
        self,
        spec: PipelineSpec,
        instantiate: bool,
        **kwargs
    ) -> AutoMLPipeline:
        """Create an AutoMLPipeline."""
        if not instantiate:
            return AutoMLPipeline(spec)

        automl_name = spec.components[0].component_name
        automl_system = self.registry.create(automl_name, ComponentType.AUTOML, **kwargs)

        return AutoMLPipeline(
            spec=spec,
            automl_system=automl_system
        )

    def _create_composable_pipeline(
        self,
        spec: PipelineSpec,
        instantiate: bool,
        **kwargs
    ) -> ComposablePipeline:
        """Create a ComposablePipeline."""
        if not instantiate:
            return ComposablePipeline(spec)

        # Create all components in order
        component_instances = []
        for comp_spec in spec.components:
            component = self.registry.create(
                comp_spec.component_name,
                comp_spec.component_type,
                **{**comp_spec.parameters, **kwargs}
            )
            component_instances.append(component)

        pipeline = ComposablePipeline(spec)
        pipeline.set_components(component_instances)
        return pipeline

    def get_available_components(self, component_type: ComponentType) -> List[str]:
        """
        Get list of available components for a given type.

        Args:
            component_type: Type to query

        Returns:
            List of component names

        Example:
            >>> factory.get_available_components(ComponentType.IMPUTER)
            ['mean', 'median', 'knn', 'ii', 'gain', 'MIRACLE', 'MIWAE']
        """
        return self.registry.list_components(component_type)

    def validate_pipeline_spec(self, spec: PipelineSpec) -> bool:
        """
        Validate that all components in spec are registered.

        Args:
            spec: Pipeline specification to validate

        Returns:
            True if all components are available

        Raises:
            ValueError: If any component is not registered
        """
        for comp_spec in spec.components:
            if not self.registry.is_registered(comp_spec.component_name, comp_spec.component_type):
                raise ValueError(
                    f"Component '{comp_spec.component_name}' of type "
                    f"{comp_spec.component_type.value} is not registered. "
                    f"Available: {self.registry.list_components(comp_spec.component_type)}"
                )
        return True


# Global default factory instance (for convenience)
_default_factory: Optional[PipelineFactory] = None


def get_default_factory() -> PipelineFactory:
    """
    Get the global default PipelineFactory instance.

    This is a singleton that's created on first access.

    Returns:
        Global PipelineFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = PipelineFactory()
    return _default_factory


def set_default_factory(factory: PipelineFactory):
    """
    Set the global default PipelineFactory.

    Useful for testing or customization.

    Args:
        factory: PipelineFactory to use as default
    """
    global _default_factory
    _default_factory = factory
