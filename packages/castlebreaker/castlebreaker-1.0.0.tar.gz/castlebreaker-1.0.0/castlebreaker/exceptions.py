"""
Castle Breaker exception hierarchy.

All exceptions raised by the package inherit from CastleBreakerError,
making it easy to catch all package-related errors in a single except block.
"""

from __future__ import annotations

from typing import Any


class CastleBreakerError(Exception):
    """Base exception for all Castle Breaker errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class AuthenticationError(CastleBreakerError):
    """
    Raised when API key is invalid or missing.
    
    This typically indicates the API key was not provided or has been revoked.
    """

    pass


class RateLimitError(CastleBreakerError):
    """
    Raised when rate limit is exceeded.
    
    Attributes:
        retry_after: Seconds to wait before retrying (if provided by server).
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.retry_after = retry_after


class InvalidRequestError(CastleBreakerError):
    """
    Raised for 400-level errors (bad request, invalid parameters).
    
    Check the `details` attribute for specific validation errors.
    """

    pass


class ServiceUnavailableError(CastleBreakerError):
    """
    Raised when the API service is temporarily unavailable (5xx errors).
    
    These are typically transient and can be retried.
    """

    pass


class NetworkError(CastleBreakerError):
    """
    Raised for connection-level failures.
    
    This includes DNS resolution failures, connection timeouts,
    and other network-related issues.
    """

    pass


class TaskError(CastleBreakerError):
    """
    Raised when a task fails to complete successfully.
    
    Attributes:
        task_id: The ID of the failed task (if available).
        status: The final status of the task.
    """

    def __init__(
        self,
        message: str,
        *,
        task_id: str | None = None,
        status: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.task_id = task_id
        self.status = status
