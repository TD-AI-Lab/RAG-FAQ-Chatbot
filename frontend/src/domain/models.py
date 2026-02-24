from __future__ import annotations

from pydantic import BaseModel, Field


class SourceModel(BaseModel):
    id: str
    question: str
    url: str
    score: float
    rank: int


class ChatResponseModel(BaseModel):
    answer: str
    sources: list[SourceModel] = Field(default_factory=list)
    debug: dict = Field(default_factory=dict)


class HealthModel(BaseModel):
    status: str
    index_ready: bool
    llm_ready: bool