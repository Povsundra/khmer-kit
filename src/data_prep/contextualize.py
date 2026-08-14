"""Build contextualized_text_en for each recipe step (Contextual Retrieval)."""

from __future__ import annotations

SAFETY_KEYWORDS = (
    "ថ្លើម",
    "liver",
    "prahok",
    "ប្រហុក",
    "ពោះវៀន",
    "intestine",
)


def step_needs_safety_review(text_kh: str, text_en: str) -> bool:
    combined = f"{text_kh} {text_en}".lower()
    return any(kw.lower() in combined for kw in SAFETY_KEYWORDS)


def contextualize_step(
    *,
    dish_name_en: str,
    category: str,
    step_num: int,
    text_en: str,
    technique_note: str = "",
) -> str:
    base = f"For the Khmer {category} dish {dish_name_en}, step {step_num}: {text_en.rstrip('.')}."
    if technique_note.strip():
        base += f" Technique note: {technique_note.rstrip('.')}."
    return base


def apply_contextualization(recipe: dict) -> dict:
    dish_name_en = recipe["dish_name_en"]
    category = recipe["category"]
    for step in recipe["steps"]:
        note = step.get("technique_note") or ""
        step["requires_safety_review"] = step_needs_safety_review(
            step["text_kh"], step["text_en"]
        )
        step["contextualized_text_en"] = contextualize_step(
            dish_name_en=dish_name_en,
            category=category,
            step_num=step["step"],
            text_en=step["text_en"],
            technique_note=note,
        )
    return recipe
