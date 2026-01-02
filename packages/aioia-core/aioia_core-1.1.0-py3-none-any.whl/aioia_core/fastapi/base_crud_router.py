import json
import warnings
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

import sentry_sdk
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from humps import decamelize
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from aioia_core.auth import UserInfoProvider, UserRole
from aioia_core.factories import BaseRepositoryFactory
from aioia_core.errors import (
    FORBIDDEN,
    INVALID_QUERY_PARAMS,
    INVALID_TOKEN,
    RESOURCE_CREATION_FAILED,
    RESOURCE_NOT_FOUND,
    RESOURCE_UPDATE_FAILED,
    ErrorResponse,
)
from aioia_core.protocols import DatabaseRepositoryProtocol, ModelType, RepositoryType

# TypeVar for _create_repository_dependency_from_factory method
FactoryRepositoryType = TypeVar("FactoryRepositoryType", bound=DatabaseRepositoryProtocol)

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


class PaginatedResponse(BaseModel, Generic[ModelType]):
    """Generic paginated response model"""

    data: list[ModelType]
    total: int


class SingleItemResponse(BaseModel, Generic[ModelType]):
    """Generic single item response model"""

    data: ModelType


class DeleteResponse(BaseModel):
    """Delete operation response model"""

    data: dict[str, Any]


