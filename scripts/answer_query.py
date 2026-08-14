#!/usr/bin/env python3
"""Phase 7: ask the Khmer Kitchen Companion a cooking question."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.core.engine import answer_query  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the Khmer Kitchen Companion")
    parser.add_argument("query", help="Your cooking question (English or Khmer)")
    parser.add_argument(
        "--lang",
        choices=("en", "kh"),
        help="Force response language (default: auto-detect from query)",
    )
    parser.add_argument(
        "--focus-slug",
        help="Prior dish slug for follow-ups like 'ingredients of this soup'",
    )
    args = parser.parse_args()

    try:
        result = answer_query(args.query, lang=args.lang, focus_slug=args.focus_slug)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Run: python scripts/build_index.py", file=sys.stderr)
        return 1

    lang_label = "English" if result.lang == "en" else "Khmer"
    print(f"QUERY: {args.query}")
    print(f"INTENT: {result.intent}")
    print(f"RESPONSE LANGUAGE: {lang_label}")
    print(f"CONFIDENCE: {result.retrieval_score:.3f}")
    print()
    print(result.text)
    if result.citations:
        print()
        print("--- Citations ---")
        for cite in result.citations:
            print(f"  · {cite}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
