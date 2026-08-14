"""Khmer Kitchen Companion — dark chat Streamlit UI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

import streamlit as st

from src.config import CATEGORIES, FAISS_PATH
from src.core.language import QueryLanguage
from src.core.llm import llm_available
from src.interfaces.web.chat_ui import init_session_state, render_chat_history, run_ask
from src.interfaces.web.recipe_card import dishes_for_category, load_dish_json, render_recipe_card
from src.interfaces.web.theme import CATEGORY_ICONS, CATEGORY_LABELS, inject_theme, render_sidebar_brand

st.set_page_config(
    page_title="Khmer Kitchen Companion",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()
init_session_state()


def _apply_streamlit_secrets() -> None:
    """Copy Cloud secrets into env so retrieval/LLM see the key after reboot."""
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if not secrets_path.is_file():
        return
    try:
        for key, value in st.secrets.items():
            if isinstance(value, str) and value and not os.getenv(key):
                os.environ[key] = value
    except Exception:
        pass


@st.cache_resource(show_spinner="Loading cookbook search model (first visit can take a few minutes)…")
def _warmup_search() -> bool:
    from src.config import EMBEDDING_MODEL
    from src.core.embed import get_embedder
    from src.core.retrieve import _get_index_bundle

    _get_index_bundle()
    get_embedder(EMBEDDING_MODEL)
    return True


def _lang_param() -> QueryLanguage | None:
    return st.session_state.ui_lang  # "en" or "kh"


def _short_name(slug: str | None, category: str) -> str:
    if not slug:
        return ""
    for d in dishes_for_category(category):
        if d["slug"] == slug:
            return d["dish_name_en"].split("(")[0].strip().lower()
    return ""


def render_sidebar() -> str:
    with st.sidebar:
        render_sidebar_brand()
        st.markdown('<div class="sidebar-section">Categories</div>', unsafe_allow_html=True)
        category = st.radio(
            "Category",
            options=list(CATEGORIES),
            format_func=lambda c: f"{CATEGORY_ICONS.get(c, '')} {CATEGORY_LABELS.get(c, c.title())}",
            index=list(CATEGORIES).index(st.session_state.selected_category),
            label_visibility="collapsed",
        )
        st.session_state.selected_category = category

        st.markdown('<div class="sidebar-section">Dishes</div>', unsafe_allow_html=True)
        dishes = dishes_for_category(category)
        labels = {d["slug"]: d["dish_name_en"].split("(")[0].strip() for d in dishes}
        opts = [None] + [d["slug"] for d in dishes]
        idx = opts.index(st.session_state.selected_slug) if st.session_state.selected_slug in opts else 0
        picked = st.selectbox(
            "Dish",
            options=opts,
            format_func=lambda s: "— Select a dish —" if s is None else labels[s],
            index=idx,
            label_visibility="collapsed",
        )
        st.session_state.selected_slug = picked

        connected = llm_available()
        status_class = "llm-status connected" if connected else "llm-status"
        status_text = "LLM connected" if connected else "Template answers only"
        dot = "●" if connected else "○"
        st.markdown(
            f'<div class="{status_class}">{dot} {status_text}</div>',
            unsafe_allow_html=True,
        )
    return category


def render_top_bar(category: str) -> str:
    dishes = dishes_for_category(category)
    cat_label = CATEGORY_LABELS.get(category, category.title())
    col_title, col_tabs, col_lang = st.columns([2, 2, 1])
    with col_title:
        st.markdown(f"### {cat_label}")
        st.caption(f"{len(dishes)} traditional recipes")
    with col_tabs:
        tab = st.radio(
            "View",
            options=["Chat", "Browse", "Recipe"],
            horizontal=True,
            label_visibility="collapsed",
            index=["Chat", "Browse", "Recipe"].index(st.session_state.active_tab),
        )
        st.session_state.active_tab = tab
    with col_lang:
        lang_choice = st.radio(
            "Lang",
            options=["EN", "KH"],
            horizontal=True,
            label_visibility="collapsed",
            index=0 if st.session_state.ui_lang == "en" else 1,
        )
        st.session_state.ui_lang = "en" if lang_choice == "EN" else "kh"
    return tab


def render_browse_tab(category: str, lang: QueryLanguage) -> None:
    dishes = dishes_for_category(category)
    cols = st.columns(2)
    for i, dish in enumerate(dishes):
        name = dish["dish_name_kh"] if lang == "kh" else dish["dish_name_en"].split("(")[0].strip()
        with cols[i % 2]:
            if st.button(name, key=f"browse_{dish['slug']}", use_container_width=True):
                st.session_state.selected_slug = dish["slug"]
                st.session_state.selected_category = category
                st.session_state.active_tab = "Recipe"
                st.rerun()


def render_recipe_tab(category: str, slug: str | None, lang: QueryLanguage) -> None:
    if not slug:
        st.info("Select a dish from the sidebar or Browse tab.")
        return
    data = load_dish_json(category, slug)
    if data:
        render_recipe_card(data, lang)
    else:
        st.warning("Recipe not found.")


def render_suggestion_chips(category: str, slug: str | None) -> None:
    short = _short_name(slug, category)
    if short:
        prompts = [
            f"ingredients of {short}",
            f"how to cook {short}",
            f"recommend a {category} dish",
        ]
    else:
        prompts = [
            f"what dishes are in the {category} category?",
            f"recommend a {category} dish today",
        ]
    cols = st.columns(len(prompts))
    for i, p in enumerate(prompts):
        if cols[i].button(p, key=f"suggest_{i}", use_container_width=True):
            run_ask(p, _lang_param())
            st.rerun()


def main() -> None:
    _apply_streamlit_secrets()
    if not FAISS_PATH.is_file():
        st.error("Recipe index not found. Run: `python scripts/build_index.py`")
        st.stop()

    _warmup_search()

    category = render_sidebar()
    tab = render_top_bar(category)
    lang: QueryLanguage = st.session_state.ui_lang
    slug = st.session_state.selected_slug

    if tab == "Chat":
        render_chat_history(lang)
        render_suggestion_chips(category, slug)
    elif tab == "Browse":
        render_browse_tab(category, lang)
    elif tab == "Recipe":
        render_recipe_tab(category, slug, lang)

    query = st.chat_input("Ask about a recipe or technique…")
    if query:
        st.session_state.active_tab = "Chat"
        run_ask(query, _lang_param())
        st.rerun()


if __name__ == "__main__":
    main()
