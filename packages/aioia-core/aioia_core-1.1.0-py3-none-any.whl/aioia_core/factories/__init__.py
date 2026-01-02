"""Factory patterns for AIoIA projects."""

from aioia_core.factories.base_repository_factory import BaseRepositoryFactory

# Deprecated alias for backwards compatibility
from aioia_core.factories.base_manager_factory import BaseManagerFactory

__all__ = [
    # New name (recommended)
    "BaseRepositoryFactory",
    # Deprecated alias (backwards compatibility)
    "BaseManagerFactory",
]
