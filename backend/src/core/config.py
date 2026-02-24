from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    faq_source_url: str = Field(default="https://support.workways.com/", alias="FAQ_SOURCE_URL")
    index_path: str = Field(default="storage/index", alias="INDEX_PATH")
    processed_faq_path: str = Field(default="data/processed/faqs.json", alias="PROCESSED_FAQ_PATH")
    top_k: int = Field(default=3, alias="TOP_K")
    min_score_threshold: float = Field(default=0.35, alias="MIN_SCORE_THRESHOLD")
    enable_debug: bool = Field(default=False, alias="ENABLE_DEBUG")
    request_timeout_seconds: int = Field(default=20, alias="REQUEST_TIMEOUT_SECONDS")
    ingest_max_pages: int = Field(default=80, alias="INGEST_MAX_PAGES")
    max_question_length: int = Field(default=1000, alias="MAX_QUESTION_LENGTH")
    max_context_chars: int = Field(default=12000, alias="MAX_CONTEXT_CHARS")
    rate_limit_per_minute: int = Field(default=0, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_max_clients: int = Field(default=5000, alias="RATE_LIMIT_MAX_CLIENTS")
    cors_allow_origins: str = Field(default="http://localhost:8501,http://127.0.0.1:8501", alias="CORS_ALLOW_ORIGINS")
    cors_allow_credentials: bool = Field(default=False, alias="CORS_ALLOW_CREDENTIALS")

    @property
    def backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.backend_root / path

    @property
    def processed_faq_file(self) -> Path:
        return self.resolve_path(self.processed_faq_path)

    @property
    def index_dir(self) -> Path:
        return self.resolve_path(self.index_path)

    @property
    def cors_origins(self) -> list[str]:
        raw = [x.strip() for x in self.cors_allow_origins.split(",")]
        return [x for x in raw if x]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
