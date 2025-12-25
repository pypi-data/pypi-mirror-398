"""
Custom exceptions for AutoImblearn components.
"""


class DockerContainerError(Exception):
    """
    Exception raised when a Docker container operation fails.

    Attributes:
        message: Explanation of the error
        container_id: ID of the Docker container (if available)
        image_name: Name of the Docker image
        logs: Container logs (if available)
        operation: The operation that failed (e.g., 'train', 'transform', 'build')
    """

    def __init__(self, message, container_id=None, image_name=None, logs=None, operation=None):
        self.message = message
        self.container_id = container_id
        self.image_name = image_name
        self.logs = logs
        self.operation = operation

        # Build detailed error message
        error_parts = [message]

        if image_name:
            error_parts.append(f"Image: {image_name}")

        if container_id:
            error_parts.append(f"Container ID: {container_id}")

        if operation:
            error_parts.append(f"Operation: {operation}")

        if logs:
            error_parts.append(f"\nContainer logs:\n{logs}")

        super().__init__("\n".join(error_parts))


class ImputationError(Exception):
    """Exception raised when imputation fails."""
    pass


class ResamplingError(Exception):
    """Exception raised when resampling fails."""
    pass


class ClassificationError(Exception):
    """Exception raised when classification fails."""
    pass


class ModelNotFoundError(Exception):
    """Exception raised when a requested model is not found in the registry."""
    pass


class DataValidationError(Exception):
    """Exception raised when data validation fails."""
    pass
