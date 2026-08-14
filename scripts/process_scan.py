#!/usr/bin/env python3
"""Phase 3: transcribe one recipe scan → data/raw/{category}/{slug}.DRAFT.txt"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.config import ROOT as PROJECT_ROOT
from src.data_prep.pipeline import find_dish, process_dish

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe one recipe scan to raw DRAFT")
    parser.add_argument("--slug", required=True, help="Dish slug from dish_checklist.json")
    parser.add_argument("--force", action="store_true", help="Overwrite existing DRAFT")
    args = parser.parse_args()

    try:
        dish = find_dish(args.slug)
        process_dish(dish, force=args.force)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
