"""
smart-errors

Standardized error handling for Smart Platform FastAPI services.
Implements Problem Details (RFC 7807) format compatible with @smart/contracts.
"""

from .exceptions import (
    SmartException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ConflictException,
    RateLimitException,
    InternalServerException,
    ServiceUnavailableException,
    BadRequestException,
)
from .handlers import setup_error_handlers
from .models import ErrorResponse, FieldError

__version__ = "0.0.1"

__all__ = [
    # Exceptions
    "SmartException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "NotFoundException",
    "ConflictException",
    "RateLimitException",
    "InternalServerException",
    "ServiceUnavailableException",
    "BadRequestException",
    # Handlers
    "setup_error_handlers",
    # Models
    "ErrorResponse",
    "FieldError",
]
