"""Phase 7 RAG engine: intent → retrieve → template or grounded LLM answer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import CATEGORIES, RETRIEVAL_MIN_SCORE
from src.core.clarify import format_clarify, offered_for_slot
from src.core.context import apply_focus, should_try_followup_rewrite
from src.core.dialogue import (
    DialogueState,
    apply_dialogue,
    missing_slots,
    named_unknown_dish,
    next_action,
    remember_assistant_turn,
    remember_retrieved_dish,
    remember_user_turn,
    set_pending,
)
from src.core.entities import Entities, _apply_dish, dish_by_slug, extract_entities
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
    menu_dish_label,
)
from src.core.intent import QueryIntent, classify_intent
from src.core.language import QueryLanguage, detect_query_language
from src.core.llm import generate, llm_available
from src.core.prompts import build_clarify_messages, build_messages
from src.core.retrieve import (
    get_chunks_for_slug,
    get_parent_for_category,
    search,
    search_for_intent,
)
from src.core.rewrite import UnderstandResult, rewrite_followup_query, rewrite_query, understand_turn


@dataclass
class AnswerResult:
    text: str
    intent: QueryIntent
    lang: QueryLanguage
    confidence: float
    citations: list[str] = field(default_factory=list)
    chunks_used: list[dict[str, Any]] = field(default_factory=list)
    retrieval_score: float = 0.0
    action: str = "answer"
    state: DialogueState = field(default_factory=DialogueState)


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


def _context_hint(text: str, entities: Entities, lang: QueryLanguage) -> str:
    if entities.match_method == "focus":
        dish_label = (entities.dish_name_en or entities.slug or "").split("(")[0].strip()
        if not dish_label:
            return text
        if lang == "kh":
            hint = f"(និយាយពី {entities.dish_name_kh or dish_label})"
        else:
            hint = f"(About {dish_label})"
        return f"{hint}\n\n{text}"
    return _fuzzy_match_hint(text, entities, lang)


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


def _finish(
    result: AnswerResult,
    state: DialogueState,
    *,
    action: str | None = None,
) -> AnswerResult:
    if action:
        result.action = action
    result.state = state
    remember_assistant_turn(state, result.text)
    return result


def _is_known_dish_template(intent: QueryIntent, entities: Entities) -> bool:
    return bool(
        entities.dish_known
        and intent in ("ingredients", "shopping_list", "how_to_cook")
        and entities.slug
        and not str(entities.slug).startswith("_parent")
    )


def _should_understand(intent: QueryIntent, entities: Entities) -> bool:
    if intent == "out_of_scope":
        return False
    if _is_known_dish_template(intent, entities):
        return False
    if named_unknown_dish(entities) and intent in (
        "dish_lookup",
        "how_to_cook",
        "ingredients",
        "shopping_list",
        "substitution",
    ):
        return False
    if intent in ("recommend", "technique", "category_browse", "substitution"):
        return True
    return intent in ("ingredients", "shopping_list", "how_to_cook", "dish_lookup") and not entities.dish_known


def _apply_understand_slots(
    result: UnderstandResult,
    state: DialogueState,
    entities: Entities,
) -> None:
    if result.slug:
        dish = dish_by_slug(result.slug)
        if dish:
            _apply_dish(
                entities,
                dish,
                method="understand",
                score=100.0,
                resolved_from=result.slug,
            )
            state.slug = dish["slug"]
            state.category = dish.get("category") or state.category
    if result.category and result.category in CATEGORIES:
        entities.category = entities.category or result.category
        state.category = result.category


def _enough_to_retrieve(intent: QueryIntent, entities: Entities, state: DialogueState) -> bool:
    if entities.dish_known:
        return True
    if intent == "recommend" and (entities.category or state.category):
        return True
    if intent == "category_browse" and (entities.category or state.category):
        return True
    return False


def _dish_names_from_hits(hits: list[dict[str, Any]], lang: QueryLanguage = "en") -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for hit in hits:
        if hit.get("chunk_type") == "parent":
            for dish in hit.get("dishes") or []:
                name = menu_dish_label(dish, lang)
                if name and name not in seen:
                    seen.add(name)
                    names.append(name)
            continue
        name = menu_dish_label(hit, lang)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _clarify_answer(
    query: str,
    intent: QueryIntent,
    entities: Entities,
    state: DialogueState,
    lang: QueryLanguage,
    confidence: float,
    *,
    question: str | None = None,
) -> AnswerResult:
    slots = missing_slots(state, intent, entities, query)
    slot = slots[0] if slots else "category"
    offered = offered_for_slot(slot, state)
    set_pending(state, slot, offered)
    template = format_clarify(slot, lang, state)
    text = (question or "").strip() or template
    if text == template and llm_available():
        try:
            messages = build_clarify_messages(
                query,
                template,
                lang,
                offered_options=offered,
                history=state.turns,
            )
            text = generate(messages, temperature=0.3)
        except Exception:
            text = template
    return _finish(
        AnswerResult(
            text=text,
            intent=intent,
            lang=lang,
            confidence=confidence,
            action="clarify",
            state=state,
        ),
        state,
        action="clarify",
    )


def answer_query(
    user_query: str,
    *,
    lang: str | None = None,
    focus_slug: str | None = None,
    prior_query: str | None = None,
    state: DialogueState | None = None,
) -> AnswerResult:
    query = user_query.strip()
    response_lang: QueryLanguage = lang if lang in ("en", "kh") else detect_query_language(query)
    state = (state.copy() if state else DialogueState())
    remember_user_turn(state, query)

    intent_result = classify_intent(query)
    intent = intent_result.intent
    entities = extract_entities(query)
    if state.pending_slot:
        effective_focus = state.slug
    else:
        effective_focus = focus_slug or state.slug
    if not state.pending_slot:
        apply_focus(query, intent, entities, effective_focus)

    if (
        not entities.dish_known
        and should_try_followup_rewrite(query, intent, entities, effective_focus)
        and llm_available()
    ):
        try:
            rewritten = rewrite_followup_query(
                query,
                focus_slug=effective_focus or "",
                prior_query=prior_query,
            )
        except Exception:
            rewritten = None
        if rewritten:
            query = rewritten
            intent_result = classify_intent(query)
            intent = intent_result.intent
            entities = extract_entities(query)
            apply_focus(query, intent, entities, effective_focus)
            if entities.slug and not dish_by_slug(entities.slug):
                entities.dish_known = False
                entities.slug = None

    intent, entities, state, _filled = apply_dialogue(query, intent, entities, state)

    if (
        intent == "dish_lookup"
        and entities.dish_known
        and entities.slug
        and not str(entities.slug).startswith("_parent")
    ):
        intent = "how_to_cook"
        state.goal = intent

    if intent == "out_of_scope":
        return _finish(
            AnswerResult(
                text=format_out_of_scope(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=intent_result.confidence,
                action="refuse",
            ),
            state,
            action="refuse",
        )

    if named_unknown_dish(entities) and intent in (
        "dish_lookup",
        "how_to_cook",
        "ingredients",
        "shopping_list",
        "substitution",
    ):
        name = entities.requested_name
        if entities.category:
            text = format_unknown_dish_with_alternatives(name, entities.category, response_lang)
        else:
            text = format_unknown_dish(response_lang, name)
        return _finish(
            AnswerResult(
                text=text,
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=0.0,
                action="refuse",
            ),
            state,
            action="refuse",
        )

    understood_query: str | None = None
    if llm_available() and _should_understand(intent, entities):
        try:
            understood = understand_turn(
                query,
                intent=intent,
                history=state.turns,
                last_slug=state.slug,
                last_category=state.category,
            )
        except Exception:
            understood = None
        if understood:
            _apply_understand_slots(understood, state, entities)
            if understood.action == "ask" and not _enough_to_retrieve(intent, entities, state):
                return _clarify_answer(
                    query,
                    intent,
                    entities,
                    state,
                    response_lang,
                    intent_result.confidence,
                    question=understood.question,
                )
            if (
                understood.action == "retrieve"
                and intent == "recommend"
                and not _enough_to_retrieve(intent, entities, state)
            ):
                return _clarify_answer(
                    query,
                    intent,
                    entities,
                    state,
                    response_lang,
                    intent_result.confidence,
                    question=understood.question,
                )
            if understood.query:
                understood_query = understood.query

    action = next_action(state, intent, entities, query)
    if action == "clarify" and not understood_query:
        return _clarify_answer(
            query, intent, entities, state, response_lang, intent_result.confidence
        )

    # Known-dish templates read the docstore by slug; skip embedding search.
    template_from_slug = _is_known_dish_template(intent, entities)
    if template_from_slug:
        hits: list[dict[str, Any]] = []
        score = 1.0
        citations: list[str] = []
    elif understood_query:
        hits = search(understood_query, mode="hybrid", top_k=5)
        score = _top_score(hits)
        citations = _citations_from_hits(hits)
    else:
        rewritten = rewrite_query(query, intent, entities)
        hits = search_for_intent(rewritten, intent, entities, top_k=5)
        score = _top_score(hits)
        citations = _citations_from_hits(hits)

    def _unknown_dish_answer() -> AnswerResult:
        name = entities.requested_name or query
        if entities.category:
            text = format_unknown_dish_with_alternatives(name, entities.category, response_lang)
        else:
            text = format_unknown_dish(response_lang, name)
        return _finish(
            AnswerResult(
                text=text,
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
                action="refuse",
            ),
            state,
            action="refuse",
        )

    def _ok(result: AnswerResult, *, refuse: bool = False) -> AnswerResult:
        if not refuse and result.chunks_used:
            remember_retrieved_dish(state, intent, entities, result.chunks_used)
        return _finish(result, state, action="refuse" if refuse else "answer")

    # --- template intents (no LLM) ---
    if intent == "category_browse":
        parent = _resolve_parent_hit(hits, entities)
        if parent:
            return _ok(
                AnswerResult(
                    text=format_category_browse(parent, response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=citations,
                    chunks_used=[parent],
                    retrieval_score=score,
                )
            )
        return _ok(
            AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            ),
            refuse=True,
        )

    if intent in ("ingredients", "shopping_list"):
        if not entities.dish_known:
            return _unknown_dish_answer()
        ing_hit = _resolve_ingredients_hit(hits, entities)
        if not ing_hit:
            return _unknown_dish_answer()
        if ing_hit:
            fmt = format_shopping_list if intent == "shopping_list" else format_ingredients
            return _ok(
                AnswerResult(
                    text=_context_hint(fmt(ing_hit, response_lang), entities, response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=_citations_from_hits([ing_hit]),
                    chunks_used=[ing_hit],
                    retrieval_score=score,
                )
            )
        if score < RETRIEVAL_MIN_SCORE:
            return _ok(
                AnswerResult(
                    text=format_refusal(response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=0.0,
                    retrieval_score=score,
                ),
                refuse=True,
            )

    if intent == "how_to_cook":
        if not entities.dish_known:
            return _unknown_dish_answer()
        slug = entities.slug
        if slug and not slug.startswith("_parent"):
            text = format_how_to_cook(slug, response_lang)
            if text:
                steps = get_chunks_for_slug(slug, chunk_type="step")
                return _ok(
                    AnswerResult(
                        text=_context_hint(text, entities, response_lang),
                        intent=intent,
                        lang=response_lang,
                        confidence=intent_result.confidence,
                        citations=_citations_from_hits(steps[:1]),
                        chunks_used=steps,
                        retrieval_score=score,
                    )
                )
        return _ok(
            AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            ),
            refuse=True,
        )

    if intent == "substitution":
        if not hits or score < RETRIEVAL_MIN_SCORE * 0.8:
            return _ok(
                AnswerResult(
                    text=format_refusal(response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=0.0,
                    retrieval_score=score,
                ),
                refuse=True,
            )
        return _ok(
            AnswerResult(
                text=format_substitution(hits, entities, response_lang),
                intent=intent,
                lang=response_lang,
                confidence=intent_result.confidence,
                citations=citations,
                chunks_used=hits[:3],
                retrieval_score=score,
            )
        )

    if intent == "recommend":
        parent = _resolve_parent_hit(hits, entities)
        dish_names = _dish_names_from_hits(hits, response_lang)
        if not dish_names and parent:
            dish_names = [
                menu_dish_label(d, response_lang) for d in parent.get("dishes", [])
            ]
        context_hits = hits[:4] if hits else ([parent] if parent else [])
        if not context_hits:
            return _ok(
                AnswerResult(
                    text=format_refusal(response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=0.0,
                    retrieval_score=score,
                ),
                refuse=True,
            )
        if llm_available() and dish_names:
            try:
                messages = build_messages(
                    query,
                    context_hits,
                    intent,
                    response_lang,
                    dish_options=dish_names,
                    history=state.turns,
                )
                text = generate(messages)
                return _ok(
                    AnswerResult(
                        text=text,
                        intent=intent,
                        lang=response_lang,
                        confidence=intent_result.confidence,
                        citations=_citations_from_hits(context_hits),
                        chunks_used=context_hits,
                        retrieval_score=score,
                    )
                )
            except Exception:
                pass
        if parent:
            return _ok(
                AnswerResult(
                    text=format_recommend_template(parent, response_lang),
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=_citations_from_hits([parent]),
                    chunks_used=[parent],
                    retrieval_score=score,
                )
            )
        return _ok(
            AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            ),
            refuse=True,
        )

    # technique, dish_lookup — LLM if available, else fallback
    if not hits or score < RETRIEVAL_MIN_SCORE:
        return _ok(
            AnswerResult(
                text=format_refusal(response_lang),
                intent=intent,
                lang=response_lang,
                confidence=0.0,
                retrieval_score=score,
            ),
            refuse=True,
        )

    if llm_available():
        try:
            messages = build_messages(
                query, hits[:4], intent, response_lang, history=state.turns
            )
            text = generate(messages)
            return _ok(
                AnswerResult(
                    text=text,
                    intent=intent,
                    lang=response_lang,
                    confidence=intent_result.confidence,
                    citations=citations,
                    chunks_used=hits[:4],
                    retrieval_score=score,
                )
            )
        except Exception:
            pass

    text = format_technique_fallback(hits, response_lang)
    return _ok(
        AnswerResult(
            text=text or format_refusal(response_lang),
            intent=intent,
            lang=response_lang,
            confidence=intent_result.confidence,
            citations=citations,
            chunks_used=hits[:3],
            retrieval_score=score,
        )
    )
