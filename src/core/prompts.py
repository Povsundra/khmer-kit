"""Grounded LLM prompt templates for Phase 7."""

from __future__ import annotations

from typing import Any

from src.core.intent import QueryIntent
from src.core.language import QueryLanguage, chunk_body

SYSTEM_PROMPT = """You are the Khmer Kitchen Companion — a bilingual cooking assistant grounded in a 14-dish Khmer cookbook corpus.

RULES:
- Answer ONLY using the provided recipe context chunks.
- Match the response language requested (English or Khmer).
- Always end with a line: Source: published_textbook (or family_interview if shown in context).
- NEVER invent recipe steps, ingredients, substitutes, or dish names not in the context.
- If context is insufficient, say explicitly that the cookbook does not cover this.
- Do NOT use general cooking knowledge outside the provided context.
- Keep answers concise (2–6 sentences unless listing steps)."""


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


def build_messages(
    user_query: str,
    hits: list[dict[str, Any]],
    intent: QueryIntent,
    lang: QueryLanguage,
    *,
    dish_options: list[str] | None = None,
) -> list[dict[str, str]]:
    lang_label = "Khmer" if lang == "kh" else "English"
    context = _format_context(hits, lang)

    if intent == "recommend":
        options = dish_options or []
        options_text = "\n".join(f"- {d}" for d in options)
        user_msg = f"""Recommend exactly ONE dish from this closed list for the user.
Do NOT suggest any dish outside this list.

Available dishes:
{options_text}

User question: {user_query}

Context from cookbook:
{context}

Respond in {lang_label}. Give 1–2 sentences why you picked it."""

    elif intent == "technique":
        user_msg = f"""Answer this technique question using ONLY the recipe steps below.
Compare across dishes if multiple chunks are provided.
If the context does not fully answer the question, say what the cookbook shows and what it does not cover.

User question: {user_query}

Context:
{context}

Respond in {lang_label}."""

    else:
        user_msg = f"""Answer the user question using the recipe context below.

User question: {user_query}

Context:
{context}

Respond in {lang_label}."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]
