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

from src.core.dialogue import DialogueState  # noqa: E402
from src.core.engine import answer_query  # noqa: E402


def _print_result(query: str, result) -> None:
    lang_label = "English" if result.lang == "en" else "Khmer"
    print(f"QUERY: {query}")
    print(f"INTENT: {result.intent}")
    print(f"ACTION: {result.action}")
    print(f"RESPONSE LANGUAGE: {lang_label}")
    print(f"CONFIDENCE: {result.retrieval_score:.3f}")
    print()
    print(result.text)
    if result.citations:
        print()
        print("--- Citations ---")
        for cite in result.citations:
            print(f"  · {cite}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask the Khmer Kitchen Companion")
    parser.add_argument("query", nargs="?", help="Your cooking question (English or Khmer)")
    parser.add_argument(
        "--lang",
        choices=("en", "kh"),
        help="Force response language (default: auto-detect from query)",
    )
    parser.add_argument(
        "--focus-slug",
        help="Prior dish slug for follow-ups like 'ingredients of this soup'",
    )
    parser.add_argument(
        "--prior-query",
        help="Previous user question for constrained follow-up rewrite",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Keep dialogue state and ask follow-up questions",
    )
    args = parser.parse_args()

    if args.interactive or not args.query:
        print("Khmer Kitchen Companion — type a question (empty / quit to exit).")
        state = DialogueState()
        prior = args.prior_query
        while True:
            try:
                line = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not line or line.lower() in {"quit", "exit", "q"}:
                return 0
            try:
                result = answer_query(
                    line,
                    lang=args.lang,
                    focus_slug=args.focus_slug or state.slug,
                    prior_query=prior,
                    state=state,
                )
            except FileNotFoundError as e:
                print(f"ERROR: {e}", file=sys.stderr)
                print("Run: python scripts/build_index.py", file=sys.stderr)
                return 1
            state = result.state
            prior = line
            _print_result(line, result)
            print()
        return 0

    try:
        result = answer_query(
            args.query,
            lang=args.lang,
            focus_slug=args.focus_slug,
            prior_query=args.prior_query,
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print("Run: python scripts/build_index.py", file=sys.stderr)
        return 1

    _print_result(args.query, result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
