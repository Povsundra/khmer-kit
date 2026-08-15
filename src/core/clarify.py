"""Grounded clarifying questions — only real categories and dishes."""

from __future__ import annotations

from src.config import CATEGORIES
from src.core.dialogue import DialogueState, PendingSlot, dishes_in_category
from src.core.language import QueryLanguage

CATEGORY_LABELS_EN = {
    "samlor": "samlor (soups)",
    "cha": "cha (stir-fry)",
    "dessert": "dessert",
    "other": "other (salad, omelette)",
}

CATEGORY_LABELS_KH = {
    "samlor": "\u179f\u1798\u17d2\u179b (soup)",
    "cha": "\u1786\u17b6 (stir-fry)",
    "dessert": "\u1794\u1784\u17d2\u1782\u17c2\u1798",
    "other": "\u1795\u17d2\u179f\u17c1\u1784\u17d7 (nhoam, omelette)",
}


def category_options() -> list[str]:
    return list(CATEGORIES)


def dish_options(category: str | None = None) -> list[str]:
    return [d["slug"] for d in dishes_in_category(category)]


def offered_for_slot(slot: PendingSlot, state: DialogueState) -> list[str]:
    if slot == "category":
        return category_options()
    if slot == "dish":
        return dish_options(state.category)
    return []


def format_clarify(
    slot: PendingSlot,
    lang: QueryLanguage,
    state: DialogueState,
) -> str:
    if slot == "category":
        return _ask_category(lang)
    if slot == "dish":
        return _ask_dish(lang, state.category)
    if slot == "ingredient":
        return _ask_ingredient(lang, state)
    return _ask_category(lang)


def _ask_category(lang: QueryLanguage) -> str:
    labels = CATEGORY_LABELS_KH if lang == "kh" else CATEGORY_LABELS_EN
    intro = "This cookbook has 14 Khmer dishes. What type of food would you like to try?"
    outro = "Tell me a type (or a number) and I will recommend from that list."
    lines = [intro, ""]
    for i, cat in enumerate(CATEGORIES, start=1):
        lines.append(f"{i}. {labels[cat]}")
    lines.extend(["", outro])
    return "\n".join(lines)


def _ask_dish(lang: QueryLanguage, category: str | None) -> str:
    dishes = dishes_in_category(category)
    labels = CATEGORY_LABELS_KH if lang == "kh" else CATEGORY_LABELS_EN
    if category:
        label = labels.get(category, category)
        header = f"Which {label} dish do you mean? In this cookbook:"
    else:
        header = (
            "Which dish is this about? You can name one, or pick a type first "
            "(samlor / cha / dessert / other)."
        )
    lines = [header, ""]
    for i, d in enumerate(dishes, start=1):
        en = d["dish_name_en"].split("(")[0].strip()
        if lang == "kh":
            lines.append(f"{i}. {d['dish_name_kh']} ({en})")
        else:
            lines.append(f"{i}. {en}")
    lines.extend(["", "Tell me the dish name or a number."])
    return "\n".join(lines)


def _ask_ingredient(lang: QueryLanguage, state: DialogueState) -> str:
    dish = ""
    if state.slug:
        from src.core.entities import dish_by_slug

        row = dish_by_slug(state.slug)
        if row:
            dish = row["dish_name_en"].split("(")[0].strip()
    if dish:
        return f"Which ingredient are you missing for {dish}?"
    return "Which ingredient do you want to substitute?"
