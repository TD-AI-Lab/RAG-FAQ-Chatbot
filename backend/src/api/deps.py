from __future__ import annotations

from src.core.config import Settings, get_settings
from src.indexing.vector_store import load_index_cached


def get_app_settings() -> Settings:
    return get_settings()


def is_index_ready(settings: Settings) -> bool:
    try:
        load_index_cached(settings.index_dir)
        return True
    except Exception:  # noqa: BLE001
        return False
