"""Build FAISS + BM25 index from processed JSON corpus."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from src.config import BM25_PATH, DOCSTORE_PATH, FAISS_PATH, INDEX_DIR, MANIFEST_PATH, PROCESSED
from src.core.embed import Embedder, get_embedder
from src.data_prep.corpus_chunks import collect_chunks

TOKEN_RE = re.compile(r"[\u1780-\u17FF]+|[a-z0-9]+", re.IGNORECASE)


def bm25_text(chunk: dict[str, Any]) -> str:
    parts = [
        chunk.get("embed_text", ""),
        chunk.get("dish_name_kh", ""),
        chunk.get("dish_name_en", ""),
        chunk.get("text_kh", ""),
    ]
    return " ".join(p for p in parts if p)


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_index(*, processed_root: Path = PROCESSED, show_progress: bool = True) -> dict[str, Any]:
    chunks = collect_chunks(processed_root)
    if not chunks:
        raise ValueError(f"No chunks found under {processed_root}")

    embedder = Embedder()
    texts = [c["embed_text"] for c in chunks]
    vectors = embedder.encode(texts, show_progress=show_progress)

    index = faiss.IndexFlatIP(embedder.dimension)
    index.add(vectors)

    tokenized = [tokenize(bm25_text(c)) for c in chunks]
    bm25 = BM25Okapi(tokenized)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_PATH))

    docstore = {"chunks": chunks}
    DOCSTORE_PATH.write_text(json.dumps(docstore, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bm25_payload = {
        "tokenized_corpus": tokenized,
        "chunk_ids": [c["id"] for c in chunks],
    }
    BM25_PATH.write_text(json.dumps(bm25_payload, ensure_ascii=False) + "\n", encoding="utf-8")

    manifest = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": embedder.model_name,
        "chunk_count": len(chunks),
        "step_chunks": sum(1 for c in chunks if c["chunk_type"] == "step"),
        "ingredient_chunks": sum(1 for c in chunks if c["chunk_type"] == "ingredients"),
        "parent_chunks": sum(1 for c in chunks if c["chunk_type"] == "parent"),
        "faiss_path": str(FAISS_PATH.relative_to(INDEX_DIR.parent.parent)),
        "docstore_path": str(DOCSTORE_PATH.relative_to(INDEX_DIR.parent.parent)),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return manifest


def load_index() -> tuple[faiss.Index, list[dict[str, Any]], BM25Okapi, dict[str, Any]]:
    if not FAISS_PATH.is_file() or not DOCSTORE_PATH.is_file():
        raise FileNotFoundError("Index not built. Run: python scripts/build_index.py")

    index = faiss.read_index(str(FAISS_PATH))
    docstore = json.loads(DOCSTORE_PATH.read_text(encoding="utf-8"))
    chunks: list[dict[str, Any]] = docstore["chunks"]

    bm25_payload = json.loads(BM25_PATH.read_text(encoding="utf-8"))
    bm25 = BM25Okapi(bm25_payload["tokenized_corpus"])

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.is_file() else {}
    return index, chunks, bm25, manifest
