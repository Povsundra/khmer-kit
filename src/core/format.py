"""Template formatters for structured answers (no LLM)."""

from __future__ import annotations

from typing import Any

from src.core.entities import Entities, dish_by_slug
from src.core.language import QueryLanguage, chunk_body
from src.core.retrieve import get_chunks_for_slug, get_parent_for_category


def _cite(hit: dict[str, Any], lang: QueryLanguage = "en") -> str:
    st = hit.get("source_type", "published_textbook").replace("_", " ")
    if lang == "kh":
        return f"ប្រភព: {st}"
    return f"Source: {st}"


def menu_dish_label(dish: dict[str, Any], lang: QueryLanguage) -> str:
    """Khmer + English when lang is kh; English only otherwise."""
    slug = dish.get("slug")
    row = dish_by_slug(slug) if slug else None
    en = (row or dish).get("dish_name_en") or dish.get("slug") or ""
    en_short = en.split("(")[0].strip()
    kh = ((row or dish).get("dish_name_kh") or "").strip()
    if lang == "kh" and kh:
        return f"{kh} ({en_short})"
    return en


def format_category_browse(hit: dict[str, Any], lang: QueryLanguage) -> str:
    title = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
    summary = hit["text_kh"] if lang == "kh" else hit["text_en"]
    dishes = hit.get("dishes") or []
    lines = [title, "", summary, ""]
    if lang == "kh":
        lines.append("ម្ហូបក្នុងប្រភេទនេះ៖")
    else:
        lines.append("Dishes in this category:")
    for i, d in enumerate(dishes, start=1):
        lines.append(f"{i}. {menu_dish_label(d, lang)}")
    lines.append("")
    lines.append(_cite(hit, lang))
    return "\n".join(lines)


def format_ingredients(hit: dict[str, Any], lang: QueryLanguage) -> str:
    name = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
    body = chunk_body(hit, lang)
    if lang == "kh":
        header = f"គ្រឿងផ្សំសម្រាប់ {name}៖"
    else:
        header = f"Ingredients for {name}:"
    return f"{header}\n\n{body}\n\n{_cite(hit, lang)}"


def format_shopping_list(hit: dict[str, Any], lang: QueryLanguage) -> str:
    name = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
    body = chunk_body(hit, lang)
    if lang == "kh":
        header = f"មុនទៅផ្សារ ទិញគ្រឿងផ្សំសម្រាប់ {name}៖"
    else:
        header = f"Before you go to the market for {name}, buy:"
    return f"{header}\n\n{body}\n\n{_cite(hit, lang)}"


def format_how_to_cook(slug: str, lang: QueryLanguage) -> str | None:
    steps = get_chunks_for_slug(slug, chunk_type="step")
    if not steps:
        return None
    name = steps[0]["dish_name_kh"] if lang == "kh" else steps[0]["dish_name_en"]
    if lang == "kh":
        lines = [f"របៀបធ្វើ {name}៖", ""]
    else:
        lines = [f"How to cook {name}:", ""]
    for step in steps:
        n = step.get("step")
        body = chunk_body(step, lang)
        if lang == "kh":
            lines.append(f"{n}. {body}")
        else:
            lines.append(f"Step {n}: {body}")
    lines.append("")
    lines.append(_cite(steps[0], lang))
    return "\n".join(lines)


def format_substitution(
    hits: list[dict[str, Any]],
    entities: Entities,
    lang: QueryLanguage,
) -> str:
    ing = entities.ingredient or "that ingredient"
    name = entities.dish_name_en or entities.slug or "this dish"
    if lang == "kh":
        lines = [
            f"សៀវភៅធ្វើម្ហូបនេះមិនបានបញ្ជាក់អ្វីជំនួសសម្រាប់ {ing} សម្រាប់ {name} ទេ។",
            "",
        ]
    else:
        lines = [
            f"This cookbook does not specify a substitute for {ing} in {name}.",
            "",
        ]

    mentions: list[str] = []
    for hit in hits:
        body = chunk_body(hit, lang)
        if ing.lower() in body.lower() or ing.lower() in hit.get("embed_text", "").lower():
            step_n = hit.get("step")
            label = f"step {step_n}" if step_n else hit.get("chunk_type", "recipe")
            mentions.append(f"- ({label}) {body}")

    if mentions:
        if lang == "kh":
            lines.append(f"គ្រឿងនេះបង្ហាញក្នុងរូបមន្ត៖")
        else:
            lines.append(f"The recipe uses {ing} here:")
        lines.extend(mentions[:3])
    else:
        if lang == "kh":
            lines.append("រកមិនឃើញគ្រឿងនេះក្នុងរូបមន្តដែលបានទាញយកទេ។")
        else:
            lines.append("That ingredient was not found in the retrieved recipe text.")

    if hits:
        lines.append("")
        lines.append(_cite(hits[0], lang))
    return "\n".join(lines)


