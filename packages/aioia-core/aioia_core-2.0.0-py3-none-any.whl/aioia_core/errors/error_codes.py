# Error codes for consistent error handling across FastAPI endpoints
# These constants ensure standardized error identification for frontend applications

# Authentication & Authorization errors
UNAUTHORIZED = "UNAUTHORIZED"  # User is not authenticated
FORBIDDEN = "FORBIDDEN"  # User lacks permission for the requested resource
INVALID_TOKEN = "INVALID_TOKEN"  # JWT token is invalid or malformed
TOKEN_EXPIRED = "TOKEN_EXPIRED"  # JWT token has expired
JWT_SECRET_NOT_CONFIGURED = "JWT_SECRET_NOT_CONFIGURED"  # Server configuration error

# Validation & Request errors
VALIDATION_ERROR = "VALIDATION_ERROR"  # Request data validation failed
INVALID_JSON = "INVALID_JSON"  # Request body contains invalid JSON
MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"  # Required field is missing
INVALID_QUERY_PARAMS = "INVALID_QUERY_PARAMS"  # Query parameters are invalid

# Resource Management errors
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"  # Requested resource does not exist
RESOURCE_CREATION_FAILED = "RESOURCE_CREATION_FAILED"  # Failed to create resource
RESOURCE_UPDATE_FAILED = "RESOURCE_UPDATE_FAILED"  # Failed to update resource
RESOURCE_DELETE_FAILED = "RESOURCE_DELETE_FAILED"  # Failed to delete resource

# System & Server errors
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"  # Unexpected server error
DATABASE_ERROR = "DATABASE_ERROR"  # Database operation failed
EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"  # External service unavailable
