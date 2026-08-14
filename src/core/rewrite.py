"""Rewrite conversational queries into focused retrieval queries."""

from __future__ import annotations

from src.core.entities import Entities
from src.core.intent import QueryIntent


def rewrite_query(user_query: str, intent: QueryIntent, entities: Entities) -> str:
    dish_part = ""
    if entities.slug:
        dish_part = entities.slug.replace("_", " ")
    elif entities.dish_name_en:
        dish_part = entities.dish_name_en.split("(")[0].strip()
    cat_part = entities.category or ""
    ing_part = entities.ingredient or ""

    if intent == "category_browse":
        return f"{cat_part or 'samlor'} category dishes list"
    if intent == "shopping_list":
        return f"{dish_part} ingredients shopping market buy"
    if intent == "ingredients":
        return f"{dish_part} ingredients list"
    if intent == "how_to_cook":
        return f"{dish_part} steps how to cook recipe"
    if intent == "recommend":
        return f"{cat_part or 'cha'} category dishes recommend"
    if intent == "substitution":
        return f"{dish_part} {ing_part} ingredients steps substitute"
    if intent == "technique":
        base = user_query.strip()
        if cat_part and cat_part not in base.lower():
            return f"{cat_part} {base} technique"
        return f"{base} technique cooking steps"
    if entities.slug:
        return f"{dish_part} {user_query}"
    return user_query.strip()
