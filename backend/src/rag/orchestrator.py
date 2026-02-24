from __future__ import annotations

from src.core.config import get_settings
from src.rag.generator import FALLBACK_ANSWER, generate_answer
from src.rag.retriever import retrieve_faqs


def ask(question: str) -> dict:
    settings = get_settings()
    retrieved = retrieve_faqs(question, k=settings.top_k)
    answer = generate_answer(question, retrieved) if retrieved else FALLBACK_ANSWER

    sources = [
        {
            "id": entry.item.id,
            "question": entry.item.question,
            "url": entry.item.url,
            "score": round(entry.score, 4),
            "rank": entry.rank,
        }
        for entry in retrieved
    ]

    payload = {
        "answer": answer,
        "sources": sources,
        "debug": {
            "retrieved_count": len(retrieved),
            "threshold": settings.min_score_threshold,
        }
        if settings.enable_debug
        else {},
    }
    return payload