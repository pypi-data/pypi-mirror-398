"""
CRUD repository protocol definition for AIoIA projects.

Defines the interface for generic CRUD operations.
"""

from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType_contra = TypeVar(
    "CreateSchemaType_contra", bound=BaseModel, contravariant=True
)
UpdateSchemaType_contra = TypeVar(
    "UpdateSchemaType_contra", bound=BaseModel, contravariant=True
)


class CrudRepositoryProtocol(  # pylint: disable=unnecessary-ellipsis,redundant-returns-doc
    Protocol, Generic[ModelType, CreateSchemaType_contra, UpdateSchemaType_contra]
):
    """
    Protocol defining the basic CRUD operations interface.

    This protocol defines the interface for basic CRUD (Create, Read, Update, Delete)
    operations. All CRUD repositories must implement this protocol.

    Note: Protocol methods use ellipsis (...) as body, which is required by type checkers
    (pyright) to validate return types. Pylint's unnecessary-ellipsis warning is disabled
    for this valid use case.
    """

    def get_by_id(self, item_id: str) -> ModelType | None:
        """
        Retrieve an item by its ID.

        Args:
            item_id: Unique identifier of the item to retrieve

        Returns:
            The found item or None if not found
        """
        ...

    def get_all(
        self,
        current: int = 1,
        page_size: int = 10,
        sort: list[tuple[str, str]] | None = None,
        filters: list[dict[str, Any]] | None = None,
    ) -> tuple[list[ModelType], int]:
        """
        Retrieve all items with pagination, sorting, and filtering.

        Args:
            current: Current page number (1-indexed)
            page_size: Number of items per page
            sort: Sort criteria as [(field, order), ...] where order is 'asc' or 'desc'
                Example: [('created_at', 'desc'), ('name', 'asc')]
            filters: Filter conditions as [{'field': str, 'operator': str, 'value': Any}, ...]
                Supported operators: eq, ne, contains, gt, gte, lt, lte, in, null, nnull, or, and
                Example: [{'field': 'status', 'operator': 'eq', 'value': 'active'}]

        Returns:
            Tuple of (list of items, total count)
        """
        ...

    def create(self, schema: CreateSchemaType_contra) -> ModelType:
        """
        Create a new item.

        Args:
            schema: Data for the new item

        Returns:
            The created item
        """
        ...

    def update(self, item_id: str, schema: UpdateSchemaType_contra) -> ModelType | None:
        """
        Update an existing item.

        Args:
            item_id: Unique identifier of the item to update
            schema: Data to update

        Returns:
            The updated item or None if not found
        """
        ...

    def delete(self, item_id: str) -> bool:
        """
        Delete an item.

        In case of exceptions such as database constraint violations,
        the exception should be propagated as-is.

        Args:
            item_id: Unique identifier of the item to delete

        Returns:
            True if deletion succeeded, False if item not found
        """
        ...


class DatabaseRepositoryProtocol(
    CrudRepositoryProtocol[ModelType, CreateSchemaType_contra, UpdateSchemaType_contra],
    Protocol,
):
    """
    Protocol for database repositories using SQLAlchemy sessions.

    This protocol extends CrudRepositoryProtocol to define the interface for repositories
    that use database sessions.
    """

    def __init__(self, db_session: Session) -> None:
        """
        Initialize database repository.

        Args:
            db_session: SQLAlchemy database session
        """


RepositoryType = TypeVar("RepositoryType", bound=CrudRepositoryProtocol)


# Deprecated aliases for backwards compatibility
CrudManagerProtocol = CrudRepositoryProtocol
DatabaseManagerProtocol = DatabaseRepositoryProtocol

# TypeVar aliases need to be redefined (cannot alias TypeVar directly)
ManagerType = TypeVar("ManagerType", bound=CrudRepositoryProtocol)

# For re-export compatibility, also export ModelType
__all__ = [
    # New names (recommended)
    "CrudRepositoryProtocol",
    "DatabaseRepositoryProtocol",
    "RepositoryType",
    "ModelType",
    # Deprecated aliases (backwards compatibility)
    "CrudManagerProtocol",
    "DatabaseManagerProtocol",
    "ManagerType",
]
