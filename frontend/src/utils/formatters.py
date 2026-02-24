from __future__ import annotations


def format_score(score: float) -> str:
    return f"{score:.2f}"


def status_label(index_ready: bool, llm_ready: bool) -> tuple[str, str]:
    if index_ready and llm_ready:
        return "Online", "status-ok"
    if index_ready and not llm_ready:
        return "Index OK / LLM OFF", "status-warn"
    return "Degraded", "status-bad"