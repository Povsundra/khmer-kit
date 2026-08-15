"""Conversation focus: resolve this/that/the soup to the last real dish."""

from __future__ import annotations

import re

from src.core.entities import Entities, _apply_dish, _match_ingredient, dish_by_slug
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
    r"\bthe (?:soup|dish|recipe|food)\b|"
    r"\bthis (?:soup|dish|recipe|food)\b|"
    r"\bthat (?:soup|dish|recipe|food)\b|"
    r"របស់វា|នៃវា|ម្ហូបហ្នឹង|ម្ហូបនោះ|ម្ហូបនេះ|សម្លនេះ|"
    r"ហ្នឹង|នោះ|នេះ)",
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
        "this food",
        "that food",
        "the food",
        "soup",
        "dish",
        "recipe",
        "food",
        "khmer",
        "cambodian",
        "khmer food",
        "cambodian food",
        "something",
        "something spicy",
        "a dish",
        "some food",
        "នេះ",
        "នោះ",
        "ហ្នឹង",
        "ម្ហូបនេះ",
        "ម្ហូបនោះ",
        "ម្ហូបហ្នឹង",
        "សម្លនេះ",
        "របស់វា",
        "នៃវា",
    }
)

_INTENT_STRIP_RE = re.compile(
    r"(?:"
    r"how to (?:cook|make|prepare)|"
    r"how do i (?:cook|make|prepare)|"
    r"tell me how to|"
    r"recipe for|steps for|"
    r"(?:list|show|give)(?: me)?(?: all)?(?: the)? ingredients?|"
    r"what are (?:all )?(?:the )?ingredients?|"
    r"ingredients? (?:of|for)|"
    r"\bingredients?\b|"
    r"what(?:'s| is) in|"
    r"what do i need|"
    r"shopping list|"
    r"what (?:do i|should i) buy|"
    r"what to buy|"
    r"go to the market|"
    r"at the market|"
    r"i don'?t have|"
    r"don'?t have|"
    r"substitute for|replacement for|"
    r"\bwithout\b|"
    r"\bshould i\b|"
    r"\bwhen (?:is|do)\b|"
    r"how (?:long|do i know)|"
    r"tell me (?:the )?steps|"
    r"the recipe|"
    r"\brecipe\b|"
    r"\bsteps\b|"
    r"\bplease\b|"
    r"stir.?fry|"
    r"\bdoneness\b|"
    r"របៀបចៀន|របៀបធ្វើ|របៀបដាំ|វិធីធ្វើ|"
    r"គ្រឿ.?ផ្សំ(?:សម្រាប់|នៃ)?|"
    r"បញ្ជី|"
    r"ត្រូវការអ្វីខ្លះ|ត្រូវការ|"
    r"ទិញអ្វីខ្លះ|ទិញ|"
    r"អ្វីខ្លះ|"
    r"គ្មាន|ជំនួស|"
    r"ផ្សារ"
    r")",
    re.I,
)

_FILLER_RE = re.compile(
    r"\b(?:list|show|give|tell|please|pls|all|the|a|an|me|my|for|of|to|and|"
    r"this|that|it|one|ones|some|any|just|also)\b",
    re.I,
)

_CHATTER_RE = re.compile(
    r"\b(?:can|you|could|would|please|pls|just|also|more|stuff|things|"
    r"enumerate|goes|into|about|with|from|need|needed|want|wanted|"
    r"cooking|cook|make|prepare|food|dish|soup|recipe)\b",
    re.I,
)

_PUNCT_RE = re.compile(r"[?.!,;:]+")


def leftover_after_intent_strip(query: str) -> str:
    """Remove intent phrasing and pronouns; leftover is a dish name, ingredient, or empty."""
    text = query.strip()
    if not text:
        return ""
    text = _INTENT_STRIP_RE.sub(" ", text)
    text = _ANAPHORA_RE.sub(" ", text)
    text = _FILLER_RE.sub(" ", text)
    text = _PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def looks_like_named_dish(leftover: str) -> bool:
    """True when leftover looks like a specific dish name, not chatter or an ingredient."""
    text = leftover.strip()
    if not text:
        return False
    norm = normalize_text(text)
    if not norm or norm in _GENERIC_REFS:
        return False
    if _match_ingredient(norm):
        return False
    khmer_chars = sum(1 for c in text if "\u1780" <= c <= "\u17FF")
    if khmer_chars >= 3:
        return True
    cleaned = _CHATTER_RE.sub(" ", text)
    cleaned = _FILLER_RE.sub(" ", cleaned)
    cleaned = _PUNCT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return bool(cleaned)


def is_followup_query(query: str, requested_name: str | None = None) -> bool:
    """True when the query points at a prior dish instead of naming a new one."""
    text = query.strip()
    if not text:
        return False
    if _ANAPHORA_RE.search(text):
        return True
    leftover = leftover_after_intent_strip(text)
    leftover_norm = normalize_text(leftover) if leftover else ""
    if not leftover_norm:
        return True
    if leftover_norm in _GENERIC_REFS:
        return True
    if requested_name and normalize_text(requested_name) in _GENERIC_REFS:
        return True
    if _match_ingredient(leftover_norm):
        return True
    return False


def should_try_followup_rewrite(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    focus_slug: str | None,
) -> bool:
    """True when Layer 1 did not attach a dish but the turn still looks conversational."""
    if entities.dish_known:
        return False
    if intent not in DISH_SCOPED_INTENTS:
        return False
    if not dish_by_slug(focus_slug):
        return False
    return not looks_like_named_dish(leftover_after_intent_strip(query))


def apply_focus(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    focus_slug: str | None,
) -> bool:
    """Fill entities from the last dish when this turn is a follow-up.

    Leaves named dishes, category browse, and out-of-scope unchanged.
    Recommend follow-ups are handled by DialogueState, not this focus attach.
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
