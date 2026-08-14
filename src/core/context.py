"""Conversation focus: resolve this/that/the soup to the last real dish."""

from __future__ import annotations

import re

from src.core.entities import Entities, _apply_dish, dish_by_slug
from src.core.entity_resolve import normalize_text
from src.core.intent import QueryIntent

DISH_SCOPED_INTENTS: frozenset[QueryIntent] = frozenset(
    {
        "ingredients",
        "shopping_list",
        "how_to_cook",
        "substitution",
        "technique",
        "dish_lookup",
    }
)

_ANAPHORA_RE = re.compile(
    r"(?:\b(?:this|that|it)\b|\bthis one\b|\bthat one\b|"
    r"\bthe (?:soup|dish|recipe)\b|\bthis (?:soup|dish|recipe)\b|"
    r"\bthat (?:soup|dish|recipe)\b|"
    r"នេះ|ម្ហូបនេះ|សម្លនេះ)",
    re.I,
)

_GENERIC_REFS = frozenset(
    {
        "this",
        "that",
        "it",
        "this one",
        "that one",
        "this soup",
        "that soup",
        "the soup",
        "this dish",
        "that dish",
        "the dish",
        "this recipe",
        "that recipe",
        "the recipe",
        "soup",
        "dish",
        "recipe",
        "នេះ",
        "ម្ហូបនេះ",
        "សម្លនេះ",
    }
)

_BARE_INTENT_RE = re.compile(
    r"^(?:ingredients?|shopping list|what(?:'s| is) in(?: it)?|"
    r"what do i need|how to (?:cook|make|prepare)(?: it)?|"
    r"recipe|steps|គ្រឿងផ្សំ|របៀបធ្វើ)[\s?!.]*$",
    re.I,
)


def is_followup_query(query: str, requested_name: str | None = None) -> bool:
    """True when the query points at a prior dish instead of naming a new one."""
    text = query.strip()
    if not text:
        return False
    if _ANAPHORA_RE.search(text):
        return True
    if _BARE_INTENT_RE.match(text):
        return True
    if requested_name and normalize_text(requested_name) in _GENERIC_REFS:
        return True
    return False


def apply_focus(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    focus_slug: str | None,
) -> bool:
    """Fill entities from the last dish when this turn is a follow-up.

    Leaves named dishes, category browse, recommend, and out-of-scope unchanged.
    """
    if entities.dish_known:
        return False
    if intent not in DISH_SCOPED_INTENTS:
        return False
    dish = dish_by_slug(focus_slug)
    if not dish:
        return False
    if not is_followup_query(query, entities.requested_name):
        return False

    _apply_dish(
        entities,
        dish,
        method="focus",
        score=100.0,
        resolved_from=focus_slug,
    )
    entities.signals.append(f"focus:{dish['slug']}")
    return True
