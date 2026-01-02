from datetime import datetime, timezone
from uuid import uuid4

from humps import camelize
from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, Integer, String, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from aioia_core.protocols import DatabaseRepositoryProtocol
from aioia_core.factories.base_repository_factory import BaseRepositoryFactory


class Base(DeclarativeBase):
    pass


class TestDBModel(Base):
    __tablename__ = "test_items"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    value: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class TestModel(BaseModel):
    model_config = ConfigDict(alias_generator=camelize, populate_by_name=True)
    id: str
    name: str
    value: int | None = None
    created_at: datetime


class TestCreate(BaseModel):
    name: str
    value: int | None = None


class TestUpdate(BaseModel):
    name: str | None = None
    value: int | None = None


class TestRepository(DatabaseRepositoryProtocol[TestModel, TestCreate, TestUpdate]):
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, item_id: str):
        obj = self.db.query(TestDBModel).filter(TestDBModel.id == item_id).first()
        if obj:
            return TestModel(
                id=str(obj.id),
                name=str(obj.name),
                value=obj.value,
                created_at=obj.created_at,
            )
        return None

    def get_all(self, current=1, page_size=10, sort=None, filters=None):
        q = self.db.query(TestDBModel)

        if filters:
            # Simplified filter handling for tests, not a full implementation
            for f in filters:
                if f["operator"] == "eq":
                    column = getattr(TestDBModel, f["field"])
                    value = f["value"]
                    if isinstance(column.type, DateTime) and isinstance(value, str):
                        value = datetime.fromisoformat(value)
                    q = q.filter(column == value)
                elif f["operator"] == "in":
                    q = q.filter(getattr(TestDBModel, f["field"]).in_(f["value"]))
                elif f["operator"] == "null":
                    q = q.filter(getattr(TestDBModel, f["field"]).is_(None))
                elif f["operator"] == "nnull":
                    q = q.filter(getattr(TestDBModel, f["field"]).isnot(None))
                elif f["operator"] == "or":
                    or_conditions = []
                    for or_f in f["value"]:
                        if or_f["operator"] == "eq":
                            or_conditions.append(
                                getattr(TestDBModel, or_f["field"]) == or_f["value"]
                            )
                    q = q.filter(or_(*or_conditions))

        if sort:
            for field, order in sort:
                column = getattr(TestDBModel, field, None)
                if column:
                    if order == "desc":
                        q = q.order_by(column.desc())
                    else:
                        q = q.order_by(column.asc())

        total = q.count()
        items = q.offset((current - 1) * page_size).limit(page_size).all()
        return [
            TestModel(
                id=str(o.id), name=str(o.name), value=o.value, created_at=o.created_at
            )
            for o in items
        ], total

    def create(self, schema: TestCreate) -> TestModel:
        new_id = str(uuid4())
        schema_data = schema.model_dump()
        obj = TestDBModel(id=new_id, **schema_data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return TestModel(
            id=str(obj.id),
            name=str(obj.name),
            value=obj.value,
            created_at=obj.created_at,
        )

    def update(self, item_id: str, schema: TestUpdate):
        obj = self.db.query(TestDBModel).filter(TestDBModel.id == item_id).first()
        if not obj:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(obj, key, value)

        self.db.commit()
        self.db.refresh(obj)
        return TestModel(
            id=str(obj.id),
            name=str(obj.name),
            value=obj.value,
            created_at=obj.created_at,
        )

    def delete(self, item_id: str) -> bool:
        obj = self.db.query(TestDBModel).filter(TestDBModel.id == item_id).first()
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True


class TestRepositoryFactory(BaseRepositoryFactory[TestRepository]):
    """Unified repository factory for both Flask and FastAPI tests."""


# Deprecated alias for backwards compatibility
TestManager = TestRepository
TestManagerFactory = TestRepositoryFactory


SECRET = "testsecret"
