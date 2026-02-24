from __future__ import annotations

from src.core.errors import InputValidationError


def validate_question(value: str, max_len: int) -> str:
    cleaned = value.strip()
    if len(cleaned) < 2:
        raise InputValidationError("Question trop courte (min 2 caracteres).")
    if len(cleaned) > max_len:
        raise InputValidationError(f"Question trop longue (max {max_len} caracteres).")
    return cleaned