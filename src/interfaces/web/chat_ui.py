"""Chat UI helpers — message history, tags, previews."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from src.core.engine import AnswerResult
from src.core.language import QueryLanguage
from src.interfaces.web.recipe_card import load_dish_json, render_recipe_preview


def _esc(text: str) -> str:
    return html.escape(text)


def init_session_state() -> None:
    defaults = {
        "selected_category": "samlor",
        "selected_slug": None,
        "active_tab": "Chat",
        "ui_lang": "en",
        "messages": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def append_exchange(user_query: str, result: AnswerResult) -> None:
    st.session_state.messages.append({"role": "user", "content": user_query})
    slug = None
    if result.chunks_used:
        slug = result.chunks_used[0].get("slug")
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.text,
            "intent": result.intent,
            "citations": result.citations,
            "slug": slug,
            "category": _slug_category(slug),
            "warning": result.intent in ("substitution", "out_of_scope"),
        }
    )


def _slug_category(slug: str | None) -> str | None:
    if not slug or slug.startswith("_parent"):
        return None
    from src.interfaces.web.recipe_card import load_checklist

    for d in load_checklist():
        if d["slug"] == slug:
            return d["category"]
    return None


def render_tags_html(msg: dict[str, Any]) -> str:
    parts: list[str] = []
    intent = msg.get("intent", "")
    if intent:
        parts.append(f'<span class="tag tag-intent">{_esc(intent.replace("_", " "))}</span>')
    for cite in msg.get("citations") or []:
        short = cite.split(":")[0] if ":" in cite else cite
        parts.append(f'<span class="tag tag-source">{_esc(short.replace("_", " "))}</span>')
    slug = msg.get("slug")
    if slug and not slug.startswith("_parent"):
        parts.append(f'<span class="tag tag-dish">{_esc(slug.replace("_", " "))}</span>')
    return "".join(parts)


def render_chat_history(lang: QueryLanguage) -> None:
    messages = st.session_state.messages
    if not messages:
        st.markdown(
            """
            <div class="welcome-box">
                <p><strong>Ask about a recipe or technique</strong></p>
                <p style="font-size:0.85rem;margin-top:0.5rem;">
                    Select a category and dish in the sidebar, or type a question below.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
            i += 1
            continue

        if msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                tags = render_tags_html(msg)
                if tags:
                    st.markdown(tags, unsafe_allow_html=True)
                slug = msg.get("slug")
                cat = msg.get("category")
                if slug and cat and not slug.startswith("_parent"):
                    dish = load_dish_json(cat, slug)
                    if dish:
                        render_recipe_preview(dish, lang)
            i += 1


def last_focus_slug() -> str | None:
    """Sidebar selection, else the last assistant reply that named a real dish."""
    slug = st.session_state.get("selected_slug")
    if slug and not str(slug).startswith("_parent"):
        return str(slug)
    for msg in reversed(st.session_state.get("messages") or []):
        s = msg.get("slug")
        if msg.get("role") == "assistant" and s and not str(s).startswith("_parent"):
            return str(s)
    return None


def run_ask(query: str, lang: QueryLanguage | None) -> None:
    from src.core.engine import answer_query

    try:
        with st.spinner("Searching the cookbook…"):
            result = answer_query(
                query.strip(),
                lang=lang,
                focus_slug=last_focus_slug(),
            )
    except Exception as exc:
        st.error(
            "Could not answer this question. On first Cloud boot the embedding "
            f"model may still be downloading. Details: {type(exc).__name__}: {exc}"
        )
        return
    append_exchange(query.strip(), result)
    if result.chunks_used:
        slug = result.chunks_used[0].get("slug")
        if slug and not slug.startswith("_parent"):
            st.session_state.selected_slug = slug
            cat = _slug_category(slug)
            if cat:
                st.session_state.selected_category = cat
