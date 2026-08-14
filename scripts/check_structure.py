#!/usr/bin/env python3
"""Phase 1 gate: verify folder structure and dish checklist."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("samlor", "cha", "other", "dessert")
LAYERS = ("source_scans", "raw", "processed")

REQUIRED_DIRS = [
    "data/index",
    "data/schema",
    "data/processed/_parents",
    "docs",
    "scripts",
    "logs",
    "eval/results",
    "src/core",
    "src/safety",
    "src/data_prep",
    "src/interfaces/web",
    "tests",
]

REQUIRED_FILES = [
    "docs/dish_checklist.json",
    "docs/collection_log.md",
    "data/schema/recipe.schema.json",
    "data/raw/_TEMPLATE.txt",
]


def main() -> int:
    errors: list[str] = []

    for d in REQUIRED_DIRS:
        if not (ROOT / d).is_dir():
            errors.append(f"Missing directory: {d}")

    for layer in LAYERS:
        for cat in CATEGORIES:
            p = ROOT / "data" / layer / cat
            if not p.is_dir():
                errors.append(f"Missing directory: data/{layer}/{cat}")

    for f in REQUIRED_FILES:
        if not (ROOT / f).is_file():
            errors.append(f"Missing file: {f}")

    checklist_path = ROOT / "docs" / "dish_checklist.json"
    if checklist_path.is_file():
        try:
            dishes = json.loads(checklist_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in dish_checklist.json: {e}")
            dishes = []
        if not (10 <= len(dishes) <= 15):
            errors.append(
                f"dish_checklist.json must have 10–15 entries, found {len(dishes)}"
            )
        for i, dish in enumerate(dishes, start=1):
            for field in ("slug", "dish_name_kh", "dish_name_en", "category", "scan_path"):
                if not dish.get(field):
                    errors.append(f"Dish #{i} missing field: {field}")
            if dish.get("category") and dish["category"] not in CATEGORIES:
                errors.append(f"Dish #{i} invalid category: {dish.get('category')}")

    if errors:
        print("STRUCTURE CHECK: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("STRUCTURE CHECK: PASS")
    print(f"  - {len(REQUIRED_DIRS)} core directories")
    print(f"  - {len(LAYERS) * len(CATEGORIES)} category data directories")
    print(f"  - dish_checklist.json: {len(json.loads((ROOT / 'docs/dish_checklist.json').read_text(encoding='utf-8')))} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
