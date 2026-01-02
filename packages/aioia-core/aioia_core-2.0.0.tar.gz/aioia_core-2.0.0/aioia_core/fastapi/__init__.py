"""FastAPI utilities for AIoIA projects."""

from aioia_core.fastapi.base_crud_router import (
    BaseCrudRouter,
    DeleteResponse,
    PaginatedResponse,
    SingleItemResponse,
)

__all__ = [
    "BaseCrudRouter",
    "PaginatedResponse",
    "SingleItemResponse",
    "DeleteResponse",
]
