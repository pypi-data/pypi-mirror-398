# smart-errors

> Standardized error handling for Smart Platform FastAPI services

## Installation

```bash
pip install smart-errors
```

Or with uv:
```bash
uv add smart-errors
```

## Quick Start

```python
from fastapi import FastAPI
from mehdashti_errors import setup_error_handlers, NotFoundException

app = FastAPI()

# Setup error handlers (must be called early)
setup_error_handlers(app)

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await find_user(user_id)
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    return user
```

## Features

- ✅ **Problem Details Format**: Compatible with RFC 7807 and `@smart/contracts`
- ✅ **Correlation ID**: Automatic correlation ID extraction/generation
- ✅ **Field Validation**: Converts Pydantic errors to standardized format
- ✅ **Logging Integration**: Structured logging with loguru
- ✅ **Type Safe**: Full typing support with Pydantic v2

## Error Response Format

All errors follow this standardized format:

```json
{
  "type": "not_found",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "User abc-123 not found",
  "instance": "/api/users/abc-123",
  "correlation_id": "xyz-789"
}
```

### Validation Errors

```json
{
  "type": "validation_error",
  "title": "Validation Failed",
  "status": 422,
  "detail": "One or more fields failed validation: 2 error(s)",
  "instance": "/api/users",
  "correlation_id": "xyz-789",
  "errors": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "code": "value_error.email"
    },
    {
      "field": "age",
      "message": "ensure this value is greater than 0",
      "code": "value_error.number.not_gt"
    }
  ]
}
```

## Available Exceptions

| Exception | Status | Error Type |
|-----------|--------|------------|
| `ValidationException` | 422 | `validation_error` |
| `AuthenticationException` | 401 | `authentication_error` |
| `AuthorizationException` | 403 | `authorization_error` |
| `NotFoundException` | 404 | `not_found` |
| `ConflictException` | 409 | `conflict` |
| `RateLimitException` | 429 | `rate_limit_exceeded` |
| `BadRequestException` | 400 | `bad_request` |
| `InternalServerException` | 500 | `internal_error` |
| `ServiceUnavailableException` | 503 | `service_unavailable` |

## Usage Examples

### Basic Exception

```python
from mehdashti_errors import NotFoundException

@app.get("/posts/{post_id}")
async def get_post(post_id: str):
    post = await db.get_post(post_id)
    if not post:
        raise NotFoundException(f"Post {post_id} not found")
    return post
```

### With Field Errors

```python
from mehdashti_errors import ValidationException, FieldError

@app.post("/users")
async def create_user(user_data: dict):
    errors = []

    if not user_data.get("email"):
        errors.append(FieldError(
            field="email",
            message="Email is required"
        ))

    if errors:
        raise ValidationException(
            detail="User validation failed",
            errors=errors
        )

    return await db.create_user(user_data)
```

### With Metadata

```python
from mehdashti_errors import ConflictException

@app.post("/users")
async def create_user(email: str):
    existing = await db.find_user_by_email(email)
    if existing:
        raise ConflictException(
            detail=f"User with email {email} already exists",
            meta={"existing_user_id": existing.id}
        )
    return await db.create_user(email)
```

## Correlation ID

The package automatically extracts correlation IDs from the `X-Correlation-Id` header. If not present, it generates a new UUID.

```python
# Client sends request with correlation ID
headers = {"X-Correlation-Id": "my-trace-id"}
response = requests.get("/api/users/123", headers=headers)

# Error response includes same correlation ID
{
  "type": "not_found",
  "status": 404,
  "correlation_id": "my-trace-id",
  ...
}
```

## Integration with Logging

All errors are automatically logged with structured context:

```python
# Logs include correlation_id, error_type, and metadata
logger.error(
    "not_found: User abc-123 not found",
    extra={
        "correlation_id": "xyz-789",
        "error_type": "not_found",
        "meta": {}
    }
)
```

## Compatibility

- **Frontend**: Works seamlessly with `@smart/contracts` error types
- **Backend**: Compatible with FastAPI 0.115+
- **Python**: Requires Python 3.11+

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
pytest

# Type checking
mypy smart_errors
```

## License

MIT
