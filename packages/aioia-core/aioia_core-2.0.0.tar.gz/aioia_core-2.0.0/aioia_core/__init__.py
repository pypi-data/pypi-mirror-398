"""
AIoIA Core - Core infrastructure for AIoIA projects.

Provides:
- Database: SQLAlchemy base models and CRUD repository
- Errors: Standardized error codes and responses
- Settings: Common settings classes
"""

__version__ = "0.1.0"

from aioia_core.errors import (
    INTERNAL_SERVER_ERROR,
    RESOURCE_NOT_FOUND,
    UNAUTHORIZED,
    VALIDATION_ERROR,
    ErrorResponse,
    extract_error_code_from_exception,
    get_error_detail_from_exception,
)
from aioia_core.factories.base_repository_factory import BaseRepositoryFactory
from aioia_core.models import Base, BaseModel
from aioia_core.protocols import (
    CrudRepositoryProtocol,
    DatabaseRepositoryProtocol,
)
from aioia_core.repositories import BaseRepository
from aioia_core.settings import DatabaseSettings, JWTSettings, OpenAIAPISettings

# Deprecated imports for backwards compatibility
from aioia_core.factories.base_manager_factory import BaseManagerFactory
from aioia_core.managers import BaseManager
from aioia_core.protocols import CrudManagerProtocol, DatabaseManagerProtocol

__all__ = [
    # Database - New names (recommended)
    "Base",
    "BaseModel",
    "BaseRepository",
    "BaseRepositoryFactory",
    "CrudRepositoryProtocol",
    "DatabaseRepositoryProtocol",
    # Database - Deprecated aliases (backwards compatibility)
    "BaseManager",
    "BaseManagerFactory",
    "CrudManagerProtocol",
    "DatabaseManagerProtocol",
    # Errors
    "ErrorResponse",
    "UNAUTHORIZED",
    "VALIDATION_ERROR",
    "RESOURCE_NOT_FOUND",
    "INTERNAL_SERVER_ERROR",
    "extract_error_code_from_exception",
    "get_error_detail_from_exception",
    # Settings
    "DatabaseSettings",
    "OpenAIAPISettings",
    "JWTSettings",
]
