"""Rewrite conversational queries into focused retrieval queries."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from src.config import CATEGORIES
from src.core.entities import Entities, _load_registry, dish_by_slug
from src.core.intent import QueryIntent
from src.core.llm import generate

_REWRITE_SYSTEM = """You are a linguistic router and query rewriter for the Khmer Kitchen Companion RAG system. Your ONLY job is to resolve conversational context into clean, standalone search queries.

## Goal
Take a user's follow-up question and rewrite it so that a vector database can understand exactly what dish and topic they are asking about, without needing the chat history.

## Instructions
1. Read the chat history to understand the current cooking topic.
2. Read the latest user question.
3. If the latest question uses pronouns (វា, it, its, this, that, ហ្នឹង, របស់វា) or implies the dish from the previous turn, replace those vague words with the actual dish name.
4. Fix obvious spelling or transliteration mistakes in Khmer or English.
5. If the latest question is a completely new question that does not rely on history, leave it mostly as-is and only correct typos.
6. Use a dish name from the allowed list only. Never invent a dish outside that list. If the latest question names a different allowed dish, keep that dish's name.
7. Answer in the same language as the latest user question.
8. CRITICAL RULE: Output ONLY the rewritten search string on a single line. Do not answer the cooking question. Do not add introductory text, quotes, or conversational filler.

## Examples
History: "របៀបឆាមីសួរ"
Latest: "គ្រឿហផ្សំរបស់វា"
Output: គ្រឿងផ្សំរបស់ឆាមីសួរ

History: "How do I make samlor machu pralit?"
Latest: "how long to cook the fish?"
Output: How long to cook the fish for samlor machu pralit

History: "What are the ingredients of num ansom chrouk?"
Latest: "Can I use chicken instead?"
Output: Can I use chicken instead of pork for num ansom chrouk"""

_MAX_REWRITE_CHARS = 200
_LABEL_RE = re.compile(r"^(?:output|rewritten(?: query| question)?|query|answer)\s*[:：]\s*", re.I)

UnderstandAction = Literal["ask", "retrieve"]

_UNDERSTAND_SYSTEM = """You are a Khmer food consultant for a 14-dish cookbook RAG system.
Your ONLY job is to understand what the user wants, then either ask ONE question or write a standalone search query.
You do not cook from memory. You do not invent dishes, heat ratings, nutrition, prices, or restaurants.

## Decide
- ask: the user want is unclear (no dish, no category, or a preference like spicy/not sweet/no pork with no type yet).
- retrieve: you know enough to search the cookbook.

## When asking
- Ask exactly one question.
- For a missing type, offer only: samlor, cha, dessert, other.
- If they asked for spicy / not sweet / no pork, say this cookbook does not rate heat, sweetness, or diet — it only has recipe text.
- Do not recommend a dish yet.

## When retrieving
- Write a standalone search string a vector index can use.
- Bind pronouns (it, this, that, its, this dish) to the last allowed dish.
- Use only allowed dish names. Never invent a dish.
- For spicy / chili / hot, search with words that appear in recipes: chili, chili leaves, pepper, kroeung, ម្ទេស — not "spicy rating".
- For not-sweet / no-pork, search with sugar / pork / ស្ករ / សាច់ជ្រូក only if useful; do not invent substitutes.

