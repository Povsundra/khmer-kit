"""Retrieval strategies: semantic, hybrid, and hierarchical."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from src.core.embed import get_embedder
from src.core.entities import Entities
from src.core.intent import QueryIntent, preferred_chunk_types
from src.data_prep.build_index import load_index, tokenize

RetrievalMode = Literal["semantic_only", "hybrid", "hierarchical"]

_INDEX_CACHE: dict[str, Any] = {}


def _get_index_bundle():
    if "bundle" not in _INDEX_CACHE:
        index, chunks, bm25, manifest = load_index()
        _INDEX_CACHE["bundle"] = (index, chunks, bm25, manifest)
    return _INDEX_CACHE["bundle"]


def _min_max(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return scores
    lo, hi = float(scores.min()), float(scores.max())
    if hi - lo < 1e-9:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


def _semantic_scores(query: str, candidate_ids: list[int]) -> dict[int, float]:
    index, chunks, _, manifest = _get_index_bundle()
    model_name = manifest.get("embedding_model", "paraphrase-multilingual-mpnet-base-v2")
    embedder = get_embedder(model_name)
    q_vec = embedder.encode([query])
    sem_scores, sem_ids = index.search(q_vec, len(chunks))
    id_set = set(candidate_ids)
    return {
        int(i): float(s)
        for i, s in zip(sem_ids[0], sem_scores[0], strict=True)
        if i >= 0 and int(i) in id_set
    }


def _bm25_scores(query: str, candidate_ids: list[int]) -> dict[int, float]:
    _, _, bm25, _ = _get_index_bundle()
    scores = bm25.get_scores(tokenize(query))
    return {i: float(scores[i]) for i in candidate_ids if i < len(scores)}


def _combine_scores(
    sem_map: dict[int, float],
    bm25_map: dict[int, float],
    *,
    semantic_weight: float,
    bm25_weight: float,
) -> list[tuple[int, float]]:
    all_ids = set(sem_map) | set(bm25_map)
    sem_arr = np.array([sem_map.get(i, 0.0) for i in all_ids])
    bm25_arr = np.array([bm25_map.get(i, 0.0) for i in all_ids])
    combined = semantic_weight * _min_max(sem_arr) + bm25_weight * _min_max(bm25_arr)
    ranked = sorted(zip(all_ids, combined, strict=True), key=lambda x: x[1], reverse=True)
    return [(int(i), float(s)) for i, s in ranked]


def _hits_from_ranked(ranked: list[tuple[int, float]], chunks: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for chunk_id, score in ranked[:top_k]:
        hit = dict(chunks[chunk_id])
        hit["score"] = score
        results.append(hit)
    return results


def _predict_categories(query: str, top_n: int = 2) -> list[str]:
    _, chunks, _, _ = _get_index_bundle()
    parent_ids = [i for i, c in enumerate(chunks) if c["chunk_type"] == "parent"]
    sem_map = _semantic_scores(query, parent_ids)
    ranked = sorted(sem_map.items(), key=lambda x: x[1], reverse=True)[:top_n]
    categories: list[str] = []
    for chunk_id, _ in ranked:
        cat = chunks[chunk_id]["category"]
        if cat not in categories:
            categories.append(cat)
    return categories


def search(
    query: str,
    *,
    mode: RetrievalMode = "hybrid",
    top_k: int = 5,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> list[dict[str, Any]]:
    _, chunks, _, _ = _get_index_bundle()
    all_ids = list(range(len(chunks)))

    if mode == "semantic_only":
        sem_map = _semantic_scores(query, all_ids)
        ranked = sorted(sem_map.items(), key=lambda x: x[1], reverse=True)
        return _hits_from_ranked(ranked, chunks, top_k)

    if mode == "hybrid":
        sem_map = _semantic_scores(query, all_ids)
        bm25_map = _bm25_scores(query, all_ids)
        ranked = _combine_scores(
            sem_map, bm25_map, semantic_weight=semantic_weight, bm25_weight=bm25_weight
        )
        return _hits_from_ranked(ranked, chunks, top_k)

    if mode == "hierarchical":
        categories = _predict_categories(query, top_n=2)
        candidate_ids = [
            i
            for i, c in enumerate(chunks)
            if c["category"] in categories or c["chunk_type"] == "parent"
        ]
        sem_map = _semantic_scores(query, candidate_ids)
        bm25_map = _bm25_scores(query, candidate_ids)
        ranked = _combine_scores(
            sem_map, bm25_map, semantic_weight=semantic_weight, bm25_weight=bm25_weight
        )
        return _hits_from_ranked(ranked, chunks, top_k)

    raise ValueError(f"Unknown retrieval mode: {mode}")


def hybrid_search(
    query: str,
    *,
    top_k: int = 5,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """Backward-compatible wrapper used by query_index.py."""
    return search(
        query,
        mode="hybrid",
        top_k=top_k,
        semantic_weight=semantic_weight,
        bm25_weight=bm25_weight,
    )


def get_all_chunks() -> list[dict[str, Any]]:
    _, chunks, _, _ = _get_index_bundle()
    return chunks


def get_chunks_for_slug(
    slug: str,
    *,
    chunk_type: str | None = None,
) -> list[dict[str, Any]]:
    chunks = get_all_chunks()
    results = [c for c in chunks if c.get("slug") == slug]
    if chunk_type:
        results = [c for c in results if c.get("chunk_type") == chunk_type]
    if chunk_type == "step":
        results.sort(key=lambda c: c.get("step") or 0)
    return results


def get_parent_for_category(category: str) -> dict[str, Any] | None:
    for chunk in get_all_chunks():
        if chunk.get("chunk_type") == "parent" and chunk.get("category") == category:
            return chunk
    return None


def _boost_hits(
    hits: list[dict[str, Any]],
    *,
    intent: QueryIntent,
    entities: Entities,
) -> list[dict[str, Any]]:
    preferred = preferred_chunk_types(intent)
    boosted: list[dict[str, Any]] = []
    for hit in hits:
        score = float(hit.get("score", 0.0))
        ctype = hit.get("chunk_type", "")
        if preferred and ctype in preferred:
            score *= 1.4
        elif preferred and ctype not in preferred:
            score *= 0.65
        if entities.slug and hit.get("slug") == entities.slug:
            score *= 1.3
        elif entities.slug and hit.get("slug") not in (entities.slug, f"_parent_{entities.category}"):
            score *= 0.75
        if entities.category and hit.get("category") == entities.category:
            score *= 1.1
        boosted.append({**hit, "score": score})
    boosted.sort(key=lambda h: h["score"], reverse=True)
    return boosted


def search_for_intent(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    *,
    top_k: int = 5,
    semantic_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """Hybrid search with intent-aware boosting and one-shot requery."""
    hits = search(
        query,
        mode="hybrid",
        top_k=top_k * 2,
        semantic_weight=semantic_weight,
        bm25_weight=bm25_weight,
    )
    hits = _boost_hits(hits, intent=intent, entities=entities)

    preferred = preferred_chunk_types(intent)
    if preferred and hits and hits[0].get("chunk_type") not in preferred:
        _, chunks, _, _ = _get_index_bundle()
        filtered_ids = [
            i for i, c in enumerate(chunks) if c.get("chunk_type") in preferred
        ]
        if entities.slug:
            slug_ids = [i for i in filtered_ids if chunks[i].get("slug") == entities.slug]
            if slug_ids:
                filtered_ids = slug_ids
        elif entities.category:
            cat_ids = [
                i
                for i in filtered_ids
                if chunks[i].get("category") == entities.category
                or chunks[i].get("chunk_type") == "parent"
            ]
            if cat_ids:
                filtered_ids = cat_ids

        sem_map = _semantic_scores(query, filtered_ids)
        bm25_map = _bm25_scores(query, filtered_ids)
        ranked = _combine_scores(
            sem_map, bm25_map, semantic_weight=semantic_weight, bm25_weight=bm25_weight
        )
        hits = _hits_from_ranked(ranked, chunks, top_k * 2)
        hits = _boost_hits(hits, intent=intent, entities=entities)

    return hits[:top_k]
