from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Minimal configuration for prism-models database operations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PG_DATABASE_URL: str = "postgresql+asyncpg://user:password@host"
    environment: Environment = Environment.DEVELOPMENT

    @property
    def PG_DATABASE_URL_PRISM(self) -> str:
        """Get the Prism database URL."""
        return self.PG_DATABASE_URL + "/prism"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


settings = Settings()