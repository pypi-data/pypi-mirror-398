from __future__ import annotations

import warnings
from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy.orm import Session, sessionmaker

from aioia_core.protocols import DatabaseRepositoryProtocol

# RepositoryType을 DatabaseRepositoryProtocol에 바인딩
RepositoryType = TypeVar("RepositoryType", bound=DatabaseRepositoryProtocol)


class BaseRepositoryFactory(ABC, Generic[RepositoryType]):
    """
    기본 레포지토리 팩토리 클래스

    이 클래스는 데이터베이스 저장소를 사용하는 레포지토리 인스턴스를 생성하기 위한
    기본 팩토리 패턴을 구현합니다.

    Args:
        repository_class: 생성할 레포지토리 클래스
        db_session_factory: SQLAlchemy 세션 팩토리 (선택적, 독립 사용 시 필요)
    """

    def __init__(
        self,
        *,
        repository_class: type[RepositoryType],
        db_session_factory: sessionmaker | None = None,
    ):
        """
        BaseRepositoryFactory 초기화

        Args:
            repository_class: 생성할 레포지토리 클래스
            db_session_factory: SQLAlchemy 세션 팩토리 (선택적, 독립 사용 시 필요)
        """
        self.repository_class = repository_class
        self.db_session_factory = db_session_factory

    def create_repository(self, db_session: Session | None = None) -> RepositoryType:
        """
        레포지토리 인스턴스를 생성합니다.

        이 메서드는 레포지토리 클래스의 인스턴스를 생성하고 반환합니다.
        db_session이 제공되지 않은 경우 db_session_factory를 사용하여 새로운 세션을 생성합니다.

        Args:
            db_session: 선택적 데이터베이스 세션. None인 경우 db_session_factory를 사용합니다.

        Returns:
            생성된 레포지토리 인스턴스

        Raises:
            ValueError: db_session이 None이고 db_session_factory도 설정되지 않은 경우
        """
        if db_session is not None:
            return self.repository_class(db_session)
        if self.db_session_factory is not None:
            return self.repository_class(self.db_session_factory())
        raise ValueError(
            "db_session is required when db_session_factory is not configured"
        )

    # Deprecated alias for backwards compatibility
    def create_manager(self, db_session: Session | None = None) -> RepositoryType:
        """
        Deprecated: Use create_repository() instead.

        This method is kept for backwards compatibility with existing code
        that uses the old BaseManagerFactory interface.
        """
        warnings.warn(
            "create_manager() is deprecated, use create_repository() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.create_repository(db_session)
