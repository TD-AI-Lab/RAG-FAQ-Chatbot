from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.core.config import get_settings
from src.core.errors import IngestionError
from src.indexing.embeddings import embed_texts
from src.indexing.vector_store import l2_normalize, save_index
from src.utils.io import read_json
from src.utils.text import truncate_text

logger = logging.getLogger(__name__)


def build_index() -> dict:
    settings = get_settings()
    data_file = settings.processed_faq_file
    if not data_file.exists():
        raise IngestionError(f"Processed FAQ file missing: {data_file}")

    faqs = read_json(data_file)
    if not faqs:
        raise IngestionError("Processed FAQ list is empty")

    texts: list[str] = []
    metadata: list[dict] = []

    for item in faqs:
        answer = item.get("answer", "")
        if not answer.strip():
            continue
        content = f"Q: {item.get('question', '').strip()}\nA: {answer.strip()}"
        content = truncate_text(content, 8000)
        texts.append(content)
        metadata.append(
            {
                "id": item.get("id"),
                "question": item.get("question"),
                "answer": item.get("answer"),
                "url": item.get("url"),
                "section": item.get("section"),
                "tags": item.get("tags", []),
                "last_seen_at": item.get("last_seen_at"),
            }
        )

    if not texts:
        raise IngestionError("No valid FAQ entries with non-empty answers")

    vectors = embed_texts(texts)
    if vectors.shape[0] != len(metadata):
        raise IngestionError("Embedding/vector metadata length mismatch")

    vectors = l2_normalize(vectors)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": settings.openai_embedding_model,
        "count": len(metadata),
        "dim": int(vectors.shape[1]),
        "source": str(data_file),
    }

    save_index(settings.index_dir, vectors, metadata, manifest)
    logger.info("Index built successfully with %s items", len(metadata))
    return manifest


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_index()