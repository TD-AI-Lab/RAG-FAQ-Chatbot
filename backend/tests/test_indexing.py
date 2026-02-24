import json

import numpy as np

from src.core.config import get_settings
from src.indexing.build_index import build_index
from src.indexing.vector_store import load_index


def test_build_and_load_index(monkeypatch, tmp_path):
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    faqs_path = data_dir / "faqs.json"
    faqs_path.write_text(
        json.dumps(
            [
                {
                    "id": "1",
                    "question": "Q1",
                    "answer": "A1",
                    "url": "https://x/1",
                    "section": None,
                    "tags": [],
                    "last_seen_at": "2026-01-01T00:00:00Z",
                },
                {
                    "id": "2",
                    "question": "Q2",
                    "answer": "A2",
                    "url": "https://x/2",
                    "section": None,
                    "tags": [],
                    "last_seen_at": "2026-01-01T00:00:00Z",
                },
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PROCESSED_FAQ_PATH", str(faqs_path))
    monkeypatch.setenv("INDEX_PATH", str(tmp_path / "index"))
    get_settings.cache_clear()

    monkeypatch.setattr("src.indexing.build_index.embed_texts", lambda texts: np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32))

    manifest = build_index()
    assert manifest["count"] == 2

    settings = get_settings()
    index, meta, _ = load_index(settings.index_dir)
    assert index.ntotal == 2
    assert len(meta) == 2