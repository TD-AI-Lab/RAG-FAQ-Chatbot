from __future__ import annotations

import re
import threading
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.deps import get_app_settings, is_index_ready
from src.api.schemas import ChatRequest, ChatResponse, HealthResponse
from src.core.config import Settings
from src.core.errors import IndexNotBuiltError, LLMProviderError
from src.rag.orchestrator import ask

router = APIRouter()

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE,
)

_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_RATE_LOCK = threading.Lock()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _evict_stale_clients(window_start: float, max_clients: int) -> None:
    stale = [ip for ip, bucket in _RATE_BUCKETS.items() if not bucket or bucket[-1] < window_start]
    for ip in stale:
        _RATE_BUCKETS.pop(ip, None)
    if len(_RATE_BUCKETS) <= max_clients:
        return
    # Best effort LRU-like cleanup by oldest seen timestamp.
    ordered = sorted(_RATE_BUCKETS.items(), key=lambda x: x[1][-1] if x[1] else 0.0)
    to_remove = len(_RATE_BUCKETS) - max_clients
    for ip, _ in ordered[:to_remove]:
        _RATE_BUCKETS.pop(ip, None)


def _validate_question(question: str, settings: Settings) -> str:
    trimmed = question.strip()
    if len(trimmed) < 2:
        raise HTTPException(status_code=400, detail="Question too short")
    if len(trimmed) > settings.max_question_length:
        raise HTTPException(status_code=400, detail="Question too long")
    if EMOJI_PATTERN.search(trimmed):
        raise HTTPException(status_code=400, detail="Emojis not allowed")
    return trimmed


def _enforce_rate_limit(request: Request, settings: Settings) -> None:
    limit = settings.rate_limit_per_minute
    if limit <= 0:
        return

    client_ip = _client_ip(request)
    now = time.time()
    window_start = now - 60
    with _RATE_LOCK:
        _evict_stale_clients(window_start=window_start, max_clients=max(100, settings.rate_limit_max_clients))
        bucket = _RATE_BUCKETS[client_ip]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        bucket.append(now)


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_app_settings)) -> HealthResponse:
    index_ready = is_index_ready(settings)
    llm_ready = bool(settings.openai_api_key)
    status = "ok" if index_ready else "degraded"
    return HealthResponse(status=status, index_ready=index_ready, llm_ready=llm_ready)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request, settings: Settings = Depends(get_app_settings)) -> ChatResponse:
    question = _validate_question(payload.question, settings)
    _enforce_rate_limit(request, settings)

    if not is_index_ready(settings):
        raise HTTPException(status_code=503, detail="Index not built")

    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="LLM provider unavailable")

    try:
        result = ask(question)
        return ChatResponse(**result)
    except LLMProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except IndexNotBuiltError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
