from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.errors import EmbeddingProviderError
from src.utils.hashing import sha256_text
from src.utils.io import ensure_parent

logger = logging.getLogger(__name__)


def _cache_file(cache_dir: Path, model: str, text: str) -> Path:
    key = sha256_text(f"{model}|{text}")
    return cache_dir / f"{key}.json"


@retry(wait=wait_exponential(multiplier=0.5, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
def _embed_one(client: OpenAI, model: str, text: str) -> list[float]:
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def embed_texts(texts: list[str], max_chars: int = 8000) -> np.ndarray:
    settings = get_settings()
    if not settings.openai_api_key:
        raise EmbeddingProviderError("OPENAI_API_KEY missing")

    client = OpenAI(api_key=settings.openai_api_key)
    cache_dir = settings.backend_root / "storage" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    vectors: list[list[float]] = []
    for text in texts:
        payload = text[:max_chars]
        cache_path = _cache_file(cache_dir, settings.openai_embedding_model, payload)
        if cache_path.exists():
            vectors.append(json.loads(cache_path.read_text(encoding="utf-8"))["embedding"])
            continue
        try:
            emb = _embed_one(client, settings.openai_embedding_model, payload)
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingProviderError(f"Embedding call failed: {exc}") from exc

        ensure_parent(cache_path)
        cache_path.write_text(json.dumps({"embedding": emb}), encoding="utf-8")
        vectors.append(emb)

    if not vectors:
        return np.array([], dtype=np.float32)

    matrix = np.array(vectors, dtype=np.float32)
    return matrix