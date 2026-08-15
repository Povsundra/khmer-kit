"""Load processed corpus and flatten into embeddable chunks."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config import ALIASES_PATH, CATEGORIES, PROCESSED


def load_dish_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _curated_aliases() -> dict[str, list[str]]:
    if not ALIASES_PATH.is_file():
        return {}
    return json.loads(ALIASES_PATH.read_text(encoding="utf-8"))


def aliases_for_slug(slug: str) -> list[str]:
    return [a.strip() for a in _curated_aliases().get(slug, []) if a and str(a).strip()]


def _alias_embed_suffix(slug: str) -> str:
    aliases = aliases_for_slug(slug)
    return (" " + " ".join(aliases)) if aliases else ""


def slug_from_path(path: Path) -> str:
    return path.stem


def build_ingredients_chunk(slug: str, dish: dict[str, Any]) -> dict[str, Any]:
    items = dish["ingredients"]
    en_lines = [ing["standardized_en"] for ing in items]
    kh_lines = [ing["raw_kh"] for ing in items]
    text_en = "Ingredients: " + ", ".join(en_lines)
    text_kh = "គ្រឿងផ្សំ៖ " + " · ".join(kh_lines)
    contextual = (
        f"Full ingredient list for {dish['dish_name_en']}: {', '.join(en_lines)}."
    )
    embed_text = (
        f"{dish['dish_name_kh']} {dish['dish_name_en']}. "
        f"ingredients គ្រឿងផ្សំ {text_kh} {contextual}"
        f"{_alias_embed_suffix(slug)}"
    )
    return {
        "chunk_type": "ingredients",
        "category": dish["category"],
        "slug": slug,
        "dish_name_kh": dish["dish_name_kh"],
        "dish_name_en": dish["dish_name_en"],
        "step": None,
        "text_kh": text_kh,
        "text_en": text_en,
        "embed_text": embed_text,
        "ingredients": items,
        "source_type": dish["source_type"],
        "source_citation": dish["source_citation"],
        "requires_safety_review": False,
    }


def build_step_chunk(slug: str, dish: dict[str, Any], step: dict[str, Any]) -> dict[str, Any]:
    contextual = step["contextualized_text_en"]
    embed_text = (
        f"{dish['dish_name_kh']} {dish['dish_name_en']}. {step['text_kh']} {contextual}"
        f"{_alias_embed_suffix(slug)}"
    )
    return {
        "chunk_type": "step",
        "category": dish["category"],
        "slug": slug,
        "dish_name_kh": dish["dish_name_kh"],
        "dish_name_en": dish["dish_name_en"],
        "step": step["step"],
        "text_kh": step["text_kh"],
        "text_en": step["text_en"],
        "embed_text": embed_text,
        "source_type": dish["source_type"],
        "source_citation": dish["source_citation"],
        "requires_safety_review": step.get("requires_safety_review", False),
    }


def build_parent_chunk(parent: dict[str, Any]) -> dict[str, Any]:
    title = parent["title_en"]
    title_kh = parent.get("title_kh", "")
    summary = parent["summary_en"]
    extra = " ".join(
        alias
        for dish in parent.get("dishes", [])
        for alias in aliases_for_slug(str(dish.get("slug", "")))
    )
    embed_text = f"{title_kh} {title}. {summary}"
    if extra:
        embed_text = f"{embed_text} {extra}"
    return {
        "chunk_type": "parent",
        "category": parent["category"],
        "slug": f"_parent_{parent['category']}",
        "dish_name_kh": title_kh,
        "dish_name_en": title,
        "step": None,
        "text_kh": title_kh,
        "text_en": summary,
        "embed_text": embed_text,
        "source_type": "published_textbook",
        "source_citation": "Category overview (corpus parent document)",
        "requires_safety_review": False,
        "dishes": parent.get("dishes", []),
    }


def collect_chunks(processed_root: Path = PROCESSED) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []

    for category in CATEGORIES:
        cat_dir = processed_root / category
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("*.json")):
            dish = load_dish_json(path)
            slug = slug_from_path(path)
            chunks.append(build_ingredients_chunk(slug, dish))
            for step in dish["steps"]:
                chunks.append(build_step_chunk(slug, dish, step))

    parents_dir = processed_root / "_parents"
    if parents_dir.is_dir():
        for path in sorted(parents_dir.glob("*.json")):
            chunks.append(build_parent_chunk(load_dish_json(path)))

    for i, chunk in enumerate(chunks):
        chunk["id"] = i
    return chunks
