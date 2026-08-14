"""Phase 7 RAG engine: intent → retrieve → template or grounded LLM answer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import RETRIEVAL_MIN_SCORE
from src.core.entities import Entities, extract_entities
from src.core.format import (
    format_category_browse,
    format_how_to_cook,
    format_ingredients,
    format_out_of_scope,
    format_recommend_template,
    format_refusal,
    format_shopping_list,
    format_substitution,
    format_technique_fallback,
    format_unknown_dish,
    format_unknown_dish_with_alternatives,
)
from src.core.intent import QueryIntent, classify_intent
from src.core.language import QueryLanguage, detect_query_language
from src.core.llm import generate, llm_available
from src.core.prompts import build_messages
from src.core.retrieve import (
    get_chunks_for_slug,
    get_parent_for_category,
    search_for_intent,
)
from src.core.rewrite import rewrite_query


@dataclass
class AnswerResult:
    text: str
    intent: QueryIntent
    lang: QueryLanguage
    confidence: float
    citations: list[str] = field(default_factory=list)
    chunks_used: list[dict[str, Any]] = field(default_factory=list)
    retrieval_score: float = 0.0


def _citations_from_hits(hits: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for hit in hits:
        cite = hit.get("source_citation", "")
        st = hit.get("source_type", "published_textbook")
        label = f"{st}: {cite}" if cite else st
        if label not in seen:
            seen.add(label)
            out.append(label)
    return out


def _top_score(hits: list[dict[str, Any]]) -> float:
    return float(hits[0]["score"]) if hits else 0.0


def _fuzzy_match_hint(text: str, entities: Entities, lang: QueryLanguage) -> str:
    if entities.match_method != "fuzzy" or not entities.resolved_from:
        return text
    if entities.match_score is not None and entities.match_score > 92:
        return text
    dish_label = (entities.dish_name_en or entities.slug or "").split("(")[0].strip()
    if not dish_label:
        return text
    if lang == "kh":
        hint = f'(បានផ្គូផ្គង "{entities.resolved_from}" ទៅ {dish_label})'
    else:
        hint = f'(Matched "{entities.resolved_from}" to {dish_label}.)'
    return f"{hint}\n\n{text}"


def _resolve_parent_hit(hits: list[dict[str, Any]], entities: Entities) -> dict[str, Any] | None:
    for hit in hits:
        if hit.get("chunk_type") == "parent":
            if entities.category and hit.get("category") == entities.category:
                return hit
            return hit
    if entities.category:
        return get_parent_for_category(entities.category)
    return None


def _resolve_ingredients_hit(hits: list[dict[str, Any]], entities: Entities) -> dict[str, Any] | None:
    if entities.slug:
        direct = get_chunks_for_slug(entities.slug, chunk_type="ingredients")
        if direct:
            return direct[0]
    for hit in hits:
        if hit.get("chunk_type") == "ingredients":
            if not entities.slug or hit.get("slug") == entities.slug:
                return hit
    return None


def answer_query(user_query: str, *, lang: str | None = None) -> AnswerResult:
    query = user_query.strip()
    response_lang: QueryLanguage = lang if lang in ("en", "kh") else detect_query_language(query)

    intent_result = classify_intent(query)
    intent = intent_result.intent
    entities = extract_entities(query)

    if intent == "out_of_scope":
        return AnswerResult(
            text=format_out_of_scope(response_lang),
            intent=intent,
            lang=response_lang,
            confidence=intent_result.confidence,
        )

    rewritten = rewrite_query(query, intent, entities)
    hits = search_for_intent(rewritten, intent, entities, top_k=5)
    score = _top_score(hits)
    citations = _citations_from_hits(hits)

    def _unknown_dish_answer() -> AnswerResult:
        name = entities.requested_name or query
        if entities.category:
            text = format_unknown_dish_with_alternatives(name, entities.category, response_lang)
        else:
            text = format_unknown_dish(response_lang)
        return AnswerResult(
            text=text,
            intent=intent,
            lang=response_lang,
            confidence=0.0,
            retrieval_score=score,
        )

    # --- template intents (no LLM) ---
    if intent == "category_browse":
        parent = _resolve_parent_hit(hits, entities)
        if parent:
            return AnswerResult(
                text=format_category_browse(parent, response_lang),
                intent=intent,
                lang=response_lang,
                confidence=intent_result.confidence,
                citations=citations,
                chunks_used=[parent],
                retrieval_score=score,
            )
        return AnswerResult(
            text=format_refusal(response_lang),
            intent=intent,
            lang=response_lang,
            confidence=0.0,
            retrieval_score=score,
        )

    if intent in ("ingredients", "shopping_list"):
        if not entities.dish_known:
            return _unknown_dish_answer()
        ing_hit = _resolve_ingredients_hit(hits, entities)
        if not ing_hit:
            return _unknown_dish_answer()
        if ing_hit:
            fmt = format_shopping_list if intent == "shopping_list" else format_ingredients
            return AnswerResult(
                text=_fuzzy_match_hint(fmt(ing_hit, response_lang), entities, response_lang),
                intent=intent,
                lang=response_lang,
                confidence=intent_result.confidence,
                citations=_citations_from_hits([ing_hit]),
                chunks_used=[ing_hit],
                retrieval_score=score,
            )
        if score < RETRIEVAL_MIN_SCORE:
            return AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            )

    if intent == "how_to_cook":
        if not entities.dish_known:
            return _unknown_dish_answer()
        slug = entities.slug
        if slug and not slug.startswith("_parent"):
            text = format_how_to_cook(slug, response_lang)
            if text:
                steps = get_chunks_for_slug(slug, chunk_type="step")
                return AnswerResult(
                    text=_fuzzy_match_hint(text, entities, response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=_citations_from_hits(steps[:1]),
                    chunks_used=steps,
                    retrieval_score=score,
                )
        return AnswerResult(
            text=format_refusal(response_lang),
            intent=intent,
            lang=response_lang,
            confidence=0.0,
            retrieval_score=score,
        )

    if intent == "substitution":
        if not hits or score < RETRIEVAL_MIN_SCORE * 0.8:
            return AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            )
        return AnswerResult(
            text=format_substitution(hits, entities, response_lang),
            intent=intent,
            lang=response_lang,
            confidence=intent_result.confidence,
            citations=citations,
            chunks_used=hits[:3],
            retrieval_score=score,
        )

    if intent == "recommend":
        parent = _resolve_parent_hit(hits, entities)
        if not parent:
            return AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            )
        dish_names = [d.get("dish_name_en", d.get("slug", "")) for d in parent.get("dishes", [])]
        if llm_available() and len(dish_names) > 1:
            try:
                messages = build_messages(
                    query, hits[:3], intent, response_lang, dish_options=dish_names
                )
                text = generate(messages)
                return AnswerResult(
                    text=text,
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=_citations_from_hits([parent]),
                    chunks_used=[parent],
                    retrieval_score=score,
                )
            except Exception:
                pass
        return AnswerResult(
            text=format_recommend_template(parent, response_lang),
            intent=intent,
            lang=response_lang,
            confidence=intent_result.confidence,
            citations=_citations_from_hits([parent]),
            chunks_used=[parent],
            retrieval_score=score,
        )

    # technique, dish_lookup — LLM if available, else fallback
    if not hits or score < RETRIEVAL_MIN_SCORE:
        return AnswerResult(
            text=format_refusal(response_lang),
            intent=intent,
            lang=response_lang,
            confidence=0.0,
            retrieval_score=score,
        )

    if llm_available():
        try:
            messages = build_messages(query, hits[:4], intent, response_lang)
            text = generate(messages)
            return AnswerResult(
                text=text,
                intent=intent,
                lang=response_lang,
                confidence=intent_result.confidence,
                citations=citations,
                chunks_used=hits[:4],
                retrieval_score=score,
            )
        except Exception:
            pass

    # No LLM: show top retrieved chunks as answer
    if intent == "technique":
        text = format_technique_fallback(hits, response_lang)
    else:
        text = format_technique_fallback(hits, response_lang)

    return AnswerResult(
        text=text or format_refusal(response_lang),
        intent=intent,
        lang=response_lang,
        confidence=intent_result.confidence,
        citations=citations,
        chunks_used=hits[:3],
        retrieval_score=score,
    )
