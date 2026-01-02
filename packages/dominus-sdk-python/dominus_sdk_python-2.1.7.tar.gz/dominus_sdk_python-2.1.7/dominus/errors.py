"""
Dominus SDK Error Classes

Custom exceptions for the Dominus SDK with structured error information.
"""
from typing import Any, Dict, Optional


class DominusError(Exception):
    """
    Base exception for all Dominus SDK errors.

    Provides structured error information including HTTP status codes,
    error messages, and optional details from the backend.

    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if applicable)
        details: Additional error details from backend
        endpoint: The endpoint that was called (if applicable)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.endpoint = endpoint
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.status_code:
            parts.append(f"(status {self.status_code})")
        if self.endpoint:
            parts.append(f"at {self.endpoint}")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"DominusError(message={self.message!r}, "
            f"status_code={self.status_code}, "
            f"details={self.details!r}, "
            f"endpoint={self.endpoint!r})"
        )


class AuthenticationError(DominusError):
    """Raised when authentication fails (invalid token, expired JWT, etc.)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        status_code: int = 401,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class AuthorizationError(DominusError):
    """Raised when authorization fails (insufficient permissions)."""

    def __init__(
        self,
        message: str = "Permission denied",
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class NotFoundError(DominusError):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        status_code: int = 404,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class ValidationError(DominusError):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class ConflictError(DominusError):
    """Raised when there's a conflict (duplicate key, version mismatch, etc.)."""

    def __init__(
        self,
        message: str = "Conflict",
        status_code: int = 409,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class ServiceError(DominusError):
    """Raised when a backend service error occurs."""

    def __init__(
        self,
        message: str = "Service error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class ConnectionError(DominusError):
    """Raised when connection to the backend fails."""

    def __init__(
        self,
        message: str = "Connection failed",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class TimeoutError(DominusError):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


class SecureTableError(DominusError):
    """Raised when accessing a secure table without providing a reason."""

    def __init__(
        self,
        message: str = "Access to secure table requires 'reason' parameter",
        status_code: int = 403,
        details: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, details, endpoint)


def raise_for_status(
    status_code: int,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None
) -> None:
    """
    Raise appropriate DominusError subclass based on status code.

    Args:
        status_code: HTTP status code
        message: Error message
        details: Optional error details
        endpoint: Optional endpoint that was called

    Raises:
        Appropriate DominusError subclass
    """
    error_classes = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        409: ConflictError,
        500: ServiceError,
        502: ServiceError,
        503: ServiceError,
        504: TimeoutError,
    }

    error_class = error_classes.get(status_code, DominusError)
    raise error_class(message, status_code, details, endpoint)
