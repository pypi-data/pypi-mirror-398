from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cross-platform default data directory in user's home
DEFAULT_DATA_DIR = str(Path.home() / ".task-context-mcp" / "data")
DEFAULT_DB_PATH = str(Path.home() / ".task-context-mcp" / "data" / "task_context.db")


class Settings(BaseSettings):
    """Main application settings"""

    model_config = SettingsConfigDict(
        env_prefix="TASK_CONTEXT_MCP__",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(default="task-context-mcp", description="Application name")
    app_version: str = Field(default="0.1.6", description="Application version")
    data_dir: str = Field(
        default=DEFAULT_DATA_DIR,
        description="Data directory path (default: ~/.task-context-mcp/data)",
    )

    # Database settings
    database_url: str = Field(
        default=f"sqlite:///{DEFAULT_DB_PATH}",
        description="Database URL (default: ~/.task-context-mcp/data/task_context.db)",
    )

    # Logging settings
    logging_level: str = Field(default="INFO", description="Logging level")
    logging_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {extra[app]} v{extra[version]} | {level: <8} | {name}:{function}:{line} - {message} | {extra}",
        description="Console log format",
    )


def get_settings() -> Settings:
    """Retrieve application settings"""
    return Settings()
