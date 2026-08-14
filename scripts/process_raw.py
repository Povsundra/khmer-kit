#!/usr/bin/env python3
"""Phase 4: convert verified raw Khmer .txt to bilingual processed JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_prep.process_recipe import find_dish, write_processed_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Process verified raw recipe to JSON")
    parser.add_argument("--slug", required=True, help="Dish slug from dish_checklist.json")
    args = parser.parse_args()

    try:
        dish = find_dish(args.slug)
        out = write_processed_json(dish, slug=args.slug)
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(f"WROTE {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
