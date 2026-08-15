"""Grounded LLM prompt templates for Phase 7 + conversational clarify."""

from __future__ import annotations

from typing import Any

from src.core.intent import QueryIntent
from src.core.language import QueryLanguage, chunk_body

SYSTEM_PROMPT = """You are a Khmer food consultant for a 14-dish cookbook. Talk like a helpful kitchen guide, not a search engine.

RULES:
- Chat naturally. Ask at most ONE clarifying question.
- Answer ONLY using the provided recipe context chunks when giving facts.
- Name only dishes that appear in the context or the allowed list.
- Match the response language requested (English or Khmer).
- Always end factual answers with a line: Source: published_textbook (or family_interview if shown in context).
- NEVER invent recipe steps, ingredients, substitutes, dish names, or heat/sweetness ratings.
- If the user asked for spicy, not-too-sweet, or no pork, say the cookbook does not rate those. Only mention dishes whose retrieved text actually talks about chili, pepper, sugar, or pork.
- If context is insufficient, say the cookbook does not cover this.
- Do NOT use general cooking knowledge outside the provided context.
- Keep answers concise (2–6 sentences unless listing steps)."""

CLARIFY_SYSTEM = """You are a Khmer food consultant. Rephrase a clarifying question so it sounds natural.

RULES:
- You may ONLY mention the options listed. Do not add dishes, categories, or facts.
- Ask exactly one question.
- Do not answer a cooking question. Do not recommend a dish yet.
- If the user mentioned spicy, sweetness, or no pork, you may say this cookbook does not rate heat, sweetness, or diet.
- Match the requested language.
- Keep it short (3–6 sentences including the option list)."""


def _format_context(hits: list[dict[str, Any]], lang: QueryLanguage) -> str:
    blocks: list[str] = []
    for i, hit in enumerate(hits, start=1):
        name = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
        step = hit.get("step")
        ctype = hit.get("chunk_type", "")
        label = f"step {step}" if step else ctype
        body = chunk_body(hit, lang)
        cite = hit.get("source_citation", "")
        blocks.append(f"[{i}] {name} ({label})\n{body}\nCitation: {cite}")
    return "\n\n".join(blocks)


def _format_history(history: list[dict[str, str]] | None) -> str:
    if not history:
        return ""
    lines = ["Recent conversation:"]
    for turn in history[-6:]:
        role = turn.get("role", "user")
        content = (turn.get("content") or "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def build_messages(
    user_query: str,
    hits: list[dict[str, Any]],
    intent: QueryIntent,
    lang: QueryLanguage,
    *,
    dish_options: list[str] | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    lang_label = "Khmer" if lang == "kh" else "English"
    context = _format_context(hits, lang)
    history_block = _format_history(history)
    history_prefix = f"{history_block}\n\n" if history_block else ""

    if intent == "recommend":
        options = dish_options or []
        options_text = "\n".join(f"- {d}" for d in options)
        user_msg = f"""{history_prefix}Recommend exactly ONE dish from this closed list for the user.
Do NOT suggest any dish outside this list. You may refer to what they already said they wanted.
If they asked for spicy, not-too-sweet, or no pork, say the cookbook has no such rating and only pick a dish whose context mentions chili, pepper, sugar, or pork. If none match, say so and ask samlor / cha / other.

Available dishes:
{options_text}

User question: {user_query}

Context from cookbook:
{context}

Respond in {lang_label}. Give 1–2 sentences why you picked it."""

    elif intent == "technique":
        user_msg = f"""{history_prefix}Answer this technique question using ONLY the recipe steps below.
Compare across dishes if multiple chunks are provided.
If the context does not fully answer the question, say what the cookbook shows and what it does not cover.

User question: {user_query}

Context:
{context}

Respond in {lang_label}."""

    else:
        user_msg = f"""{history_prefix}Answer the user question using the recipe context below.

User question: {user_query}

Context:
{context}

Respond in {lang_label}."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]


def build_clarify_messages(
    user_query: str,
    template: str,
    lang: QueryLanguage,
    *,
    offered_options: list[str] | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    lang_label = "Khmer" if lang == "kh" else "English"
    options = offered_options or []
    options_text = "\n".join(f"- {o}" for o in options) if options else "(see the draft question)"
    history_block = _format_history(history)
    history_prefix = f"{history_block}\n\n" if history_block else ""
    user_msg = f"""{history_prefix}User said: {user_query}

Allowed options (do not invent any other):
{options_text}

Draft question (keep the same options; you may rephrase):
{template}

Respond in {lang_label}. Output only the clarifying question."""
    return [
        {"role": "system", "content": CLARIFY_SYSTEM},
        {"role": "user", "content": user_msg},
    ]
