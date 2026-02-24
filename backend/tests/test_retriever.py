import numpy as np
import pytest

from src.core.config import get_settings
from src.core.errors import IndexNotBuiltError
from src.rag.retriever import retrieve_faqs


class FakeIndex:
    def search(self, q, k):
        return np.array([[0.9, 0.2]], dtype=np.float32), np.array([[0, 1]], dtype=np.int64)


def test_retriever_ranks_and_filters(monkeypatch):
    monkeypatch.setenv("MIN_SCORE_THRESHOLD", "0.3")
    get_settings.cache_clear()

    meta = [
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

    monkeypatch.setattr(
        "src.rag.retriever.load_index_cached",
        lambda _: (FakeIndex(), meta, {"embedding_model": "text-embedding-3-small"}),
    )
    monkeypatch.setattr("src.rag.retriever.embed_texts", lambda texts: np.array([[1.0, 0.0]], dtype=np.float32))

    results = retrieve_faqs("Question test", k=2)
    assert len(results) == 1
    assert results[0].item.id == "1"
    assert results[0].rank == 1


def test_retriever_fails_on_embedding_model_mismatch(monkeypatch):
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    get_settings.cache_clear()

    meta = [
        {
            "id": "1",
            "question": "Q1",
            "answer": "A1",
            "url": "https://x/1",
            "section": None,
            "tags": [],
            "last_seen_at": "2026-01-01T00:00:00Z",
        }
    ]
    manifest = {"embedding_model": "text-embedding-3-large"}
    monkeypatch.setattr("src.rag.retriever.load_index_cached", lambda _: (FakeIndex(), meta, manifest))
    monkeypatch.setattr("src.rag.retriever.embed_texts", lambda texts: np.array([[1.0, 0.0]], dtype=np.float32))

    with pytest.raises(IndexNotBuiltError):
        retrieve_faqs("Question test", k=1)
