#!/usr/bin/env python3
"""Score multi-turn dialogue paths from eval/test_queries_dialogue.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.dialogue import DialogueState  # noqa: E402
from src.core.engine import answer_query  # noqa: E402


def main() -> int:
    path = ROOT / "eval" / "test_queries_dialogue.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        state = DialogueState()
        result = None
        for turn in case["turns"]:
            result = answer_query(turn, lang="en", state=state)
            state = result.state
        assert result is not None
        ok = True
        reasons: list[str] = []
        if result.intent != case["expected_intent"]:
            ok = False
            reasons.append(f"intent {result.intent} != {case['expected_intent']}")
        if result.action != case["expected_action"]:
            ok = False
            reasons.append(f"action {result.action} != {case['expected_action']}")
        if case.get("expected_category") and result.state.category != case["expected_category"]:
            ok = False
            reasons.append(f"category {result.state.category}")
        if case.get("must_have_slug") and not result.state.slug:
            ok = False
            reasons.append("missing slug")
        for needle in case.get("must_contain") or []:
            if needle.lower() not in result.text.lower():
                ok = False
                reasons.append(f"missing {needle!r}")
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        extra = f" — {'; '.join(reasons)}" if reasons else ""
        print(f"{case['id']} {status}  {case['turns'][-1]!r}  {result.action}/{result.intent}{extra}")
    print()
    print(f"{passed}/{len(cases)} passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
