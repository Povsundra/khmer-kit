#!/usr/bin/env python3
"""Phase 3 batch: transcribe all scans that have no verified raw or DRAFT yet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.config import ROOT as PROJECT_ROOT
from src.data_prep.pipeline import load_checklist, needs_transcription, process_dish

load_dotenv(PROJECT_ROOT / ".env")


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch transcribe pending recipe scans")
    parser.add_argument("--force", action="store_true", help="Overwrite existing DRAFT files")
    args = parser.parse_args()

    checklist = load_checklist()
    pending = [d for d in checklist if args.force or needs_transcription(d)]

    if not pending:
        print("No pending scans (all have DRAFT or verified raw).")
        return 0

    print(f"Processing {len(pending)} dish(es)...")
    errors = 0
    for dish in pending:
        try:
            process_dish(dish, force=args.force)
        except Exception as e:
            print(f"ERROR {dish['slug']}: {e}", file=sys.stderr)
            errors += 1

    print(f"\nDone. Errors: {errors}/{len(pending)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
