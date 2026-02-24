from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from src.core.errors import IndexNotBuiltError


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    if vectors.size == 0:
        return vectors
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def save_index(index_dir: Path, vectors: np.ndarray, metadata: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors.astype(np.float32))

    faiss.write_index(index, str(index_dir / "faiss.index"))
    (index_dir / "meta.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    (index_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def load_index(index_dir: Path) -> tuple[faiss.Index, list[dict[str, Any]], dict[str, Any]]:
    idx_file = index_dir / "faiss.index"
    meta_file = index_dir / "meta.json"
    manifest_file = index_dir / "manifest.json"

    if not idx_file.exists() or not meta_file.exists() or not manifest_file.exists():
        raise IndexNotBuiltError("Index artifacts not found")

    index = faiss.read_index(str(idx_file))
    metadata = json.loads(meta_file.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

    if index.ntotal != len(metadata):
        raise IndexNotBuiltError("Index/meta mismatch")

    return index, metadata, manifest


def _index_signature(index_dir: Path) -> tuple[float, float, float]:
    files = [index_dir / "faiss.index", index_dir / "meta.json", index_dir / "manifest.json"]
    if not all(p.exists() for p in files):
        raise IndexNotBuiltError("Index artifacts not found")
    return tuple(p.stat().st_mtime for p in files)


@lru_cache(maxsize=2)
def _load_index_cached(index_dir_raw: str, signature: tuple[float, float, float]) -> tuple[faiss.Index, list[dict[str, Any]], dict[str, Any]]:
    del signature
    return load_index(Path(index_dir_raw))


def load_index_cached(index_dir: Path) -> tuple[faiss.Index, list[dict[str, Any]], dict[str, Any]]:
    sig = _index_signature(index_dir)
    return _load_index_cached(str(index_dir.resolve()), sig)
