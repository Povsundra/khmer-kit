"""End-to-end: verified raw .txt → bilingual processed JSON."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import CHECKLIST_PATH, ROOT
from src.data_prep.contextualize import apply_contextualization
from src.data_prep.structure import parse_raw_file, require_verified, to_recipe_skeleton
from src.data_prep.translate import apply_translation


def load_checklist() -> list[dict]:
    return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))


def find_dish(slug: str) -> dict:
    for dish in load_checklist():
        if dish["slug"] == slug:
            return dish
    raise ValueError(f"Slug not found in dish_checklist.json: {slug}")


def resolve_raw_path(dish: dict) -> Path:
    """Find verified raw file — supports slug renames (e.g. samlor_chap_chhay)."""
    candidates = [
        ROOT / dish["raw_path"],
        ROOT / "data" / "raw" / dish["category"] / f"{dish['slug']}.txt",
        ROOT / "data" / "raw" / dish["category"] / f"{dish['slug']}.DRAFT.txt",
    ]
    slug_aliases = {
        "samlor_chap_chhay": ["samlor_chap_bampong"],
        "samlor_chap_bampong": ["samlor_chap_chhay"],
    }
    for alias in slug_aliases.get(dish["slug"], []):
        candidates.append(ROOT / "data" / "raw" / dish["category"] / f"{alias}.txt")

    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"No verified raw .txt for slug: {dish['slug']}")


def processed_output_path(dish: dict) -> Path:
    return ROOT / dish["processed_path"]


def raw_to_json(dish: dict, *, slug: str | None = None) -> dict:
    slug = slug or dish["slug"]
    raw_path = resolve_raw_path(dish)
    parsed = parse_raw_file(raw_path)
    parsed["slug"] = slug
    require_verified(parsed)

    recipe = to_recipe_skeleton(parsed, category=dish["category"])
    recipe = apply_translation(recipe, slug=slug)
    recipe = apply_contextualization(recipe)
    return recipe


def write_processed_json(dish: dict, *, slug: str | None = None) -> Path:
    recipe = raw_to_json(dish, slug=slug)
    out = processed_output_path(dish)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
