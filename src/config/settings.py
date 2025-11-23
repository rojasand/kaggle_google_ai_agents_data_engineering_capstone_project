"""Application settings and configuration management."""

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    google_api_key: str | None = Field(
        default=None,
        alias="GOOGLE_API_KEY",
        description="Google Gemini API key for the AI agent",
    )

    # Database Configuration
    database_path: str = Field(
        default="data/data_engineer.db",
        alias="DUCKDB_PATH",
        description="Path to the DuckDB database file",
    )

    # Model Configuration
    gemini_model: str = Field(
        default="gemini-2.5-flash-lite",
        alias="GEMINI_MODEL",
        description="Gemini model to use for the agent",
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    log_directory: str = Field(
        default="logs",
        alias="LOG_DIRECTORY",
        description="Directory for log files",
    )

    # Application Configuration
    app_name: str = Field(
        default="data_engineer_assistant",
        alias="APP_NAME",
        description="Application name",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_dir(self) -> Path:
        """Get the database directory path."""
        return Path(self.database_path).parent

    @property
    def database_file(self) -> Path:
        """Get the full database file path."""
        return Path(self.database_path)

    @property
    def log_dir(self) -> Path:
        """Get the log directory path."""
        return Path(self.log_directory)

    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Set the API key in the environment for google-adk compatibility
if settings.google_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key
