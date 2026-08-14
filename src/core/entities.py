"""Extract dish, category, and ingredient entities from user queries."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any

from src.config import CATEGORIES, CHECKLIST_PATH, PROCESSED
from src.core.entity_resolve import normalize_text, resolve_dish_phrase

NORMALIZE_RE = re.compile(r"[^a-z0-9\u1780-\u17FF]+")
TRAILING_PUNCT_RE = re.compile(r"[?.!,;:]+$")

# Aliases too short/generic to count as a known dish on their own
_GENERIC_DISH_TOKENS = frozenset(
    {"cha", "samlor", "sngor", "soup", "soups", "dessert", "other", "stir", "fry"}
)
MIN_DISH_MATCH_LEN = 8

_PREFIX_RE = re.compile(
    r"^(?:how to (?:cook|make|prepare)|how do i (?:cook|make|prepare)|"
    r"recipe for|steps for|tell me how to|ingredients of|ingredients for|"
    r"i want to (?:eat|make|cook)|what(?:'s| is) in)\s+",
    re.I,
)


@dataclass
class Entities:
    slug: str | None = None
    category: str | None = None
    ingredient: str | None = None
    dish_name_en: str | None = None
    dish_name_kh: str | None = None
    requested_name: str | None = None
    dish_known: bool = False
    resolved_from: str | None = None
    match_method: str | None = None
    match_score: float | None = None
    signals: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return normalize_text(text)


@lru_cache(maxsize=1)
def _load_registry() -> list[dict[str, Any]]:
    return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _registered_slug_norms() -> frozenset[str]:
    norms: set[str] = set()
    for dish in _load_registry():
        norms.add(_normalize(dish["slug"].replace("_", " ")))
        norms.add(_normalize(dish["slug"]))
    return frozenset(norms)


@lru_cache(maxsize=1)
def _ingredient_vocab() -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for cat in CATEGORIES:
        cat_dir = PROCESSED / cat
        if not cat_dir.is_dir():
            continue
        for path in cat_dir.glob("*.json"):
            dish = json.loads(path.read_text(encoding="utf-8"))
            for ing in dish.get("ingredients", []):
                en = ing.get("standardized_en", "").strip()
                kh = ing.get("raw_kh", "").strip()
                if en:
                    items.append((_normalize(en), en))
                if kh:
                    items.append((_normalize(kh), en or kh))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for norm, canon in sorted(items, key=lambda x: len(x[0]), reverse=True):
        if norm not in seen:
            seen.add(norm)
            unique.append((norm, canon))
    return unique


def extract_requested_dish_phrase(query: str) -> str | None:
    """Strip intent prefixes to get the dish name the user asked for."""
    text = query.strip()
    text = _PREFIX_RE.sub("", text).strip()
    # Drop trailing context clauses
    for sep in (" but ", " what should", " what do", " at the market", " without "):
        idx = text.lower().find(sep)
        if idx > 0:
            text = text[:idx].strip()
    # Remove parenthetical notes e.g. "(chicken)"
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text).strip()
    text = TRAILING_PUNCT_RE.sub("", text).strip()
    return text if len(text) >= 3 else None


def _is_valid_dish_match(alias_norm: str) -> bool:
    if alias_norm in _registered_slug_norms():
        return True
    khmer_chars = sum(1 for c in alias_norm if "\u1780" <= c <= "\u17FF")
    if khmer_chars >= 3:
        return True
    if alias_norm in _GENERIC_DISH_TOKENS:
        return False
    tokens = alias_norm.split()
    if len(tokens) >= 2:
        return True
    return len(alias_norm) >= MIN_DISH_MATCH_LEN


def _match_dish(query: str) -> tuple[dict[str, Any] | None, int]:
    q_norm = _normalize(query)
    best: dict[str, Any] | None = None
    best_len = 0
    for dish in _load_registry():
        candidates = [
            dish["slug"].replace("_", " "),
            dish["dish_name_en"].split("(")[0].strip(),
            dish["dish_name_en"],
            dish["dish_name_kh"],
        ]
        for alias in candidates:
            a_norm = _normalize(alias)
            if not a_norm or not _is_valid_dish_match(a_norm):
                continue
            if a_norm in q_norm and len(a_norm) > best_len:
                best = dish
                best_len = len(a_norm)
    return best, best_len


def _match_category(query_norm: str) -> str | None:
    aliases = {
        "samlor": ["samlor", "sngor", "soup", "soups", "សម្ល", "ស្ងោរ"],
        "cha": ["cha", "stir fry", "stir-fry", "ឆា"],
        "dessert": ["dessert", "desserts", "sweet", "បង្អែ"],
        "other": ["other", "salad", "omelette"],
    }
    for cat, terms in aliases.items():
        for term in terms:
            t_norm = _normalize(term)
            if t_norm and t_norm in query_norm:
                return cat
    return None


def _match_ingredient(query_norm: str) -> str | None:
    for norm, canon in _ingredient_vocab():
        if norm and norm in query_norm:
            return canon
    return None


def _apply_dish(
    entities: Entities,
    dish: dict[str, Any],
    *,
    match_len: int = 0,
    method: str = "exact",
    score: float | None = None,
    resolved_from: str | None = None,
) -> None:
    entities.slug = dish["slug"]
    entities.category = dish["category"]
    entities.dish_name_en = dish["dish_name_en"]
    entities.dish_name_kh = dish["dish_name_kh"]
    entities.dish_known = True
    entities.match_method = method
    entities.match_score = score
    if resolved_from:
        entities.resolved_from = resolved_from
    if method == "exact":
        entities.signals.append(f"dish:{dish['slug']}:{match_len}")
    else:
        entities.signals.append(f"dish_{method}:{dish['slug']}:{score:.0f}")


def _resolve_fuzzy(entities: Entities, phrase: str) -> bool:
    result = resolve_dish_phrase(phrase)
    if not result:
        return False
    _apply_dish(
        entities,
        result.dish,
        method=result.method,
        score=result.score,
        resolved_from=phrase.strip(),
    )
    return True


def extract_entities(query: str) -> Entities:
    entities = Entities()
    q_norm = _normalize(query)
    entities.requested_name = extract_requested_dish_phrase(query)

    dish, match_len = _match_dish(query)
    if dish:
        _apply_dish(entities, dish, match_len=match_len, method="exact")
    elif entities.requested_name and _resolve_fuzzy(entities, entities.requested_name):
        pass
    elif not entities.dish_known and _resolve_fuzzy(entities, query):
        pass

    cat = _match_category(q_norm)
    if cat:
        entities.category = entities.category or cat
        entities.signals.append(f"category:{cat}")

    ing = _match_ingredient(q_norm)
    if ing:
        entities.ingredient = ing
        entities.signals.append(f"ingredient:{ing}")

    return entities
