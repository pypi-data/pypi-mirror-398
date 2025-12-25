"""
Custom Exception Classes

Domain-agnostic exceptions compatible with @smart/contracts error types.
"""

from typing import Any

from .models import FieldError


class SmartException(Exception):
    """
    Base exception for all Smart Platform errors.

    Attributes:
        error_type: Error type identifier (maps to ErrorType in @smart/contracts)
        status_code: HTTP status code
        detail: Detailed error message
        errors: Optional field-level validation errors
        meta: Optional additional metadata
    """

    error_type: str = "internal_error"
    status_code: int = 500
    title: str = "Internal Server Error"

    def __init__(
        self,
        detail: str,
        errors: list[FieldError] | None = None,
        meta: dict[str, Any] | None = None,
    ):
        self.detail = detail
        self.errors = errors
        self.meta = meta or {}
        super().__init__(detail)


class ValidationException(SmartException):
    """Raised when validation fails."""

    error_type = "validation_error"
    status_code = 422
    title = "Validation Failed"


class AuthenticationException(SmartException):
    """Raised when authentication fails."""

    error_type = "authentication_error"
    status_code = 401
    title = "Authentication Required"


class AuthorizationException(SmartException):
    """Raised when authorization fails."""

    error_type = "authorization_error"
    status_code = 403
    title = "Permission Denied"


class NotFoundException(SmartException):
    """Raised when a resource is not found."""

    error_type = "not_found"
    status_code = 404
    title = "Resource Not Found"


class ConflictException(SmartException):
    """Raised when a resource conflict occurs."""

    error_type = "conflict"
    status_code = 409
    title = "Resource Conflict"


class RateLimitException(SmartException):
    """Raised when rate limit is exceeded."""

    error_type = "rate_limit_exceeded"
    status_code = 429
    title = "Rate Limit Exceeded"


class InternalServerException(SmartException):
    """Raised when an internal server error occurs."""

    error_type = "internal_error"
    status_code = 500
    title = "Internal Server Error"


class ServiceUnavailableException(SmartException):
    """Raised when a service is unavailable."""

    error_type = "service_unavailable"
    status_code = 503
    title = "Service Unavailable"


class BadRequestException(SmartException):
    """Raised when a bad request is made."""

    error_type = "bad_request"
    status_code = 400
    title = "Bad Request"