# TypeVar design decision: No contravariance for concrete router implementation
#
# Contravariance is required for Protocol definitions (interfaces) to enable
# correct subtype relationships in Protocol parameters. However, concrete generic
# classes like BaseCrudRouter do NOT need contravariance because:
#
# 1. YAGNI (You Aren't Gonna Need It): Contravariance adds complexity without
#    providing value for concrete implementations. The router binds to specific
#    types at instantiation.
#
# 2. Simplicity: Invariant TypeVars are easier to understand and reason about.
#    Type checker errors are clearer when variance doesn't come into play.
#
# 3. Occam's Razor: The simplest solution that works is preferable. Original
#    implementation worked fine without contravariance.
#
# Note: aioia_core/protocols.py DOES use contravariance for Protocol definitions,
# which is correct per PEP 544. The distinction is: Protocols (interfaces) need
# contravariance, concrete classes (implementations) don't.
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCrudRouter(
    Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]
):
    # pylint: disable=too-many-instance-attributes
    """
    Base FastAPI CRUD router with JWT authentication and admin authorization.

    This base class provides complete CRUD operations that require admin privileges.
    All endpoints are protected by both JWT authentication and admin role verification.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        model_class: type[ModelType],
        create_schema: type[CreateSchemaType],
        update_schema: type[UpdateSchemaType],
        db_session_factory: sessionmaker,
        role_provider: UserInfoProvider | None,
        jwt_secret_key: str | None,
        resource_name: str,
        tags: Sequence[str],
        repository_factory=None,
        manager_factory=None,  # Deprecated
    ):
        """
        Initialize the CRUD router with concrete schema types and admin authentication.

        Args:
            model_class: The Pydantic model class for responses
            create_schema: The Pydantic schema class for create operations
            update_schema: The Pydantic schema class for update operations
            db_session_factory: SQLAlchemy session factory
            repository_factory: Factory for creating database repositories
            role_provider: Provider for user role lookup (None = no auth)
            jwt_secret_key: JWT secret key for authentication
            resource_name: Name of the resource (for URLs and error messages)
            tags: OpenAPI tags for the endpoints
            manager_factory: (Deprecated) Use repository_factory instead
        """
        # Handle backwards compatibility
        if manager_factory is not None and repository_factory is None:
            warnings.warn(
                "manager_factory parameter is deprecated, use repository_factory instead",
                DeprecationWarning,
                stacklevel=2,
            )
            repository_factory = manager_factory
        elif manager_factory is not None and repository_factory is not None:
            raise ValueError("Cannot specify both manager_factory and repository_factory")

        if repository_factory is None:
            raise ValueError("repository_factory is required")

        self.model_class = model_class
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.db_session_factory = db_session_factory
        self.repository_factory = repository_factory
        self.role_provider = role_provider
        self.jwt_secret_key = jwt_secret_key
        self.resource_name = resource_name
        self.router = APIRouter(tags=list(tags))

        # Create dependency functions to avoid 'self' in FastAPI dependencies
        self._create_auth_dependencies()

        # Register routes
        self._register_routes()

    def _create_auth_dependencies(self):
        """Create dependency functions that FastAPI can properly handle"""

        def get_db():
            """Database session dependency"""
            db = self.db_session_factory()
            try:
                yield db
            finally:
                db.close()

        def get_user_id_from_token(
            credentials: HTTPAuthorizationCredentials
            | None = Depends(optional_security),
        ) -> str | None:
            """
            Decodes JWT and returns user_id.
            - Returns user_id if token is valid.
            - Returns None if no token is provided.
            - Raises HTTPException for invalid tokens.
            """
            if not self.jwt_secret_key:
                # Silently fail if key is not configured to avoid breaking public access
                return None
            if not credentials:
                return None

            try:
                payload = jwt.decode(
                    credentials.credentials, self.jwt_secret_key, algorithms=["HS256"]
                )
                user_id: str | None = payload.get("sub")
                if user_id is None:
                    raise JWTError("No 'sub' claim in token")
                return user_id
            except JWTError as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "detail": "Invalid authentication credentials",
                        "code": INVALID_TOKEN,
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc

        def get_current_user_role(
            user_id: str | None = Depends(get_user_id_from_token),
            db: Session = Depends(get_db),
        ) -> UserRole | None:
            """
            Gets the user's role from the database based on user_id from token.
            Also sets user context for monitoring/observability tools.
            - Raises 401 if user_id from token does not exist in the DB.
            """
            if not user_id:
                return None

            if not self.role_provider:
                # No role provider = no authorization check
                return None

            user_info = self.role_provider.get_user_info(user_id, db)
            if user_info is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "detail": "User associated with token not found",
                        "code": INVALID_TOKEN,
                    },
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Set user context for monitoring tools (Sentry, DataDog, etc.)
            sentry_user = {
                "id": user_info.user_id,
                "username": user_info.username,
            }
            if user_info.email is not None:
                sentry_user["email"] = user_info.email
            sentry_sdk.set_user(sentry_user)

            return user_info.role

        def get_admin_user(
            user_id: str | None = Depends(get_user_id_from_token),
            role: UserRole | None = Depends(get_current_user_role),
        ) -> str:
            """
            Admin authorization dependency - requires admin role.
            Returns the admin user's ID if authorized.
            """
            if role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "detail": "Admin access required",
                        "code": FORBIDDEN,
                    },
                )
            # get_current_user_role ensures user_id is str when role is ADMIN
            assert user_id is not None, "Admin user must have user_id"
            return user_id

        def get_repository(db: Session = Depends(get_db)) -> RepositoryType:
            """Repository dependency with simplified DB session handling"""
            return self.repository_factory.create_repository(db)

        # Store as instance attributes
        self.get_db_dep = get_db
        self.get_current_user_role_dep = get_current_user_role
        self.get_admin_user_dep = get_admin_user
        self._get_repository_dep = get_repository
        self.get_current_user_id_dep = get_user_id_from_token

    @property
    def get_repository_dep(self):
        """Dependency function for getting repository instance."""
        return self._get_repository_dep

    @property
    def get_manager_dep(self):
        """Deprecated alias for get_repository_dep. Use get_repository_dep instead."""
        warnings.warn(
            "get_manager_dep is deprecated. Use get_repository_dep instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._get_repository_dep

    def _create_repository_dependency_from_factory(
        self, factory: BaseRepositoryFactory[FactoryRepositoryType]
    ) -> Callable[..., FactoryRepositoryType]:
        """
        Create a FastAPI dependency from a repository factory.

        This allows creating dependencies for additional repositories (e.g., StudioRepository)
        that share the same DB session with the primary repository.

        Args:
            factory (BaseRepositoryFactory[FactoryRepositoryType]): A repository factory instance.

        Returns:
            A FastAPI dependency function that returns the repository instance.

        Example:
            self.get_studio_repository_dep = self._create_repository_dependency_from_factory(
                studio_repository_factory
            )
        """

        def repository_dependency(db: Session = Depends(self.get_db_dep)):
            return factory.create_repository(db)

        return repository_dependency

    def _register_routes(self) -> None:
        """Register all CRUD routes with concrete type annotations"""
        self._register_list_route()
        self._register_create_route()
        self._register_get_route()
        self._register_update_route()
        self._register_delete_route()
        self._register_custom_routes()

    def _register_list_route(self) -> None:
        """Register list/pagination route with concrete type annotations"""

        model_class = self.model_class

        # Create response model with concrete type using proper Pydantic model creation
        class PaginatedResponseModel(BaseModel):
            data: list[model_class]  # type: ignore
            total: int

        @self.router.get(
            f"/{self.resource_name}",
            response_model=PaginatedResponseModel,
            summary=f"List {self.resource_name.title()} (Admin Only)",
            description=f"Retrieve a paginated list of {self.resource_name}. Requires admin privileges.",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication failed"},
                422: {"model": ErrorResponse, "description": "Validation error"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def list_items(
            current: int = Query(1, ge=1, description="Current page number"),
            page_size: int = Query(10, ge=1, le=100, description="Items per page"),
            sort_param: str
            | None = Query(
                None,
                alias="sort",
                description='Sorting criteria in JSON format. Array of [field, order] pairs. Example: [["createdAt","desc"], ["name","asc"]]',
                example='[["createdAt","desc"]]',
            ),
            filters_param: str
            | None = Query(
                None,
                alias="filters",
                description="Filter conditions (JSON format)",
            ),
            _admin_user: None = Depends(self.get_admin_user_dep),
            repository: RepositoryType = Depends(self.get_repository_dep),
        ):
            sort_list, filter_list = self._parse_query_params(sort_param, filters_param)

            items, total = repository.get_all(
                current=current,
                page_size=page_size,
                sort=sort_list,
                filters=filter_list,
            )
            return PaginatedResponseModel(data=items, total=total)

    def _register_create_route(
        self,
        auth_dependency: Callable[..., str] | None = None,
    ) -> None:
        """
        Register create route with concrete type annotations.

        Args:
            auth_dependency: Custom authentication dependency. If None, uses admin-only auth.
                           Must return user_id (str) on success, or raise HTTPException on failure.
        """
        # Use admin-only auth by default
        if auth_dependency is None:
            auth_dependency = self.get_admin_user_dep

        model_class = self.model_class
        create_schema_class = self.create_schema

        # Create response model with concrete type using proper Pydantic model creation
        class SingleItemResponseModel(BaseModel):
            data: model_class  # type: ignore

        @self.router.post(
            f"/{self.resource_name}",
            response_model=SingleItemResponseModel,
            status_code=status.HTTP_201_CREATED,
            summary=f"Create {self.resource_name.title()}",
            description=f"Create a new {self.resource_name} record.",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication failed"},
                422: {"model": ErrorResponse, "description": "Validation error"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def create_item(
            item_data: create_schema_class = Body(...),  # type: ignore
            repository: RepositoryType = Depends(self.get_repository_dep),
            _auth: str = Depends(auth_dependency),
        ):
            created_item = repository.create(item_data)
            if not created_item:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "detail": f"Failed to create {self.resource_name}",
                        "code": RESOURCE_CREATION_FAILED,
                    },
                )
            return SingleItemResponseModel(data=created_item)

    def _register_get_route(self) -> None:
        """Register single item get route with concrete type annotations"""

        model_class = self.model_class

        # Create response model with concrete type using proper Pydantic model creation
        class SingleItemResponseModel(BaseModel):
            data: model_class  # type: ignore

        @self.router.get(
            f"/{self.resource_name}/{{item_id}}",
            response_model=SingleItemResponseModel,
            summary=f"Get {self.resource_name.title()} (Admin Only)",
            description=f"Retrieve a specific {self.resource_name} by ID. Requires admin privileges.",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication failed"},
                404: {"model": ErrorResponse, "description": "Resource not found"},
                422: {"model": ErrorResponse, "description": "Validation error"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def get_item(
            item_id: str,
            _admin_user: None = Depends(self.get_admin_user_dep),
            repository: RepositoryType = Depends(self.get_repository_dep),
        ):
            item = self._get_item_or_404(repository, item_id)
            return SingleItemResponseModel(data=item)

    def _register_update_route(self) -> None:
        """Register update route with concrete type annotations"""

        model_class = self.model_class
        update_schema_class = self.update_schema

        # Create response model with concrete type using proper Pydantic model creation
        class SingleItemResponseModel(BaseModel):
            data: model_class  # type: ignore

        @self.router.patch(
            f"/{self.resource_name}/{{item_id}}",
            response_model=SingleItemResponseModel,
            summary=f"Update {self.resource_name.title()} (Admin Only)",
            description=f"Partially update a specific {self.resource_name} by ID. Only provided fields will be updated. Requires admin privileges.",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication failed"},
                404: {"model": ErrorResponse, "description": "Resource not found"},
                422: {"model": ErrorResponse, "description": "Validation error"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def update_item(
            item_id: str,
            item_data: update_schema_class = Body(...),  # type: ignore
            _admin_user: None = Depends(self.get_admin_user_dep),
            repository: RepositoryType = Depends(self.get_repository_dep),
        ):
            updated_item = repository.update(item_id, item_data)
            if not updated_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "detail": f"{self.resource_name.title()} not found or update failed: {item_id}",
                        "code": RESOURCE_UPDATE_FAILED,
                    },
                )
            return SingleItemResponseModel(data=updated_item)

    def _register_delete_route(self) -> None:
        """Register delete route"""

        @self.router.delete(
            f"/{self.resource_name}/{{item_id}}",
            response_model=DeleteResponse,
            status_code=status.HTTP_200_OK,
            summary=f"Delete {self.resource_name.title()} (Admin Only)",
            description=f"Delete a specific {self.resource_name} by ID. Requires admin privileges.",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication failed"},
                404: {"model": ErrorResponse, "description": "Resource not found"},
                422: {"model": ErrorResponse, "description": "Validation error"},
                500: {"model": ErrorResponse, "description": "Internal server error"},
            },
        )
        async def delete_item(
            item_id: str,
            _admin_user: None = Depends(self.get_admin_user_dep),
            repository: RepositoryType = Depends(self.get_repository_dep),
        ):
            if not repository.delete(item_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "detail": f"{self.resource_name.title()} not found or already deleted: {item_id}",
                        "code": RESOURCE_NOT_FOUND,
                    },
                )

            return DeleteResponse(
                data={
                    "id": item_id,
                    "type": self.resource_name,
                    "metadata": {
                        "deletedAt": datetime.now(timezone.utc).isoformat(),
                    },
                }
            )

    def _get_item_or_404(self, repository: RepositoryType, item_id: str) -> ModelType:
        """Get item by ID or raise 404 HTTPException if not found."""
        item = repository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"{self.resource_name.title()} not found: {item_id}",
                    "code": RESOURCE_NOT_FOUND,
                },
            )
        return item

    def _decamelize_filter_fields(
        self, filters: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Recursively traverses the filter structure and decamelizes field names."""
        processed_filters = []
        for filter_item in filters:
            # Conditional Filter (or/and)
            if (
                filter_item.get("operator") in {"or", "and"}
                and "value" in filter_item
                and isinstance(filter_item["value"], list)
            ):
                processed_filters.append(
                    {
                        **filter_item,
                        "value": self._decamelize_filter_fields(filter_item["value"]),
                    }
                )
            # Logical Filter
            elif "field" in filter_item:
                processed_filters.append(
                    {
                        **filter_item,
                        "field": decamelize(str(filter_item["field"])),
                    }
                )
            # Unrecognized filter structure, append as is
            else:
                processed_filters.append(filter_item)

        return processed_filters

    def _parse_query_params(
        self, sort_param: str | None, filters_param: str | None
    ) -> tuple[list | None, list | None]:
        """Parse and validate query parameters"""
        sort_list = None
        filter_list = None

        if sort_param:
            try:
                sort_data = json.loads(sort_param)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "'sort' parameter must be a valid JSON string",
                        "code": INVALID_QUERY_PARAMS,
                    },
                ) from e

            if not (
                isinstance(sort_data, list)
                and all(
                    isinstance(item, list)
                    and len(item) == 2
                    and isinstance(item[0], str)
                    and item[1] in {"asc", "desc"}
                    for item in sort_data
                )
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": '\'sort\' parameter format must be [["field", "asc|desc"], ...]. Example: [["name", "asc"], ["createdAt", "desc"]]',
                        "code": INVALID_QUERY_PARAMS,
                    },
                )

            sort_list = [(decamelize(s[0]), s[1]) for s in sort_data]

        if filters_param:
            try:
                filter_data = json.loads(filters_param)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "'filters' parameter must be a valid JSON string",
                        "code": INVALID_QUERY_PARAMS,
                    },
                ) from e

            if not isinstance(filter_data, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "detail": "'filters' parameter must be a list of filter objects.",
                        "code": INVALID_QUERY_PARAMS,
                    },
                )

            filter_list = self._decamelize_filter_fields(filter_data)

        return sort_list, filter_list

    def _register_custom_routes(self) -> None:
        """Register custom routes. Override in subclasses if needed."""

    def get_router(self) -> APIRouter:
        """Get the configured router"""
        return self.router
