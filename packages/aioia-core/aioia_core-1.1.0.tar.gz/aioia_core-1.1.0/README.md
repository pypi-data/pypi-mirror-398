# AIoIA Core (Python)

AIoIA 프로젝트 공통 Python 인프라 라이브러리

## 설치

```bash
pip install aioia-core
```

## 포함 기능

- **Database**: SQLAlchemy Base, BaseModel, BaseRepository (CRUD)
- **Errors**: 표준화된 에러 코드 및 응답
- **Settings**: DatabaseSettings, OpenAIAPISettings, JWTSettings
- **Testing**: 테스트 인프라 (fixtures, managers)

## 사용법

```python
from aioia_core import BaseModel, BaseRepository
from aioia_core.errors import ErrorResponse, RESOURCE_NOT_FOUND

# SQLAlchemy 모델
class MyModel(BaseModel):
    __tablename__ = "my_table"
    name: Mapped[str] = mapped_column(String)

# Repository 사용
repository = BaseRepository(session, MyModel)
```

## 요구사항

- Python 3.10-3.12

## 라이선스

Apache 2.0
