"""Parse verified Khmer raw .txt files into structured recipe dicts."""

from __future__ import annotations

import re
from pathlib import Path

INGREDIENTS_HEADER = "គ្រឿងផ្សំ"
STEPS_HEADER = "របៀបធ្វើ"
STEP_SPLIT = re.compile(r"\s*។\s*")


def parse_header(lines: list[str]) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            break
        m = re.match(r"#\s*([^:]+):\s*(.*)$", stripped)
        if m:
            meta[m.group(1).strip()] = m.group(2).strip()
    return meta


def body_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    past_header = False
    for line in lines:
        if line.startswith("#"):
            continue
        if not past_header and not line.strip():
            continue
        past_header = True
        out.append(line.rstrip())
    return out


def split_ingredients(text: str) -> list[str]:
    text = text.strip().rstrip("។").strip()
    if not text:
        return []
    return [part.strip() for part in text.split() if part.strip()]


def split_steps(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = [p.strip() for p in STEP_SPLIT.split(text) if p.strip()]
    return parts


def parse_raw_text(text: str, *, slug_hint: str = "") -> dict:
    lines = text.splitlines()
    meta = parse_header(lines)
    content = body_lines(lines)

    dish_name_kh = ""
    ingredients_lines: list[str] = []
    steps_lines: list[str] = []
    section: str | None = None

    for line in content:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == INGREDIENTS_HEADER:
            section = "ingredients"
            continue
        if stripped == STEPS_HEADER:
            section = "steps"
            continue
        if section == "ingredients":
            ingredients_lines.append(stripped)
        elif section == "steps":
            steps_lines.append(stripped)
        elif section is None:
            dish_name_kh = stripped

    ingredients_kh = split_ingredients(" ".join(ingredients_lines))
    steps_kh = split_steps(" ".join(steps_lines))

    slug = (meta.get("slug") or slug_hint).strip()
    if meta.get("khmer_name"):
        dish_name_kh = meta["khmer_name"]

    return {
        "slug": slug,
        "dish_name_kh": dish_name_kh,
        "source_type": meta.get("source_type", "published_textbook"),
        "source_citation": meta.get("source_citation", ""),
        "verified": meta.get("verified", "no").lower() == "yes",
        "notes": meta.get("notes", ""),
        "ingredients_kh": ingredients_kh,
        "steps_kh": steps_kh,
    }


def parse_raw_file(path: Path) -> dict:
    parsed = parse_raw_text(path.read_text(encoding="utf-8"), slug_hint=path.stem)
    parsed["raw_path"] = str(path.as_posix())
    return parsed


def require_verified(parsed: dict) -> None:
    if not parsed.get("verified"):
        raise ValueError(f"Raw file not verified: {parsed.get('raw_path', parsed.get('slug'))}")


def to_recipe_skeleton(parsed: dict, *, category: str) -> dict:
    return {
        "dish_name_kh": parsed["dish_name_kh"],
        "dish_name_en": "",
        "category": category,
        "source_type": parsed["source_type"],
        "source_citation": parsed["source_citation"],
        "ingredients": [{"raw_kh": kh, "standardized_en": ""} for kh in parsed["ingredients_kh"]],
        "steps": [
            {
                "step": i,
                "text_kh": kh,
                "text_en": "",
                "technique_note": "",
                "requires_safety_review": False,
                "contextualized_text_en": "",
            }
            for i, kh in enumerate(parsed["steps_kh"], start=1)
        ],
        "common_mistake": "",
    }
