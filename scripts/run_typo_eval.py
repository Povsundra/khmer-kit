#!/usr/bin/env python3
"""Run typo-tolerant entity resolution eval queries."""

from __future__ import annotations

import json
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
from src.core.intent import classify_intent  # noqa: E402

QUERIES_PATH = ROOT / "eval" / "test_queries_typo.json"


def main() -> int:
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    passed = 0
    for q in queries:
        intent_ok = classify_intent(q["query"]).intent == q["expected_intent"]
        result = answer_query(q["query"])
        text_lower = result.text.lower()
        contains_ok = all(m.lower() in text_lower for m in q.get("must_contain", []))
        excludes = q.get("must_not_contain", [])
        excludes_ok = all(m.lower() not in text_lower for m in excludes)
        ok = intent_ok and contains_ok and excludes_ok
        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        print(f"{status} {q['id']}: intent={result.intent} (expected {q['expected_intent']})")
        if not ok:
            if not intent_ok:
                print("       intent mismatch")
            if not contains_ok:
                missing = [m for m in q.get("must_contain", []) if m.lower() not in text_lower]
                print(f"       missing phrases: {missing}")
            if not excludes_ok:
                found = [m for m in excludes if m.lower() in text_lower]
                print(f"       forbidden phrases present: {found}")
    print(f"\nTYPO EVAL: {passed}/{len(queries)} passed")
    return 0 if passed == len(queries) else 1


if __name__ == "__main__":
    sys.exit(main())
