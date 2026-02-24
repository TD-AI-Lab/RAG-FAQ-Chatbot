from __future__ import annotations

import re

from openai import OpenAI

from src.core.config import get_settings
from src.core.errors import LLMProviderError
from src.domain.models import RetrievedFAQ
from src.rag.prompt_builder import build_grounded_prompt


FALLBACK_ANSWER = "Je ne sais pas."


def _strip_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", text)


def generate_answer(question: str, retrieved: list[RetrievedFAQ]) -> str:
    settings = get_settings()
    if not retrieved:
        return FALLBACK_ANSWER
    if not settings.openai_api_key:
        raise LLMProviderError("OPENAI_API_KEY missing")

    system_prompt, user_prompt = build_grounded_prompt(
        question=question,
        retrieved=retrieved,
        max_context_chars=settings.max_context_chars,
    )

    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.chat.completions.create(
            model=settings.openai_chat_model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise LLMProviderError(f"Chat generation failed: {exc}") from exc

    content = (response.choices[0].message.content or "").strip()
    content = _strip_markdown_links(content)
    return content or FALLBACK_ANSWER
