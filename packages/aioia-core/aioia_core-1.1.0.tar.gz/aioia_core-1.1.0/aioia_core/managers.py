"""
Deprecated: Use aioia_core.repositories instead.

This module provides backwards compatibility aliases for the renamed repository classes.
All classes have been renamed from *Manager to *Repository to follow industry standards.

Migration guide:
    # Old (deprecated)
    from aioia_core.managers import BaseManager

    # New (recommended)
    from aioia_core.repositories import BaseRepository
"""

from __future__ import annotations

import warnings

# Re-export from repositories module
from aioia_core.repositories import (
    BaseRepository,
    CreateSchemaType,
    DBModelType,
    ModelType,
    UpdateSchemaType,
)

# Issue deprecation warning when module is imported
warnings.warn(
    "aioia_core.managers module is deprecated. "
    "Use aioia_core.repositories instead (BaseManager -> BaseRepository)",
    DeprecationWarning,
    stacklevel=2,
)

# Explicit alias for type checkers and static analysis
BaseManager = BaseRepository

__all__ = [
    # Deprecated alias (backwards compatibility)
    "BaseManager",
    # Re-exported types for compatibility
    "ModelType",
    "DBModelType",
    "CreateSchemaType",
    "UpdateSchemaType",
]
