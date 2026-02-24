from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class SourceOut(BaseModel):
    id: str
    question: str
    url: str
    score: float
    rank: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceOut]
    debug: dict


class HealthResponse(BaseModel):
    status: str
    index_ready: bool
    llm_ready: bool