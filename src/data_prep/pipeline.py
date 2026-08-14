"""Run transcription for one checklist dish."""

from __future__ import annotations

import json
from pathlib import Path

from src.config import CHECKLIST_PATH, ROOT
from src.data_prep.transcribe import build_raw_draft, draft_output_path, transcribe_image


def load_checklist() -> list[dict]:
    return json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))


def find_dish(slug: str) -> dict:
    for dish in load_checklist():
        if dish["slug"] == slug:
            return dish
    raise ValueError(f"Slug not found in dish_checklist.json: {slug}")


def is_verified(path: Path) -> bool:
    if not path.is_file():
        return False
    return "# verified: yes" in path.read_text(encoding="utf-8")


def needs_transcription(dish: dict) -> bool:
    raw = ROOT / dish["raw_path"]
    draft = draft_output_path(raw)
    if is_verified(raw) or is_verified(draft):
        return False
    return (ROOT / dish["scan_path"]).is_file()


def process_dish(dish: dict, *, force: bool = False) -> Path:
    scan = ROOT / dish["scan_path"]
    raw = ROOT / dish["raw_path"]
    out = draft_output_path(raw)

    if not force:
        if is_verified(raw):
            print(f"SKIP {dish['slug']} — raw already verified")
            return raw
        if out.exists():
            print(f"SKIP {dish['slug']} — draft exists: {out.relative_to(ROOT)}")
            return out

    print(f"TRANSCRIBE {dish['slug']} ← {scan.name}")
    khmer = transcribe_image(scan, dish_hint=dish.get("dish_name_kh", ""))
    body = build_raw_draft(
        slug=dish["slug"],
        source_type=dish.get("source_type") or "published_textbook",
        source_citation=dish.get("source_citation") or "Khmer cookbook (paraphrased)",
        khmer_body=khmer,
        scan_path=dish["scan_path"],
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"WROTE {out.relative_to(ROOT)}")
    return out