def format_recommend_template(parent: dict[str, Any], lang: QueryLanguage) -> str:
    dishes = parent.get("dishes") or []
    title = parent["dish_name_kh"] if lang == "kh" else parent["dish_name_en"]
    if lang == "kh":
        lines = [f"ម្ហូប{title} ដែលមានក្នុងសៀវភៅនេះ៖", ""]
    else:
        lines = [f"{title} in this cookbook:", ""]
    for i, d in enumerate(dishes, start=1):
        lines.append(f"{i}. {menu_dish_label(d, lang)}")
    if dishes:
        pick = menu_dish_label(dishes[0], lang)
        if lang == "kh":
            lines.extend(["", f"សាកល្បង {pick} — ម្ហូបដំបូងក្នុងបញ្ជី។"])
        else:
            lines.extend(["", f"You could try **{pick}** — the first dish in this category."])
    lines.append("")
    lines.append(_cite(parent, lang))
    return "\n".join(lines)


def format_technique_fallback(hits: list[dict[str, Any]], lang: QueryLanguage) -> str:
    if not hits:
        return ""
    if lang == "kh":
        lines = ["ព័ត៌មានពាក់ព័ន្ធពីសៀវភៅធ្វើម្ហូប៖", ""]
    else:
        lines = ["Related steps from this cookbook:", ""]
    for hit in hits[:3]:
        name = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
        step_n = hit.get("step")
        body = chunk_body(hit, lang)
        label = f"{name} (step {step_n})" if step_n else name
        lines.append(f"- {label}: {body}")
    lines.append("")
    lines.append(_cite(hits[0], lang))
    return "\n".join(lines)


def format_refusal(lang: QueryLanguage) -> str:
    if lang == "kh":
        return (
            "សំណួរនេះនៅក្រៅពី ១៤ រូបមន្តក្នុងបណ្ណាល័យនេះ។ "
            "ខ្ញុំអាចជួយអំពីគ្រឿងផ្សំ របៀបធ្វើ ឬណែនាំម្ហូប "
            "ក្នុងប្រភេទ samlor, cha, dessert, other។"
        )
    return (
        "This question is outside the 14 recipes in this collection. "
        "I can help with ingredients, cooking steps, or dish recommendations "
        "from samlor, cha, dessert, and other categories."
    )


def format_out_of_scope(lang: QueryLanguage) -> str:
    if lang == "kh":
        return "សំណួរអំពីតម្លៃ ភោជនីយដ្ឋាន ឬអាហារូបត្ថម្ភ នៅក្រៅពីវិសាលភាពរបស់ប្រព័ន្ធនេះ។"
    return (
        "Questions about prices, restaurants, or nutrition are outside this system's scope. "
        "Ask about cooking techniques or recipes from the 14-dish corpus."
    )


def _unknown_dish_name(requested_name: str | None, lang: QueryLanguage) -> str:
    name = (requested_name or "").strip()
    if not name:
        return "ម្ហូបនេះ" if lang == "kh" else "this dish"
    return name.title() if lang == "en" else name


def _unknown_dish_opener(name: str, lang: QueryLanguage) -> str:
    if lang == "kh":
        return f'មិនមាន "{name}" ក្នុងម៉ឺនុយរបស់យើងនៅឡើយទេ។'
    return f'We don\'t have "{name}" in our menu yet.'


def _unknown_dish_recommend(lang: QueryLanguage) -> str:
    if lang == "kh":
        return (
            "ខ្ញុំអាចណែនាំម្ហូបពី samlor, cha, dessert, ឬ other។ "
            'សួរ "ណែនាំម្ហូប cha" ឬ "របៀបធ្វើ cha mi sour"។'
        )
    return (
        "I can help with dishes from samlor, cha, dessert, or other. "
        'Ask "recommend a cha dish" or "how to cook cha mi sour".'
    )


def format_unknown_dish(lang: QueryLanguage, requested_name: str | None = None) -> str:
    name = _unknown_dish_name(requested_name, lang)
    return f"{_unknown_dish_opener(name, lang)}\n\n{_unknown_dish_recommend(lang)}"


def format_unknown_dish_with_alternatives(
    requested_name: str | None,
    category: str | None,
    lang: QueryLanguage,
) -> str:
    from src.core.retrieve import get_parent_for_category

    name = _unknown_dish_name(requested_name, lang)
    lines = [_unknown_dish_opener(name, lang), ""]

    parent = get_parent_for_category(category) if category else None
    if parent and parent.get("dishes"):
        cat_title = parent["dish_name_kh"] if lang == "kh" else parent["dish_name_en"]
        if lang == "kh":
            lines.append(f"ម្ហូប{cat_title} ដែលអ្នកអាចសាកល្បង៖")
        else:
            lines.append(f"{cat_title} you can try from our database:")
        for i, d in enumerate(parent["dishes"], start=1):
            lines.append(f"{i}. {menu_dish_label(d, lang)}")
        if lang == "kh":
            lines.extend(["", 'សួរ "របៀបធ្វើ cha mi sour" ឬ "ណែនាំម្ហូប cha" ដើម្បីទទួលបានរូបមន្តពេញលេញ។'])
        else:
            example = parent["dishes"][0].get("dish_name_en", "").split("(")[0].strip()
            lines.extend([
                "",
                f'Ask "how to cook {example.lower()}" or "recommend a {category} dish" for a full recipe.',
            ])
    else:
        lines.append(_unknown_dish_recommend(lang))

    return "\n".join(lines)
