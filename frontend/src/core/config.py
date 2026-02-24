from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    backend_base_url: str = Field(default="http://localhost:8000", alias="BACKEND_BASE_URL")
    backend_chat_path: str = Field(default="/chat", alias="BACKEND_CHAT_PATH")
    backend_health_path: str = Field(default="/health", alias="BACKEND_HEALTH_PATH")
    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")
    max_question_length: int = Field(default=1000, alias="MAX_QUESTION_LENGTH")
    show_debug: bool = Field(default=False, alias="SHOW_DEBUG")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()