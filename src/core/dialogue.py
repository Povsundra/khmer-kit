"""Dialogue state tracking: slots, pending asks, clarify-vs-retrieve policy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from src.config import CATEGORIES
from src.core.context import leftover_after_intent_strip, looks_like_named_dish
from src.core.entities import Entities, _apply_dish, _load_registry, _match_category, dish_by_slug
from src.core.entity_resolve import normalize_text
from src.core.intent import QueryIntent

DialogueAction = Literal["clarify", "retrieve", "refuse"]
PendingSlot = Literal["category", "dish", "ingredient"]

MAX_TURNS = 8

DISH_REQUIRED: frozenset[QueryIntent] = frozenset(
    {
        "ingredients",
        "shopping_list",
        "how_to_cook",
        "substitution",
        "dish_lookup",
    }
)

_ORDINAL = {
    "1": 0,
    "first": 0,
    "one": 0,
    "2": 1,
    "second": 1,
    "two": 1,
    "3": 2,
    "third": 2,
    "three": 2,
    "4": 3,
    "fourth": 3,
    "four": 3,
    "5": 4,
    "fifth": 4,
    "five": 4,
    "6": 5,
    "sixth": 5,
    "six": 5,
}

_AFFIRM_RE = re.compile(
    r"^(?:yes|yeah|yep|y|ok|okay|sure|please|that(?: one)?|this(?: one)?|"
    r"the first(?: one)?|បាទ|ចាស|យល់ព្រម)$",
    re.I,
)

_TOPIC_RE = re.compile(
    r"(?:\brecommend\b|\bsuggest\b|\bhow to\b|\brecipe\b|"
    r"ingredients?|shopping list|what (?:do i|should i) buy|"
    r"actually|instead|"
    r"\u178e\u17c2\u1793\u17b6\u17c6|"
    r"\u179a\u1794\u17c0\u1794\u178a\u17b6\u17c6|"
    r"\u179a\u1794\u17c0\u1794\u1792\u17d2\u179c\u17be|"
    r"\u1782\u17d2\u179a\u17b9\u17a2.?\u1795\u17d2\u179f\u17c6)",
    re.I,
)

_TECHNIQUE_SPECIFIC_RE = re.compile(
    r"\b(?:fish|meat|beef|pork|chicken|garlic|noodle|rice|stir.?fry|"
    r"boil|doneness|70\s*%|tender|golden|crisp)\b|"
    r"ត្រី|សាច់|ខ្ទឹម|មី|បាយ",
    re.I,
)

_GENERIC_REQUEST_RE = re.compile(
    r"(?:khmer food|cambodian food|something spicy|something|"
    r"a dish|some food|what to eat|what should i eat)",
    re.I,
)

_PREFERENCE_RE = re.compile(
    r"(?:spicy|not too sweet|no pork|without pork|hot food|"
    r"i want to eat|i want something|something spicy|"
    r"\u1798\u17d2\u1791\u17c1\u179f)",
    re.I,
)


@dataclass
class DialogueState:
    goal: QueryIntent | None = None
    category: str | None = None
    slug: str | None = None
    ingredient: str | None = None
    constraints: list[str] = field(default_factory=list)
    pending_slot: PendingSlot | None = None
    offered_options: list[str] = field(default_factory=list)
    turns: list[dict[str, str]] = field(default_factory=list)

    def copy(self) -> DialogueState:
        return DialogueState(
            goal=self.goal,
            category=self.category,
            slug=self.slug,
            ingredient=self.ingredient,
            constraints=list(self.constraints),
            pending_slot=self.pending_slot,
            offered_options=list(self.offered_options),
            turns=[dict(t) for t in self.turns],
        )


def is_generic_request(text: str | None) -> bool:
    if not text:
        return False
    norm = normalize_text(text)
    if not norm:
        return True
    if _GENERIC_REQUEST_RE.search(text):
        return True
    return norm in {
        "khmer food",
        "cambodian food",
        "khmer",
        "cambodian",
        "food",
        "dish",
        "something",
        "something spicy",
        "a dish",
        "some food",
    }


def is_new_preference_turn(
    query: str,
    intent: QueryIntent,
    entities: Entities,
) -> bool:
    """True when recommend starts a new want and should not reuse leftover dish."""
    if intent != "recommend":
        return False
    if entities.dish_known:
        return False
    if entities.category:
        return False
    if is_generic_request(query):
        return True
    return bool(_PREFERENCE_RE.search(query or ""))


def named_unknown_dish(entities: Entities) -> bool:
    """True when the user named a specific dish that is not in the corpus."""
    if entities.dish_known or not entities.requested_name:
        return False
    if is_generic_request(entities.requested_name):
        return False
    return looks_like_named_dish(entities.requested_name)


def dishes_in_category(category: str | None) -> list[dict[str, Any]]:
    rows = _load_registry()
    if not category:
        return list(rows)
    return [d for d in rows if d.get("category") == category]


def technique_is_specific(query: str) -> bool:
    return bool(_TECHNIQUE_SPECIFIC_RE.search(query or ""))


def missing_slots(
    state: DialogueState,
    intent: QueryIntent,
    entities: Entities,
    query: str = "",
) -> list[PendingSlot]:
    """Required slots that are still empty for this intent."""
    if intent == "out_of_scope":
        return []
    if intent == "recommend" or intent == "category_browse":
        if entities.dish_known or state.slug:
            return []
        if entities.category or state.category:
            return []
        return ["category"]
    if intent == "technique":
        if entities.dish_known or state.slug:
            return []
        if technique_is_specific(query):
            return []
        return ["dish"]
    if intent == "substitution":
        missing: list[PendingSlot] = []
        if not (entities.dish_known or state.slug):
            missing.append("dish")
        elif not (entities.ingredient or state.ingredient):
            missing.append("ingredient")
        return missing
    if intent in DISH_REQUIRED:
        if entities.dish_known or state.slug:
            return []
        if named_unknown_dish(entities):
            return []
        if not (entities.category or state.category):
            return ["category"]
        return ["dish"]
    return []


def next_action(
    state: DialogueState,
    intent: QueryIntent,
    entities: Entities,
    query: str = "",
) -> DialogueAction:
    if intent == "out_of_scope":
        return "refuse"
    if named_unknown_dish(entities) and intent in DISH_REQUIRED | {"how_to_cook", "dish_lookup"}:
        return "refuse"
    if missing_slots(state, intent, entities, query):
        return "clarify"
    return "retrieve"


def resolve_offered_choice(query: str, offered: list[str]) -> str | None:
    """Map '1' / 'the first one' / a listed name onto an offered slug or category."""
    if not offered:
        return None
    raw = (query or "").strip()
    norm = normalize_text(raw)
    if not norm:
        return None

    if _AFFIRM_RE.match(raw):
        return offered[0]

    for token, idx in _ORDINAL.items():
        if re.search(rf"\b{re.escape(token)}\b", norm) or norm == token:
            if 0 <= idx < len(offered):
                return offered[idx]

    for opt in offered:
        opt_norm = normalize_text(opt.replace("_", " "))
        if opt_norm and opt_norm in norm:
            return opt
        dish = dish_by_slug(opt)
        if not dish:
            continue
        for alias in (
            dish["slug"].replace("_", " "),
            dish["dish_name_en"].split("(")[0].strip(),
            dish["dish_name_kh"],
        ):
            a_norm = normalize_text(alias)
            if a_norm and a_norm in norm:
                return opt
    return None


def _is_topic_change(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    state: DialogueState,
) -> bool:
    if intent == "out_of_scope":
        return True
    if entities.dish_known and intent != state.goal:
        return True
    if is_new_preference_turn(query, intent, entities) and (state.slug or state.category):
        return True
    if intent == "recommend" and _TOPIC_RE.search(query):
        if entities.category and entities.category != state.category:
            return True
        if state.goal and state.goal != "recommend":
            return True
        if entities.category and not entities.dish_known and state.slug:
            return True
    if intent in DISH_REQUIRED and named_unknown_dish(entities):
        return True
    if (
        intent in ("how_to_cook", "ingredients", "shopping_list", "technique", "substitution")
        and _TOPIC_RE.search(query)
        and leftover_after_intent_strip(query)
        and looks_like_named_dish(leftover_after_intent_strip(query))
    ):
        return True
    return False


def try_fill_pending(state: DialogueState, query: str, entities: Entities) -> bool:
    """Fill pending_slot from a short reply. Returns True if something was filled."""
    slot = state.pending_slot
    if not slot:
        return False

    choice = resolve_offered_choice(query, state.offered_options)
    if choice:
        if choice in CATEGORIES:
            state.category = choice
            if slot == "category":
                state.pending_slot = None
            return True
        dish = dish_by_slug(choice)
        if dish:
            _fill_dish(state, dish)
            state.pending_slot = None
            return True

    cat = _match_category(normalize_text(query))
    if cat and slot in ("category", "dish"):
        state.category = cat
        if slot == "category":
            state.pending_slot = None
        return True

    if slot == "dish" and entities.dish_known and entities.slug:
        dish = dish_by_slug(entities.slug)
        if dish:
            _fill_dish(state, dish)
            state.pending_slot = None
            return True

    if slot == "ingredient":
        ing = entities.ingredient
        if not ing:
            leftover = leftover_after_intent_strip(query)
            ing = leftover.strip() if leftover else None
        if ing:
            state.ingredient = ing
            state.pending_slot = None
            return True

    return False


def _fill_dish(state: DialogueState, dish: dict[str, Any]) -> None:
    state.slug = dish["slug"]
    state.category = dish.get("category") or state.category


def apply_dialogue(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    state: DialogueState,
) -> tuple[QueryIntent, Entities, DialogueState, bool]:
    """Update state from this turn. Returns (intent, entities, state, filled_slot)."""
    state = state.copy()
    filled = False

    if intent == "dish_lookup" and not entities.dish_known and is_generic_request(query):
        intent = "recommend"

    if state.pending_slot and not _is_topic_change(query, intent, entities, state):
        filled = try_fill_pending(state, query, entities)
        if filled:
            intent = state.goal or intent
            state.pending_slot = None if state.pending_slot == "category" or state.slug or state.ingredient else state.pending_slot
            sync_entities_from_state(entities, state)
            return intent, entities, state, True

    if _is_topic_change(query, intent, entities, state):
        if intent == "recommend" and entities.category and not entities.dish_known:
            state.slug = None
        state.pending_slot = None
        state.offered_options = []

    if is_new_preference_turn(query, intent, entities):
        state.slug = None
        if not entities.category:
            state.category = None
        state.pending_slot = None
        state.offered_options = []

    if named_unknown_dish(entities):
        state.slug = None
        if not entities.category:
            state.category = None
        state.pending_slot = None
        state.offered_options = []

    if intent != "dish_lookup" or entities.dish_known:
        state.goal = intent

    if entities.category:
        state.category = entities.category
    if entities.dish_known and entities.slug:
        state.slug = entities.slug
        state.category = entities.category or state.category
    if entities.ingredient:
        state.ingredient = entities.ingredient

    sync_entities_from_state(entities, state)
    return intent, entities, state, filled


def sync_entities_from_state(entities: Entities, state: DialogueState) -> None:
    """Copy remembered slots onto entities so retrieve/templates see them."""
    if not entities.dish_known and state.slug:
        dish = dish_by_slug(state.slug)
        if dish:
            _apply_dish(
                entities,
                dish,
                method="focus",
                score=100.0,
                resolved_from=state.slug,
            )
            entities.signals.append(f"dialogue:{dish['slug']}")
    if not entities.category and state.category:
        entities.category = state.category
        entities.signals.append(f"dialogue_category:{state.category}")
    if not entities.ingredient and state.ingredient:
        entities.ingredient = state.ingredient


def remember_user_turn(state: DialogueState, query: str) -> None:
    state.turns.append({"role": "user", "content": query})
    _trim_turns(state)


def remember_assistant_turn(state: DialogueState, text: str) -> None:
    state.turns.append({"role": "assistant", "content": text})
    _trim_turns(state)


def remember_retrieved_dish(
    state: DialogueState,
    intent: QueryIntent,
    entities: Entities,
    hits: list[dict[str, Any]],
) -> None:
    """After a successful answer, keep the dish so follow-ups do not re-ask."""
    state.pending_slot = None
    if entities.slug and not str(entities.slug).startswith("_parent"):
        state.slug = entities.slug
        state.category = entities.category or state.category
        return
    if intent == "recommend" and hits:
        parent = hits[0]
        dishes = parent.get("dishes") or []
        if dishes:
            pick = dishes[0].get("slug")
            if pick:
                state.slug = pick
            state.category = parent.get("category") or state.category
            state.offered_options = [d.get("slug") for d in dishes if d.get("slug")]


def set_pending(
    state: DialogueState,
    slot: PendingSlot,
    offered: list[str],
) -> None:
    state.pending_slot = slot
    state.offered_options = list(offered)


def _trim_turns(state: DialogueState) -> None:
    if len(state.turns) > MAX_TURNS:
        state.turns = state.turns[-MAX_TURNS:]
