from datetime import datetime
from pydantic import BaseModel, Field


class FAQItem(BaseModel):
    id: str
    question: str
    answer: str
    url: str
    section: str | None = None
    tags: list[str] = Field(default_factory=list)
    last_seen_at: datetime


class RetrievedFAQ(BaseModel):
    item: FAQItem
    score: float
    rank: int