from __future__ import annotations

import logging
import re

import numpy as np

from src.core.config import get_settings
from src.core.errors import IndexNotBuiltError
from src.domain.models import FAQItem, RetrievedFAQ
from src.indexing.embeddings import embed_texts
from src.indexing.vector_store import l2_normalize, load_index_cached

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"\b[\w']+\b", text.lower()) if len(t) > 2}


def _lexical_overlap(query: str, question: str, answer: str) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    doc_tokens = _tokenize(f"{question} {answer}")
    if not doc_tokens:
        return 0.0
    return len(q_tokens.intersection(doc_tokens)) / len(q_tokens)


def retrieve_faqs(query: str, k: int | None = None) -> list[RetrievedFAQ]:
    settings = get_settings()
    query = query.strip()
    if len(query) < 2:
        return []

    top_k = k or settings.top_k
    index, metadata, manifest = load_index_cached(settings.index_dir)
    indexed_model = str(manifest.get("embedding_model", "")).strip()
    if indexed_model and indexed_model != settings.openai_embedding_model:
        raise IndexNotBuiltError(
            f"Index built with '{indexed_model}' but runtime model is '{settings.openai_embedding_model}'. Rebuild index."
        )

    q_vec = embed_texts([query])
    if q_vec.size == 0:
        return []
    q_vec = l2_normalize(q_vec)

    # Pull a wider semantic candidate set, then rerank with lexical overlap.
    candidate_k = min(max(top_k * 4, top_k), len(metadata))
    scores, indices = index.search(q_vec.astype(np.float32), candidate_k)

    candidates: list[tuple[float, float, int, dict]] = []
    seen_ids: set[str] = set()
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        if float(score) < settings.min_score_threshold:
            continue
        item_raw = metadata[idx]
        faq_id = str(item_raw.get("id"))
        if faq_id in seen_ids:
            continue
        seen_ids.add(faq_id)
        lex = _lexical_overlap(
            query=query,
            question=str(item_raw.get("question", "")),
            answer=str(item_raw.get("answer", "")),
        )
        combined = (0.8 * float(score)) + (0.2 * lex)
        candidates.append((combined, float(score), idx, item_raw))

    candidates.sort(key=lambda x: x[0], reverse=True)

    results: list[RetrievedFAQ] = []
    for rank, (combined_score, semantic_score, _, item_raw) in enumerate(candidates[:top_k], start=1):
        faq_item = FAQItem(**item_raw)
        final_score = max(semantic_score, combined_score)
        results.append(RetrievedFAQ(item=faq_item, score=final_score, rank=rank))

    return results
