"""
Error Response Models

Pydantic models for standardized error responses.
Compatible with @smart/contracts ErrorResponse format.
"""

from typing import Any

from pydantic import BaseModel, Field


class FieldError(BaseModel):
    """Field-level validation error."""

    field: str = Field(..., description="Field name or path (e.g., 'email', 'address.city')")
    message: str = Field(..., description="Error message for this field")
    code: str | None = Field(None, description="Error code for programmatic handling")


class ErrorResponse(BaseModel):
    """
    Standard error response format (Problem Details).

    Compatible with @smart/contracts ErrorResponse.
    """

    type: str = Field(..., description="Error type identifier")
    title: str = Field(..., description="Short human-readable summary")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Detailed explanation of the error")
    instance: str = Field(..., description="URI reference identifying the specific occurrence")
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    errors: list[FieldError] | None = Field(None, description="Field-level validation errors")
    meta: dict[str, Any] | None = Field(None, description="Additional error metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "validation_error",
                "title": "Validation Failed",
                "status": 422,
                "detail": "One or more fields failed validation",
                "instance": "/api/users",
                "correlation_id": "abc-123",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                    }
                ],
            }
        }
    }
