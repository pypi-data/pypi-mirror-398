import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# configure centralized logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ProjectSettings(BaseSettings):
    """Project settings using Pydantic."""

    # Example settings with default values
    # These can be overridden by environment variables (e.g. PROJECT_NAME)
    PROJECT_NAME: str = "python-starter"
    LOG_LEVEL: str = "INFO"

    # Configuration for Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ProjectConfig:
    """Central configuration for the project."""

    logger = logging.getLogger("project")
    settings = ProjectSettings()

    @staticmethod
    def _ensure_dir(path: str) -> None:
        """Ensures that a directory exists."""
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_logger() -> logging.Logger:
        """Returns the central logger."""
        return ProjectConfig.logger

    @staticmethod
    def get_settings() -> ProjectSettings:
        """Returns the project settings."""
        return ProjectConfig.settings

    @staticmethod
    def get_base_dir() -> Path:
        """Returns the base directory of the project."""
        return Path(__file__).resolve().parent.parent.parent
