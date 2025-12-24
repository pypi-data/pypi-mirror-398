"""
Execution-specific exceptions for the autonomous execution system.

These exceptions provide specific error handling for common issues that
can occur during programmatic agent execution.
"""

from typing import Optional


class ExecutionError(Exception):
    """Base exception for execution-related errors."""

    def __init__(
        self,
        message: str,
        execution_id: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        self.message = message
        self.execution_id = execution_id
        self.status_code = status_code
        super().__init__(message)

    def __str__(self) -> str:
        if self.execution_id:
            return f"ExecutionError (ID: {self.execution_id}): {self.message}"
        return f"ExecutionError: {self.message}"


class AuthenticationError(ExecutionError):
    """Raised when API key authentication fails."""

    def __init__(self, message: str = "Invalid API key or insufficient permissions"):
        super().__init__(message, status_code=401)


class NotFoundError(ExecutionError):
    """Raised when requested agent, workflow, or execution is not found."""

    def __init__(self, message: str, resource_type: str = "resource"):
        self.resource_type = resource_type
        super().__init__(message, status_code=404)

    def __str__(self) -> str:
        return f"NotFoundError ({self.resource_type}): {self.message}"


class ValidationError(ExecutionError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, status_code=400)

    def __str__(self) -> str:
        if self.field:
            return f"ValidationError ({self.field}): {self.message}"
        return f"ValidationError: {self.message}"


class RateLimitError(ExecutionError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)

    def __str__(self) -> str:
        if self.retry_after:
            return f"RateLimitError: {self.message} (retry after {self.retry_after}s)"
        return f"RateLimitError: {self.message}"


class TimeoutError(ExecutionError):
    """Raised when execution times out."""

    def __init__(self, message: str = "Execution timeout", timeout_seconds: Optional[int] = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, status_code=408)

    def __str__(self) -> str:
        if self.timeout_seconds:
            return f"TimeoutError: {self.message} (timeout: {self.timeout_seconds}s)"
        return f"TimeoutError: {self.message}"


class ServerError(ExecutionError):
    """Raised when server encounters an internal error."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)