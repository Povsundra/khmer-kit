#!/usr/bin/env python3
"""Spot-check hybrid retrieval against the built index."""

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
from src.core.entities import extract_entities  # noqa: E402
from src.core.intent import classify_intent  # noqa: E402
from src.core.language import chunk_body, chunk_title, detect_query_language  # noqa: E402
from src.core.retrieve import hybrid_search  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the recipe index")
    parser.add_argument("query", help="Search query (English or Khmer)")
    parser.add_argument("-k", type=int, default=3, help="Number of results")
    parser.add_argument(
        "--lang",
        choices=("en", "kh"),
        help="Force response language (default: auto-detect from query)",
    )
    parser.add_argument(
        "--engine",
        action="store_true",
        help="Use Phase 7 answer engine (formatted answer + citations)",
    )
    args = parser.parse_args()

    if args.engine:
        try:
            result = answer_query(args.query, lang=args.lang)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
        lang_label = "English" if result.lang == "en" else "Khmer"
        print(f"QUERY: {args.query}")
        print(f"INTENT: {result.intent}")
        print(f"RESPONSE LANGUAGE: {lang_label}\n")
        print(result.text)
        return 0

    try:
        hits = hybrid_search(args.query, top_k=args.k)
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    lang = args.lang or detect_query_language(args.query)
    lang_label = "English" if lang == "en" else "Khmer"
    entities = extract_entities(args.query)
    intent = classify_intent(args.query).intent

    print(f"QUERY: {args.query}")
    print(f"RESPONSE LANGUAGE: {lang_label}")
    if intent in ("how_to_cook", "ingredients", "shopping_list") and not entities.dish_known:
        print(
            "WARNING: Requested dish is not in the 14-recipe corpus. "
            "Retrieval hits below may not match. Use --engine or answer_query.py for a proper answer."
        )
    print()
    for i, hit in enumerate(hits, start=1):
        title = chunk_title(hit, lang)
        body = chunk_body(hit, lang)
        print(f"{i}. [{hit['score']:.3f}] {title} ({hit['chunk_type']})")
        print(f"   slug: {hit['slug']} · category: {hit['category']}")
        for line in body.splitlines():
            print(f"   {line}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
