from datetime import datetime, timezone

from src.domain.models import FAQItem, RetrievedFAQ
from src.rag.generator import FALLBACK_ANSWER, generate_answer
from src.rag.prompt_builder import build_grounded_prompt


def test_generator_fallback_without_retrieval(monkeypatch):
    result = generate_answer("Question", [])
    assert result == FALLBACK_ANSWER


def test_prompt_contains_sources():
    item = FAQItem(
        id="1",
        question="Q1",
        answer="A1",
        url="https://x/1",
        section=None,
        tags=[],
        last_seen_at=datetime.now(timezone.utc),
    )
    retrieved = [RetrievedFAQ(item=item, score=0.9, rank=1)]
    _, user = build_grounded_prompt("Test", retrieved, max_context_chars=1000)
    assert "[FAQ 1]" in user
    assert "URL: https://x/1" in user