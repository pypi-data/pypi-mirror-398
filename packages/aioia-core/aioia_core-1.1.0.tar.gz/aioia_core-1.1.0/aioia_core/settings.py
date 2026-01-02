"""Settings classes for AIoIA projects."""

from typing import ClassVar

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """
    Database connection settings.

    Leverages environment variables for configuration, allowing different setups for
    various environments (development, production).

    Environment variables:
        DATABASE_ENABLED: Enable/disable database (default: True)
        DATABASE_URL: Database connection URL (default: sqlite:///./local_database.db)
        DATABASE_POOL_SIZE: Connection pool size (default: 5)
        DATABASE_MAX_OVERFLOW: Max connections beyond pool_size (default: 10)
        DATABASE_POOL_TIMEOUT: Seconds to wait for free connection (default: 30)
        DATABASE_POOL_RECYCLE: Seconds after which connection is recycled (default: 1800)
        DATABASE_CONNECTION_TIMEOUT: Seconds to wait when establishing connection (default: 10)
        DATABASE_STATEMENT_TIMEOUT: Milliseconds for PostgreSQL statement timeout (default: 30000)
    """

    INI_SECTION: ClassVar[str] = "database"

    enabled: bool = True
    url: str = "sqlite:///./local_database.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800
    connection_timeout: int = 10
    statement_timeout: int = 30000

    class Config:
        env_prefix = "DATABASE_"


class OpenAIAPISettings(BaseSettings):
    """
    OpenAI API authentication settings.

    Environment variables:
        OPENAI_API_KEY: OpenAI API key
        OPENAI_ORGANIZATION: OpenAI organization ID (optional)
    """

    INI_SECTION: ClassVar[str] = "openai"

    api_key: str | None = None
    organization: str | None = None

    class Config:
        env_prefix = "OPENAI_"


class JWTSettings(BaseSettings):
    """
    JWT authentication settings.

    Environment variables:
        JWT_SECRET_KEY: Secret key for JWT signing and verification
    """

    INI_SECTION: ClassVar[str] = "jwt"

    secret_key: str | None = None

    class Config:
        env_prefix = "JWT_"
