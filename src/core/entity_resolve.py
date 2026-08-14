"""Typo-tolerant dish entity resolution against the 14-dish registry."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from rapidfuzz import fuzz

from src.config import ALIASES_PATH, CHECKLIST_PATH

NORMALIZE_RE = re.compile(r"[^a-z0-9\u1780-\u17FF]+")
TRAILING_PUNCT_RE = re.compile(r"[?.!,;:]+$")

_CATEGORY_TOKENS = frozenset(
    {"cha", "samlor", "sngor", "soup", "soups", "dessert", "other", "stir", "fry", "salad"}
)

MIN_FUZZY_SCORE_EN = 85
MIN_FUZZY_SCORE_KH = 90
MIN_AMBIGUITY_MARGIN = 8
MIN_EN_LEN = 4
MIN_KH_LEN = 3


@dataclass(frozen=True)
class ResolveResult:
    slug: str
    score: float
    method: str  # alias | fuzzy
    dish: dict[str, Any]
    matched_alias: str


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    text = TRAILING_PUNCT_RE.sub("", text).strip()
    return NORMALIZE_RE.sub(" ", text).strip()


def _khmer_char_count(text: str) -> int:
    return sum(1 for c in text if "\u1780" <= c <= "\u17FF")


def _score_pair(query_norm: str, alias_norm: str) -> float:
    if _khmer_char_count(query_norm) >= MIN_KH_LEN or _khmer_char_count(alias_norm) >= MIN_KH_LEN:
        return float(fuzz.ratio(query_norm, alias_norm))
    if " " in query_norm or " " in alias_norm:
        return float(fuzz.token_set_ratio(query_norm, alias_norm))
    return float(fuzz.partial_ratio(query_norm, alias_norm))


def _min_score(query_norm: str) -> float:
    return MIN_FUZZY_SCORE_KH if _khmer_char_count(query_norm) >= MIN_KH_LEN else MIN_FUZZY_SCORE_EN


def _phrase_too_short(query_norm: str) -> bool:
    if not query_norm:
        return True
    if _khmer_char_count(query_norm) >= MIN_KH_LEN:
        return False
    if query_norm in _CATEGORY_TOKENS:
        return True
    return len(query_norm) < MIN_EN_LEN


@lru_cache(maxsize=1)
def _load_registry() -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(CHECKLIST_PATH.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def _load_curated_aliases() -> dict[str, list[str]]:
    if not ALIASES_PATH.is_file():
        return {}
    return json.loads(ALIASES_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _alias_index() -> tuple[tuple[str, str, str], ...]:
    """(normalized_alias, slug, display_alias) entries for lookup and fuzzy scoring."""
    by_slug: dict[str, dict[str, Any]] = {d["slug"]: d for d in _load_registry()}
    entries: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(alias: str, slug: str) -> None:
        norm = normalize_text(alias)
        if not norm:
            return
        key = (norm, slug)
        if key in seen:
            return
        seen.add(key)
        entries.append((norm, slug, alias.strip()))

    for dish in _load_registry():
        slug = dish["slug"]
        add(slug.replace("_", " "), slug)
        add(slug, slug)
        base_en = dish["dish_name_en"].split("(")[0].strip()
        add(base_en, slug)
        add(dish["dish_name_en"], slug)
        add(dish["dish_name_kh"], slug)

    for slug, aliases in _load_curated_aliases().items():
        if slug not in by_slug:
            continue
        for alias in aliases:
            add(alias, slug)

    return tuple(entries)


@lru_cache(maxsize=1)
def _alias_exact_map() -> dict[str, str]:
    exact: dict[str, str] = {}
    for norm, slug, _ in _alias_index():
        exact.setdefault(norm, slug)
    return exact


def resolve_dish_phrase(phrase: str) -> ResolveResult | None:
    """Resolve a dish phrase via alias exact match, then fuzzy scoring."""
    query_norm = normalize_text(phrase)
    if _phrase_too_short(query_norm):
        return None

    by_slug = {d["slug"]: d for d in _load_registry()}

    slug = _alias_exact_map().get(query_norm)
    if slug:
        return ResolveResult(
            slug=slug,
            score=100.0,
            method="alias",
            dish=by_slug[slug],
            matched_alias=phrase.strip(),
        )

    scored: list[tuple[float, str, str]] = []
    for alias_norm, slug, display_alias in _alias_index():
        if alias_norm in _CATEGORY_TOKENS and " " not in query_norm:
            continue
        score = _score_pair(query_norm, alias_norm)
        scored.append((score, slug, display_alias))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_slug, best_alias = scored[0]
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if best_score < _min_score(query_norm):
        return None
    if best_score - second_score < MIN_AMBIGUITY_MARGIN and best_score < 100:
        return None

    return ResolveResult(
        slug=best_slug,
        score=best_score,
        method="fuzzy",
        dish=by_slug[best_slug],
        matched_alias=best_alias,
    )
