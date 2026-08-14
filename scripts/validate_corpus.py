#!/usr/bin/env python3
"""Validate all processed dish JSON and category parent JSON against schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import jsonschema
except ImportError:
    print("ERROR: install jsonschema — pip install jsonschema", file=sys.stderr)
    sys.exit(1)

SCHEMA_PATH = ROOT / "data" / "schema" / "recipe.schema.json"
PROCESSED = ROOT / "data" / "processed"
PARENTS = PROCESSED / "_parents"
CATEGORIES = ("samlor", "cha", "other", "dessert")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_recipe(path: Path, schema: dict) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON — {e}"]
    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{path.relative_to(ROOT)}: {e.message}")
    return errors


def main() -> int:
    schema = load_schema()
    errors: list[str] = []
    dish_count = 0

    for cat in CATEGORIES:
        cat_dir = PROCESSED / cat
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("*.json")):
            dish_count += 1
            errors.extend(validate_recipe(path, schema))

    parent_count = 0
    if PARENTS.is_dir():
        for path in sorted(PARENTS.glob("*.json")):
            parent_count += 1
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{path.name}: invalid JSON — {e}")
                continue
            for field in ("category", "title_en", "summary_en", "dishes"):
                if field not in data:
                    errors.append(f"{path.relative_to(ROOT)}: missing field '{field}'")

    if errors:
        print("CORPUS VALIDATION: FAIL")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("CORPUS VALIDATION: PASS")
    print(f"  - dish JSON: {dish_count}")
    print(f"  - parent JSON: {parent_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
