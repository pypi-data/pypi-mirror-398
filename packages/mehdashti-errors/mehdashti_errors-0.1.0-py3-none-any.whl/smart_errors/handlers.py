"""
Exception Handlers

Global exception handlers for FastAPI that convert exceptions to
standardized ErrorResponse format.
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from smart_observability import get_correlation_id as get_context_correlation_id
from smart_observability import generate_correlation_id

from .exceptions import SmartException
from .models import ErrorResponse, FieldError


def get_correlation_id(request: Request) -> str:
    """
    Get correlation ID from context or generate new one.

    First tries to get the correlation ID from the context (set by CorrelationMiddleware).
    If not found, extracts from request headers or generates a new one.

    Args:
        request: FastAPI request object

    Returns:
        Correlation ID string
    """
    # Try to get from context first (set by CorrelationMiddleware)
    context_id = get_context_correlation_id()
    if context_id:
        return context_id

    # Fallback: extract from headers or generate
    return request.headers.get("x-correlation-id", generate_correlation_id())


def create_error_response(
    error_type: str,
    title: str,
    status_code: int,
    detail: str,
    instance: str,
    correlation_id: str,
    errors: list[FieldError] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create standardized error response dict.

    Args:
        error_type: Error type identifier
        title: Short summary
        status_code: HTTP status code
        detail: Detailed message
        instance: Request path
        correlation_id: Correlation ID
        errors: Optional field errors
        meta: Optional metadata

    Returns:
        Error response dictionary
    """
    response = ErrorResponse(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
        errors=errors,
        meta=meta,
    )
    return response.model_dump(exclude_none=True)


def setup_error_handlers(app: FastAPI) -> None:
    """
    Register standardized exception handlers for FastAPI app.

    This function sets up handlers for:
    - SmartException and its subclasses
    - RequestValidationError (Pydantic validation)
    - Generic Exception (catch-all)

    Args:
        app: FastAPI application instance

    Example:
        ```python
        from fastapi import FastAPI
        from smart_errors import setup_error_handlers

        app = FastAPI()
        setup_error_handlers(app)
        ```
    """

    @app.exception_handler(SmartException)
    async def smart_exception_handler(request: Request, exc: SmartException) -> JSONResponse:
        """Handle Smart Platform custom exceptions."""
        correlation_id = get_correlation_id(request)

        logger.error(
            f"{exc.error_type}: {exc.detail}",
            extra={
                "correlation_id": correlation_id,
                "error_type": exc.error_type,
                "meta": exc.meta,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=create_error_response(
                error_type=exc.error_type,
                title=exc.title,
                status_code=exc.status_code,
                detail=exc.detail,
                instance=request.url.path,
                correlation_id=correlation_id,
                errors=exc.errors,
                meta=exc.meta,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle FastAPI/Pydantic validation errors."""
        correlation_id = get_correlation_id(request)

        # Convert Pydantic errors to FieldError format
        field_errors = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"][1:])  # Skip 'body'
            field_errors.append(
                FieldError(
                    field=field_path,
                    message=error["msg"],
                    code=error["type"],
                )
            )

        logger.warning(
            f"Validation error: {len(field_errors)} field(s) failed",
            extra={"correlation_id": correlation_id, "errors": field_errors},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=create_error_response(
                error_type="validation_error",
                title="Validation Failed",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"One or more fields failed validation: {len(field_errors)} error(s)",
                instance=request.url.path,
                correlation_id=correlation_id,
                errors=field_errors,
            ),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        correlation_id = get_correlation_id(request)

        logger.exception(
            f"Unexpected error: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "exception_type": exc.__class__.__name__,
            },
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=create_error_response(
                error_type="internal_error",
                title="Internal Server Error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred. Please try again later.",
                instance=request.url.path,
                correlation_id=correlation_id,
                meta={"exception_type": exc.__class__.__name__},
            ),
        )
