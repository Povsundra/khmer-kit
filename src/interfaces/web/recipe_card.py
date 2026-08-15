"""Load and render recipe JSON as HTML cards."""

from __future__ import annotations

import html
import json
from functools import lru_cache
from typing import Any

import streamlit as st

from src.config import CHECKLIST_PATH, PROCESSED
from src.core.language import QueryLanguage
from src.interfaces.web.i18n import t


@lru_cache(maxsize=1)
def load_checklist() -> list[dict[str, Any]]:
    return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))


def dishes_for_category(category: str) -> list[dict[str, Any]]:
    return [d for d in load_checklist() if d["category"] == category]


@st.cache_data(show_spinner=False)
def _load_dish_json_cached(category: str, slug: str, file_mtime: float) -> dict[str, Any] | None:
    path = PROCESSED / category / f"{slug}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_dish_json(category: str, slug: str) -> dict[str, Any] | None:
    path = PROCESSED / category / f"{slug}.json"
    if not path.is_file():
        return None
    mtime = path.stat().st_mtime
    return _load_dish_json_cached(category, slug, mtime)


def clear_dish_json_cache() -> None:
    _load_dish_json_cached.clear()


def render_recipe_preview(dish: dict[str, Any], lang: QueryLanguage) -> None:
    """Compact retrieved-recipe preview under chat answers."""
    name_en = dish.get("dish_name_en", "")
    name_kh = dish.get("dish_name_kh", "")
    n_ing = len(dish.get("ingredients", []))
    n_steps = len(dish.get("steps", []))
    title = name_kh if lang == "kh" else name_en.split("(")[0].strip()
    subtitle = t("ing_steps", lang, n_ing=n_ing, n_steps=n_steps)
    with st.container(border=True):
        st.caption(t("retrieved", lang))
        if lang == "kh":
            st.markdown(f'<p class="khmer" style="margin:0;font-weight:600;">{html.escape(title)}</p>', unsafe_allow_html=True)
        else:
            st.markdown(f"**{html.escape(title)}**")
        st.markdown(f'<span style="color:var(--muted);font-size:0.85rem;">{html.escape(subtitle)}</span>', unsafe_allow_html=True)


def render_recipe_preview_html(dish: dict[str, Any], lang: QueryLanguage) -> str:
    """Deprecated: use render_recipe_preview(). Kept for callers that need HTML strings."""
    name_en = dish.get("dish_name_en", "")
    name_kh = dish.get("dish_name_kh", "")
    title = name_kh if lang == "kh" else name_en.split("(")[0].strip()
    n_ing = len(dish.get("ingredients", []))
    n_steps = len(dish.get("steps", []))
    return f"{title} — {n_ing} ingredients · {n_steps} steps"


def render_recipe_card(dish: dict[str, Any], lang: QueryLanguage) -> None:
    name_en = dish.get("dish_name_en", "")
    name_kh = dish.get("dish_name_kh", "")
    ingredients = dish.get("ingredients", [])
    steps = dish.get("steps", [])
    needs_safety = any(s.get("requires_safety_review") for s in steps)

    if lang == "kh":
        ing_items = [i.get("raw_kh", "") for i in ingredients if i.get("raw_kh")]
        step_items = [s.get("text_kh", "") for s in steps if s.get("text_kh")]
        ing_label = "គ្រឿងផ្សំ"
        steps_label = "របៀបធ្វើ"
        safety_msg = "រូបមន្តនេះមានគ្រឿងឬជំហានដែលត្រូវការប្រុងប្រយ័ត្ន (ឧ. ថ្លើម)។"
    else:
        ing_items = [i.get("standardized_en", "") for i in ingredients if i.get("standardized_en")]
        step_items = [s.get("text_en", "") for s in steps if s.get("text_en")]
        ing_label = "Ingredients"
        steps_label = "Steps"
        safety_msg = "This recipe includes ingredients or steps that may need extra care (e.g. liver)."

    source_type = dish.get("source_type", "published_textbook").replace("_", " ")
    citation = dish.get("source_citation", "")

    with st.container(border=True):
        if lang == "kh" and name_kh:
            st.markdown(
                f'<p class="khmer" style="margin:0;font-weight:600;">{html.escape(name_kh)}</p>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="recipe-title-kh" style="margin:0.25rem 0 0.75rem 0;color:var(--muted);">'
                f"{html.escape(name_en)}</p>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"**{name_en}**")
            if name_kh:
                st.markdown(
                    f'<p class="khmer recipe-title-kh" style="margin:0.25rem 0 0.75rem 0;color:var(--muted);">'
                    f"{html.escape(name_kh)}</p>",
                    unsafe_allow_html=True,
                )
        if needs_safety:
            st.warning(safety_msg)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{ing_label}**")
            st.markdown("\n".join(f"- {item}" for item in ing_items))
        with col2:
            st.markdown(f"**{steps_label}**")
            st.markdown("\n".join(f"{i}. {text}" for i, text in enumerate(step_items, start=1)))

        st.caption(f"{t('source', lang)}: {source_type} · {citation}")
