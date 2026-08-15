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

st.set_page_config(
    page_title="Khmer Kitchen Companion",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config import CATEGORIES, FAISS_PATH, secrets_toml_exists
from src.core.language import QueryLanguage
from src.core.llm import llm_available
from src.interfaces.web.chat_ui import (
    init_session_state,
    render_chat_history,
    reset_conversation,
    run_ask,
)
from src.interfaces.web.recipe_card import dishes_for_category, load_dish_json, render_recipe_card
from src.interfaces.web.i18n import TABS, category_label, t, tab_label, ui_lang
from src.interfaces.web.theme import CATEGORY_ICONS, inject_theme, render_sidebar_brand

inject_theme()
init_session_state()


def _apply_streamlit_secrets() -> None:
    """Copy Streamlit secrets into os.environ when a secrets.toml exists.

    Do not touch st.secrets otherwise: Streamlit prints 'No secrets files found'
    in the UI even inside try/except. Local runs use `.env` via dotenv.
    """
    if not secrets_toml_exists():
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


def _dish_names(slug: str | None, category: str) -> tuple[str, str]:
    if not slug:
        return "", ""
    for d in dishes_for_category(category):
        if d["slug"] == slug:
            en = d["dish_name_en"].split("(")[0].strip()
            kh = (d.get("dish_name_kh") or en).strip()
            return en.lower(), kh
    return "", ""


def render_sidebar() -> str:
    lang = ui_lang()
    with st.sidebar:
        render_sidebar_brand()
        st.radio(
            "Lang",
            options=["en", "kh"],
            format_func=lambda x: "EN" if x == "en" else "KH",
            horizontal=True,
            label_visibility="collapsed",
            key="ui_lang",
        )
        lang = ui_lang()
        tab = st.radio(
            "View",
            options=list(TABS),
            format_func=lambda name: tab_label(name, lang),
            horizontal=True,
            label_visibility="collapsed",
            index=list(TABS).index(st.session_state.active_tab)
            if st.session_state.active_tab in TABS
            else 0,
        )
        st.session_state.active_tab = tab
        st.markdown('<div class="sidebar-nav-end"></div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="sidebar-section khmer">{t("categories", lang)}</div>',
            unsafe_allow_html=True,
        )
        category = st.radio(
            "Category",
            options=list(CATEGORIES),
            format_func=lambda c: f"{CATEGORY_ICONS.get(c, '')} {category_label(c, lang)}",
            index=list(CATEGORIES).index(st.session_state.selected_category),
            label_visibility="collapsed",
        )
        st.session_state.selected_category = category

        st.markdown(
            f'<div class="sidebar-section khmer">{t("dishes", lang)}</div>',
            unsafe_allow_html=True,
        )
        dishes = dishes_for_category(category)
        if lang == "kh":
            labels = {d["slug"]: d["dish_name_kh"] or d["dish_name_en"] for d in dishes}
        else:
            labels = {d["slug"]: d["dish_name_en"].split("(")[0].strip() for d in dishes}
        opts = [None] + [d["slug"] for d in dishes]
        idx = opts.index(st.session_state.selected_slug) if st.session_state.selected_slug in opts else 0
        picked = st.selectbox(
            "Dish",
            options=opts,
            format_func=lambda s: t("select_dish", lang) if s is None else labels[s],
            index=idx,
            label_visibility="collapsed",
        )
        st.session_state.selected_slug = picked

        if st.button(t("new_chat", lang), use_container_width=True):
            reset_conversation()
            st.rerun()

        connected = llm_available()
        status_class = "llm-status connected" if connected else "llm-status"
        status_text = t("llm_on", lang) if connected else t("llm_off", lang)
        dot = "●" if connected else "○"
        st.markdown(
            f'<div class="{status_class} khmer">{dot} {status_text}</div>',
            unsafe_allow_html=True,
        )
        if not connected:
            st.caption(
                "Add OPENROUTER_API_KEY in `.env` (local) or Streamlit Cloud **Settings → Secrets**, then reboot."
            )
    return category


def render_top_bar(category: str) -> None:
    lang = ui_lang()
    dishes = dishes_for_category(category)
    cat_label = category_label(category, lang)
    st.markdown(f'<h3 class="khmer">{cat_label}</h3>', unsafe_allow_html=True)
    st.caption(t("recipes_count", lang, n=len(dishes)))


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
        st.info(t("pick_dish", lang))
        return
    data = load_dish_json(category, slug)
    if data:
        render_recipe_card(data, lang)
    else:
        st.warning(t("recipe_missing", lang))


def render_suggestion_chips(category: str, slug: str | None) -> None:
    lang = ui_lang()
    cat_shown = category_label(category, lang)
    en_name, kh_name = _dish_names(slug, category)
    shown_name = kh_name if lang == "kh" else en_name
    if en_name:
        pairs = [
            (f"ingredients of {en_name}", t("chip_ingredients", lang, name=shown_name)),
            (f"how to cook {en_name}", t("chip_how_to", lang, name=shown_name)),
            (f"recommend a {category} dish", t("chip_recommend", lang, cat=cat_shown)),
        ]
    else:
        pairs = [
            (
                f"what dishes are in the {category} category?",
                t("chip_list_cat", lang, cat=cat_shown),
            ),
            (
                f"recommend a {category} dish today",
                t("chip_recommend_cat", lang, cat=cat_shown),
            ),
        ]
    cols = st.columns(len(pairs))
    for i, (query, label) in enumerate(pairs):
        if cols[i].button(label, key=f"suggest_{i}", use_container_width=True):
            run_ask(query, _lang_param())
            st.rerun()


def main() -> None:
    _apply_streamlit_secrets()
    if not FAISS_PATH.is_file():
        st.error(t("index_missing"))
        st.stop()

    _warmup_search()

    category = render_sidebar()
    render_top_bar(category)
    tab = st.session_state.active_tab
    lang: QueryLanguage = st.session_state.ui_lang
    slug = st.session_state.selected_slug

    if tab == "Chat":
        render_chat_history(lang)
        render_suggestion_chips(category, slug)
    elif tab == "Browse":
        render_browse_tab(category, lang)
    elif tab == "Recipe":
        render_recipe_tab(category, slug, lang)

    query = st.chat_input(t("chat_placeholder", lang))
    if query:
        st.session_state.active_tab = "Chat"
        run_ask(query, _lang_param())
        st.rerun()


if __name__ == "__main__":
    main()
