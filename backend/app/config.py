"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Jarvis backend."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    openai_whisper_model: str = Field(default="whisper-1", alias="OPENAI_WHISPER_MODEL")

    # Server
    host: str = Field(default="0.0.0.0", alias="JARVIS_HOST")
    port: int = Field(default=8000, alias="JARVIS_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="JARVIS_CORS_ORIGINS",
    )

    # Storage
    db_path: str = Field(default="./data/jarvis.db", alias="JARVIS_DB_PATH")

    # Tool toggles
    enable_app_launcher: bool = Field(default=True, alias="JARVIS_ENABLE_APP_LAUNCHER")
    enable_browser: bool = Field(default=True, alias="JARVIS_ENABLE_BROWSER")
    enable_file_summarizer: bool = Field(default=True, alias="JARVIS_ENABLE_FILE_SUMMARIZER")
    enable_task_memory: bool = Field(default=True, alias="JARVIS_ENABLE_TASK_MEMORY")

    # Browser
    browser_engine: str = Field(default="chromium", alias="JARVIS_BROWSER_ENGINE")
    browser_headless: bool = Field(default=True, alias="JARVIS_BROWSER_HEADLESS")

    # Plugin dir (relative to backend/)
    plugin_dir: str = Field(default="app/plugins", alias="JARVIS_PLUGIN_DIR")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def db_url(self) -> str:
        path = Path(self.db_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
