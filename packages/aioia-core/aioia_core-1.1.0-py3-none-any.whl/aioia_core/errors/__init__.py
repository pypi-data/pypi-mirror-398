"""
Error handling infrastructure for AIoIA projects.

Provides standardized error codes and responses for FastAPI applications.
"""

# Error codes
from aioia_core.errors.error_codes import (
    DATABASE_ERROR,
    EXTERNAL_SERVICE_ERROR,
    FORBIDDEN,
    INTERNAL_SERVER_ERROR,
    INVALID_JSON,
    INVALID_QUERY_PARAMS,
    INVALID_TOKEN,
    JWT_SECRET_NOT_CONFIGURED,
    MISSING_REQUIRED_FIELD,
    RESOURCE_CREATION_FAILED,
    RESOURCE_DELETE_FAILED,
    RESOURCE_NOT_FOUND,
    RESOURCE_UPDATE_FAILED,
    TOKEN_EXPIRED,
    UNAUTHORIZED,
    VALIDATION_ERROR,
)

# Error responses
from aioia_core.errors.error_responses import (
    ErrorResponse,
    extract_error_code_from_exception,
    get_error_detail_from_exception,
)

__all__ = [
    # Error codes
    "UNAUTHORIZED",
    "FORBIDDEN",
    "INVALID_TOKEN",
    "TOKEN_EXPIRED",
    "JWT_SECRET_NOT_CONFIGURED",
    "VALIDATION_ERROR",
    "INVALID_JSON",
    "MISSING_REQUIRED_FIELD",
    "INVALID_QUERY_PARAMS",
    "RESOURCE_NOT_FOUND",
    "RESOURCE_CREATION_FAILED",
    "RESOURCE_UPDATE_FAILED",
    "RESOURCE_DELETE_FAILED",
    "INTERNAL_SERVER_ERROR",
    "DATABASE_ERROR",
    "EXTERNAL_SERVICE_ERROR",
    # Error responses
    "ErrorResponse",
    "extract_error_code_from_exception",
    "get_error_detail_from_exception",
]
