"""UI chrome strings for EN / KH. Internal tab keys stay English."""

from __future__ import annotations

from src.core.language import QueryLanguage

TABS = ("Chat", "Browse", "Recipe")

CATEGORY_LABELS_EN = {
    "samlor": "Samlor",
    "cha": "Cha",
    "dessert": "Dessert",
    "other": "Other",
}

CATEGORY_LABELS_KH = {
    "samlor": "សម្ល",
    "cha": "ឆា",
    "dessert": "បង្អែម",
    "other": "ផ្សេងទៀត",
}

_TAB_LABELS = {
    "en": {"Chat": "Chat", "Browse": "Browse", "Recipe": "Recipe"},
    "kh": {"Chat": "សន្ទនា", "Browse": "រកមើល", "Recipe": "រូបមន្ត"},
}

_STRINGS = {
    "en": {
        "brand_sub": "Khmer Kitchen Companion",
        "categories": "Categories",
        "dishes": "Dishes",
        "select_dish": "— Select a dish —",
        "new_chat": "New chat",
        "llm_on": "LLM connected",
        "llm_off": "Template answers only",
        "recipes_count": "{n} traditional recipes",
        "welcome_title": "Ask about a recipe or technique",
        "welcome_body": (
            "Try “recommend me Khmer food?” — I will ask what type you want "
            "(samlor, cha, dessert, other), then look it up in the cookbook."
        ),
        "chat_placeholder": "Ask about a recipe or technique…",
        "pick_dish": "Select a dish from the sidebar or Browse tab.",
        "recipe_missing": "Recipe not found.",
        "searching": "Searching the cookbook…",
        "retrieved": "Retrieved recipe",
        "ing_steps": "{n_ing} ingredients · {n_steps} steps",
        "source": "Source",
        "chip_list_cat": "what dishes are in the {cat} category?",
        "chip_recommend_cat": "recommend a {cat} dish today",
        "chip_ingredients": "ingredients of {name}",
        "chip_how_to": "how to cook {name}",
        "chip_recommend": "recommend a {cat} dish",
        "index_missing": "Recipe index not found. Run: `python scripts/build_index.py`",
    },
    "kh": {
        "brand_sub": "មគ្គុទ្ទេសក៍ផ្ទះបាយខ្មែរ",
        "categories": "ប្រភេទ",
        "dishes": "ម្ហូប",
        "select_dish": "— ជ្រើសរើសម្ហូប —",
        "new_chat": "សន្ទនាថ្មី",
        "llm_on": "LLM បានភ្ជាប់",
        "llm_off": "ចម្លើយពីគំរូតែប៉ុណ្ណោះ",
        "recipes_count": "រូបមន្តប្រពៃណី {n}",
        "welcome_title": "សួរអំពីរូបមន្ត ឬវិធីធ្វើ",
        "welcome_body": (
            "សាកសួរ «ណែនាំម្ហូបខ្មែរ» — ខ្ញុំនឹងសួរថាត្រូវការប្រភេទណា "
            "(សម្ល, ឆា, បង្អែម, ផ្សេងទៀត) រួចរកក្នុងសៀវភៅធ្វើម្ហូប។"
        ),
        "chat_placeholder": "សួរអំពីរូបមន្ត ឬវិធីធ្វើ…",
        "pick_dish": "សូមជ្រើសម្ហូបពីរបារចំហៀង ឬផ្ទាំងរកមើល។",
        "recipe_missing": "រកមិនឃើញរូបមន្ត។",
        "searching": "កំពុងរកក្នុងសៀវភៅធ្វើម្ហូប…",
        "retrieved": "រូបមន្តដែលបានទាញយក",
        "ing_steps": "គ្រឿងផ្សំ {n_ing} · ជំហាន {n_steps}",
        "source": "ប្រភព",
        "chip_list_cat": "ម្ហូបអ្វីខ្លះក្នុងប្រភេទ {cat}?",
        "chip_recommend_cat": "ណែនាំម្ហូប{cat} ថ្ងៃនេះ",
        "chip_ingredients": "គ្រឿងផ្សំ{name}",
        "chip_how_to": "របៀបធ្វើ {name}",
        "chip_recommend": "ណែនាំម្ហូប{cat}",
        "index_missing": "រកមិនឃើញលិបិក្រមរូបមន្ត។ រត់: `python scripts/build_index.py`",
    },
}


def ui_lang() -> QueryLanguage:
    import streamlit as st

    lang = st.session_state.get("ui_lang", "en")
    return "kh" if lang == "kh" else "en"


def t(key: str, lang: QueryLanguage | None = None, **kwargs: object) -> str:
    code = lang or ui_lang()
    table = _STRINGS.get(code, _STRINGS["en"])
    text = table.get(key) or _STRINGS["en"][key]
    return text.format(**kwargs) if kwargs else text


def tab_label(tab: str, lang: QueryLanguage | None = None) -> str:
    code = lang or ui_lang()
    return _TAB_LABELS.get(code, _TAB_LABELS["en"]).get(tab, tab)


def category_label(category: str, lang: QueryLanguage | None = None) -> str:
    code = lang or ui_lang()
    labels = CATEGORY_LABELS_KH if code == "kh" else CATEGORY_LABELS_EN
    return labels.get(category, category)
