"""Load and render recipe JSON as HTML cards."""

from __future__ import annotations

import html
import json
from functools import lru_cache
from typing import Any

import streamlit as st

from src.config import CHECKLIST_PATH, PROCESSED
from src.core.language import QueryLanguage


@lru_cache(maxsize=1)
def load_checklist() -> list[dict[str, Any]]:
    return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))


def dishes_for_category(category: str) -> list[dict[str, Any]]:
    return [d for d in load_checklist() if d["category"] == category]


@st.cache_data(show_spinner=False)
def load_dish_json(category: str, slug: str) -> dict[str, Any] | None:
    path = PROCESSED / category / f"{slug}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _esc(text: str) -> str:
    return html.escape(text)


def render_recipe_preview_html(dish: dict[str, Any], lang: QueryLanguage) -> str:
    name_en = dish.get("dish_name_en", "")
    name_kh = dish.get("dish_name_kh", "")
    n_ing = len(dish.get("ingredients", []))
    n_steps = len(dish.get("steps", []))
    title = name_kh if lang == "kh" else name_en.split("(")[0].strip()
    subtitle = f"{n_ing} ingredients · {n_steps} steps"
    return f"""
    <div class="card-preview">
        <div class="card-preview-label">Retrieved recipe</div>
        <div class="recipe-title khmer">{_esc(title)}</div>
        <div style="color: var(--muted); font-size: 0.85rem;">{_esc(subtitle)}</div>
    </div>
    """


def render_recipe_card(dish: dict[str, Any], lang: QueryLanguage) -> None:
    name_en = dish.get("dish_name_en", "")
    name_kh = dish.get("dish_name_kh", "")
    ingredients = dish.get("ingredients", [])
    steps = dish.get("steps", [])
    needs_safety = any(s.get("requires_safety_review") for s in steps)

    if lang == "kh":
        ing_items = [_esc(i.get("raw_kh", "")) for i in ingredients]
        step_items = [_esc(s.get("text_kh", "")) for s in steps]
        ing_label = "គ្រឿងផ្សំ"
        steps_label = "របៀបធ្វើ"
        safety_msg = "រូបមន្តនេះមានគ្រឿងឬជំហានដែលត្រូវការប្រុងប្រយ័ត្ន (ឧ. ថ្លើម)។"
    else:
        ing_items = [_esc(i.get("standardized_en", "")) for i in ingredients]
        step_items = [_esc(s.get("text_en", "")) for s in steps]
        ing_label = "Ingredients"
        steps_label = "Steps"
        safety_msg = "This recipe includes ingredients or steps that may need extra care (e.g. liver)."

    ing_html = "".join(f"<li>{item}</li>" for item in ing_items if item)
    steps_html = "".join(f"<li>{item}</li>" for item in step_items if item)

    safety_html = ""
    if needs_safety:
        safety_html = f'<div class="safety-banner">{_esc(safety_msg)}</div>'

    source_type = _esc(dish.get("source_type", "published_textbook").replace("_", " "))
    citation = _esc(dish.get("source_citation", ""))

    st.markdown(
        f"""
        <div class="card">
            <div class="recipe-title">{_esc(name_en)}</div>
            <div class="recipe-title khmer recipe-title-kh">{_esc(name_kh)}</div>
            {safety_html}
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 1rem;">
                <div class="recipe-col">
                    <h4>{ing_label}</h4>
                    <ul>{ing_html}</ul>
                </div>
                <div class="recipe-col">
                    <h4>{steps_label}</h4>
                    <ol>{steps_html}</ol>
                </div>
            </div>
            <div class="source-footer">Source: {source_type} · {citation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
