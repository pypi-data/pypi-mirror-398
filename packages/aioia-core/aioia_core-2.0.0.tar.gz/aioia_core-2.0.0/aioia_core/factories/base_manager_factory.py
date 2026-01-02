"""
Deprecated: Use aioia_core.factories.base_repository_factory instead.

This module provides backwards compatibility aliases for the renamed factory classes.
All classes have been renamed from *ManagerFactory to *RepositoryFactory to follow
industry standards.

Migration guide:
    # Old (deprecated)
    from aioia_core.factories.base_manager_factory import BaseManagerFactory

    # New (recommended)
    from aioia_core.factories.base_repository_factory import BaseRepositoryFactory
"""

from __future__ import annotations

import warnings
from typing import TypeVar

# Re-export from base_repository_factory module
from aioia_core.factories.base_repository_factory import BaseRepositoryFactory
from aioia_core.protocols import DatabaseRepositoryProtocol

# TypeVar for backwards compatibility (cannot alias TypeVar directly)
ManagerType = TypeVar("ManagerType", bound=DatabaseRepositoryProtocol)

# Issue deprecation warning when module is imported
warnings.warn(
    "aioia_core.factories.base_manager_factory module is deprecated. "
    "Use aioia_core.factories.base_repository_factory instead",
    DeprecationWarning,
    stacklevel=2,
)

# Explicit aliases for type checkers and static analysis
BaseManagerFactory = BaseRepositoryFactory

__all__ = [
    # Deprecated aliases (backwards compatibility)
    "BaseManagerFactory",
    "ManagerType",  # TypeVar for backwards compatibility
]