## Output
Return ONLY a JSON object, no markdown, no extra text:
{"action":"ask","question":"...","query":null,"category":null,"slug":null}
{"action":"retrieve","question":null,"query":"...","category":"samlor","slug":"samlor_machu_pralit"}
category must be one of samlor, cha, dessert, other, or null.
slug must be an allowed slug or null.
"""


@dataclass
class UnderstandResult:
    action: UnderstandAction
    query: str | None = None
    question: str | None = None
    category: str | None = None
    slug: str | None = None


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
        if cat_part:
            return f"{cat_part} category dishes recommend"
        return user_query.strip()
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


def _clean_rewrite(text: str) -> str | None:
    """Keep one query line; a preamble or a full cooking answer must not become the query.

    Scans bottom-up because a chatty model puts the query after its lead-in line.
    """
    for raw_line in reversed((text or "").splitlines()):
        line = _LABEL_RE.sub("", raw_line.strip()).strip().strip('"\u201c\u201d\'')
        if not line or line.endswith(":") or len(line) > _MAX_REWRITE_CHARS:
            continue
        return line
    return None


def _allowed_dish_lines() -> str:
    return "\n".join(
        f"- {d['dish_name_en']} / {d['dish_name_kh']} ({d['slug']})"
        for d in _load_registry()
    )


def _format_history_block(history: list[dict[str, str]] | None) -> str:
    if not history:
        return "(none)"
    lines: list[str] = []
    for turn in history[-6:]:
        role = turn.get("role", "user")
        content = (turn.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(none)"


def _normalize_slot(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"null", "none"}:
        return None
    return text


def _parse_understand(text: str) -> UnderstandResult | None:
    raw = (text or "").strip()
    if not raw:
        return None
    start = raw.find("{")
    end = raw.rfind("}")
    data: dict[str, Any] | None = None
    if start >= 0 and end > start:
        try:
            parsed = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            data = parsed
    if data is None:
        cleaned = _clean_rewrite(raw)
        if cleaned:
            return UnderstandResult(action="retrieve", query=cleaned)
        return None

    action = str(data.get("action") or "").strip().lower()
    if action not in ("ask", "retrieve"):
        return None
    query = _normalize_slot(data.get("query"))
    question = _normalize_slot(data.get("question"))
    category = _normalize_slot(data.get("category"))
    slug = _normalize_slot(data.get("slug"))
    if category and category not in CATEGORIES:
        category = None
    if slug and not dish_by_slug(slug):
        slug = None
    if action == "ask":
        if not question or len(question) > 800:
            return None
        return UnderstandResult(action="ask", question=question, category=category, slug=slug)
    if not query or len(query) > _MAX_REWRITE_CHARS:
        return None
    return UnderstandResult(
        action="retrieve",
        query=query,
        category=category,
        slug=slug,
    )


def understand_turn(
    query: str,
    *,
    intent: QueryIntent,
    history: list[dict[str, str]] | None = None,
    last_slug: str | None = None,
    last_category: str | None = None,
) -> UnderstandResult | None:
    """Understand the user want, then ask once or write a retrieval query."""
    last_dish = "(none)"
    dish = dish_by_slug(last_slug)
    if dish:
        last_dish = f"{dish['dish_name_en']} / {dish['dish_name_kh']} ({dish['slug']})"
    cat = last_category if last_category in CATEGORIES else "(none)"
    user_msg = (
        f"Allowed dishes (do not invent any other dish):\n{_allowed_dish_lines()}\n\n"
        f"Allowed categories: samlor, cha, dessert, other\n"
        f"Last dish in focus: {last_dish}\n"
        f"Last category: {cat}\n"
        f"Rule-classified intent: {intent}\n\n"
        f"Chat history:\n{_format_history_block(history)}\n\n"
        f"Latest user question: {query.strip()}\n\n"
        "Return the JSON object only."
    )
    text = generate(
        [
            {"role": "system", "content": _UNDERSTAND_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )
    return _parse_understand(text)


def rewrite_followup_query(
    query: str,
    *,
    focus_slug: str,
    prior_query: str | None = None,
) -> str | None:
    """Constrained LLM rewrite: bind a follow-up to the last dish or the 14-name list."""
    dish = dish_by_slug(focus_slug)
    if not dish:
        return None
    last_dish = f"{dish['dish_name_en']} / {dish['dish_name_kh']} ({dish['slug']})"
    prior = (prior_query or "").strip() or "(none)"
    user_msg = (
        f"Allowed dishes (do not invent any other dish):\n{_allowed_dish_lines()}\n\n"
        f"Last dish in focus: {last_dish}\n\n"
        f"Chat history — previous user question: {prior}\n"
        f"Latest user question: {query.strip()}\n\n"
        "Output the rewritten search string only."
    )
    text = generate(
        [
            {"role": "system", "content": _REWRITE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )
    return _clean_rewrite(text)
