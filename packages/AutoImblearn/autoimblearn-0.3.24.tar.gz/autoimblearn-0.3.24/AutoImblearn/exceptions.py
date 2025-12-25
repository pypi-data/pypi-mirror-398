"""
Custom exception hierarchy for AutoImblearn.

This module defines a hierarchy of exceptions that provide better error handling
and debugging capabilities throughout the AutoImblearn system.
"""

from typing import Optional, Dict, Any


class AutoImblearnException(Exception):
    """
    Base exception for all AutoImblearn errors.

    All custom exceptions in AutoImblearn should inherit from this.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class PipelineError(AutoImblearnException):
    """
    Exception raised when pipeline execution fails.

    This can occur during:
    - Pipeline fitting
    - Pipeline prediction
    - Pipeline validation
    """

    def __init__(self, message: str, pipeline_spec=None, stage: Optional[str] = None,
                 original_error: Optional[Exception] = None):
        """
        Initialize pipeline error.

        Args:
            message: Error description
            pipeline_spec: The pipeline specification that failed
            stage: Which stage failed (e.g., "imputation", "resampling", "classification")
            original_error: The underlying exception that caused this error
        """
        details = {}
        if pipeline_spec:
            details['pipeline'] = str(pipeline_spec)
        if stage:
            details['stage'] = stage
        if original_error:
            details['original_error'] = str(original_error)

        super().__init__(message, details)
        self.pipeline_spec = pipeline_spec
        self.stage = stage
        self.original_error = original_error


class ComponentNotFoundError(AutoImblearnException):
    """
    Exception raised when a requested component is not registered.

    This occurs when trying to create a component that doesn't exist
    in the ComponentRegistry.
    """

    def __init__(self, component_name: str, component_type,
                 available_components: Optional[list] = None):
        """
        Initialize component not found error.

        Args:
            component_name: Name of the component that wasn't found
            component_type: Type of component (from ComponentType enum)
            available_components: List of available components of this type
        """
        message = f"Component '{component_name}' of type {component_type.value} not found"

        details = {
            'component_name': component_name,
            'component_type': component_type.value
        }

        if available_components:
            details['available'] = available_components
            message += f". Available: {available_components}"

        super().__init__(message, details)
        self.component_name = component_name
        self.component_type = component_type
        self.available_components = available_components


class DockerContainerError(AutoImblearnException):
    """
    Exception raised when Docker container operations fail.

    This can occur during:
    - Container creation
    - Container startup
    - API communication
    - Container cleanup
    """

    def __init__(self, message: str, container_id: Optional[str] = None,
                 image_name: Optional[str] = None, logs: Optional[str] = None,
                 operation: Optional[str] = None):
        """
        Initialize Docker container error.

        Args:
            message: Error description
            container_id: ID of the container that failed
            image_name: Docker image name
            logs: Container logs (for debugging)
            operation: Which operation failed (e.g., "start", "stop", "api_call")
        """
        details = {}
        if container_id:
            details['container_id'] = container_id
        if image_name:
            details['image'] = image_name
        if operation:
            details['operation'] = operation

        super().__init__(message, details)
        self.container_id = container_id
        self.image_name = image_name
        self.logs = logs
        self.operation = operation

    def get_logs(self, max_lines: int = 50) -> str:
        """
        Get formatted container logs.

        Args:
            max_lines: Maximum number of log lines to return

        Returns:
            Formatted log string
        """
        if not self.logs:
            return "No logs available"

        lines = self.logs.split('\n')
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
            return f"... (showing last {max_lines} lines)\n" + '\n'.join(lines)
        return self.logs


class ValidationError(AutoImblearnException):
    """
    Exception raised when validation fails.

    This can occur during:
    - Pipeline specification validation
    - Configuration validation
    - Data validation
    """

    def __init__(self, message: str, field: Optional[str] = None,
                 expected=None, actual=None):
        """
        Initialize validation error.

        Args:
            message: Error description
            field: Which field failed validation
            expected: Expected value/type
            actual: Actual value/type
        """
        details = {}
        if field:
            details['field'] = field
        if expected is not None:
            details['expected'] = expected
        if actual is not None:
            details['actual'] = actual

        super().__init__(message, details)
        self.field = field
        self.expected = expected
        self.actual = actual


class SearchBudgetExceededError(AutoImblearnException):
    """
    Exception raised when search budget is exceeded.

    This occurs when:
    - Maximum iterations reached
    - Time budget exceeded
    """

    def __init__(self, message: str, budget_type: str,
                 limit, actual, best_found=None):
        """
        Initialize budget exceeded error.

        Args:
            message: Error description
            budget_type: Type of budget ("iterations" or "time")
            limit: The budget limit
            actual: Actual value reached
            best_found: Best pipeline found before budget exhausted
        """
        details = {
            'budget_type': budget_type,
            'limit': limit,
            'actual': actual
        }
        if best_found:
            details['best_pipeline'] = str(best_found)

        super().__init__(message, details)
        self.budget_type = budget_type
        self.limit = limit
        self.actual = actual
        self.best_found = best_found


class DataLoadError(AutoImblearnException):
    """
    Exception raised when data loading fails.

    This can occur during:
    - CSV/Excel file loading
    - Data preprocessing
    - Data splitting
    """

    def __init__(self, message: str, dataset_name: Optional[str] = None,
                 file_path: Optional[str] = None, reason: Optional[str] = None):
        """
        Initialize data load error.

        Args:
            message: Error description
            dataset_name: Name of the dataset
            file_path: Path to the data file
            reason: Reason for failure
        """
        details = {}
        if dataset_name:
            details['dataset'] = dataset_name
        if file_path:
            details['path'] = file_path
        if reason:
            details['reason'] = reason

        super().__init__(message, details)
        self.dataset_name = dataset_name
        self.file_path = file_path
        self.reason = reason


class CacheError(AutoImblearnException):
    """
    Exception raised when cache operations fail.

    This can occur during:
    - Cache read
    - Cache write
    - Cache invalidation
    """

    def __init__(self, message: str, operation: Optional[str] = None,
                 cache_key: Optional[str] = None):
        """
        Initialize cache error.

        Args:
            message: Error description
            operation: Which operation failed ("read", "write", "delete")
            cache_key: The cache key involved
        """
        details = {}
        if operation:
            details['operation'] = operation
        if cache_key:
            details['cache_key'] = cache_key

        super().__init__(message, details)
        self.operation = operation
        self.cache_key = cache_key


class ImputationError(PipelineError):
    """Exception raised when imputation fails."""

    def __init__(self, message: str, imputer_name: str, **kwargs):
        super().__init__(message, stage="imputation", **kwargs)
        self.imputer_name = imputer_name


class ResamplingError(PipelineError):
    """Exception raised when resampling fails."""

    def __init__(self, message: str, resampler_name: str, **kwargs):
        super().__init__(message, stage="resampling", **kwargs)
        self.resampler_name = resampler_name


class ClassificationError(PipelineError):
    """Exception raised when classification fails."""

    def __init__(self, message: str, classifier_name: str, **kwargs):
        super().__init__(message, stage="classification", **kwargs)
        self.classifier_name = classifier_name


# Utility functions for exception handling

def wrap_component_error(component_name: str, stage: str, original_error: Exception) -> PipelineError:
    """
    Wrap a component error in a PipelineError with context.

    Args:
        component_name: Name of the component that failed
        stage: Stage where error occurred
        original_error: The original exception

    Returns:
        PipelineError with full context

    Example:
        try:
            imputer.fit(X, y)
        except Exception as e:
            raise wrap_component_error("median", "imputation", e)
    """
    message = f"Component '{component_name}' failed during {stage}: {str(original_error)}"

    if stage == "imputation":
        return ImputationError(message, imputer_name=component_name, original_error=original_error)
    elif stage == "resampling":
        return ResamplingError(message, resampler_name=component_name, original_error=original_error)
    elif stage == "classification":
        return ClassificationError(message, classifier_name=component_name, original_error=original_error)
    else:
        return PipelineError(message, stage=stage, original_error=original_error)


def format_exception_chain(exc: Exception) -> str:
    """
    Format an exception with its chain of causes.

    Args:
        exc: The exception to format

    Returns:
        Multi-line string showing exception chain
    """
    lines = []
    current = exc
    depth = 0

    while current:
        indent = "  " * depth
        lines.append(f"{indent}{type(current).__name__}: {str(current)}")

        # Add details if available
        if isinstance(current, AutoImblearnException) and current.details:
            for key, value in current.details.items():
                lines.append(f"{indent}  {key}: {value}")

        # Move to cause
        current = getattr(current, 'original_error', None) or current.__cause__
        depth += 1

    return '\n'.join(lines)
