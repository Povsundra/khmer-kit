#!/usr/bin/env python3
"""Phase 9: golden-query eval — Hit@k, citation, faithfulness."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from src.core.language import chunk_body  # noqa: E402
from src.core.llm import generate, llm_available  # noqa: E402
from src.core.retrieve import search_for_intent  # noqa: E402
from src.core.rewrite import rewrite_query  # noqa: E402

QUERIES_PATH = ROOT / "eval" / "test_queries.json"
RESULTS = ROOT / "eval" / "results"

TARGETS = {
    "hit_at_1": 70.0,
    "hit_at_3": 60.0,
    "faithfulness": 3.5,
    "citation": 80.0,
}

TOKEN_RE = re.compile(r"[\u1780-\u17FF]+|[a-z0-9]+", re.I)
SCORE_RE = re.compile(r'"score"\s*:\s*([1-5](?:\.\d+)?)')

JUDGE_SYSTEM = """You are a faithfulness judge for a Khmer cookbook RAG system.
Score 1-5 whether ANSWER is supported by CONTEXT chunks only.
1 = invents or contradicts the context
3 = mixed / only partly grounded
5 = fully grounded, or a correct refusal that the cookbook does not cover this
Reply with JSON only: {"score": N, "reason": "one sentence"}"""


def _contains_all(text: str, phrases: list[str]) -> bool:
    lower = text.lower()
    return all(p.lower() in lower for p in phrases)


def _citation_ok(text: str, citations: list[str], expected: str | None) -> bool:
    if not expected:
        return True
    blob = f"{' '.join(citations)} {text}".lower().replace("_", " ")
    label = expected.replace("_", " ").lower()
    return label in blob


def _chunk_context(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for c in chunks:
        parts.append(chunk_body(c, "en"))
        parts.append(chunk_body(c, "kh"))
        parts.append(c.get("embed_text", ""))
        for dish in c.get("dishes") or []:
            parts.append(dish.get("dish_name_en", ""))
            parts.append(dish.get("slug", ""))
    return " ".join(parts).lower()


def _heuristic_faithfulness(answer: str, chunks: list[dict[str, Any]], *, is_refusal: bool) -> float:
    if not answer.strip():
        return 1.0
    if is_refusal:
        return 5.0
    if not chunks:
        return 3.0
    ctx = _chunk_context(chunks)
    tokens = [t for t in TOKEN_RE.findall(answer.lower()) if len(t) > 2]
    if not tokens:
        return 3.0
    overlap = sum(1 for t in tokens if t in ctx) / len(tokens)
    return round(1.0 + 4.0 * overlap, 2)


def _llm_faithfulness(answer: str, chunks: list[dict[str, Any]]) -> tuple[float | None, str]:
    if not llm_available():
        return None, "llm_unavailable"
    ctx_parts = []
    for i, hit in enumerate(chunks[:4], start=1):
        body = chunk_body(hit, "en") or hit.get("text_en", "")
        ctx_parts.append(f"[{i}] {hit.get('dish_name_en', '')} ({hit.get('chunk_type', '')})\n{body}")
    context = "\n\n".join(ctx_parts) if ctx_parts else "(no retrieved chunks)"
    try:
        raw = generate(
            [
                {"role": "system", "content": JUDGE_SYSTEM},
                {
                    "role": "user",
                    "content": f"CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\nJSON:",
                },
            ],
            temperature=0.0,
        )
    except Exception as exc:
        return None, f"llm_error: {exc}"
    match = SCORE_RE.search(raw)
    if not match:
        return None, f"parse_fail: {raw[:120]}"
    return float(match.group(1)), raw[:240]


def _slugs(hits: list[dict[str, Any]]) -> list[str]:
    out: list[str] = []
    for hit in hits:
        slug = hit.get("slug", "")
        if slug and slug not in out:
            out.append(slug)
    return out


def evaluate_query(q: dict[str, Any]) -> dict[str, Any]:
    query = q["query"]
    intent_result = classify_intent(query)
    entities = extract_entities(query)
    rewritten = rewrite_query(query, intent_result.intent, entities)
    hits = search_for_intent(rewritten, intent_result.intent, entities, top_k=5)
    slugs = _slugs(hits)

    result = answer_query(query)
    expected_slug = q.get("expected_slug")
    score_retrieval = q.get("score_retrieval", True) and bool(expected_slug)

    hit_at_1 = None
    hit_at_3 = None
    if score_retrieval:
        hit_at_1 = bool(slugs) and slugs[0] == expected_slug
        hit_at_3 = expected_slug in slugs[:3]

    intent_ok = intent_result.intent == q["expected_intent"]
    contains_ok = _contains_all(result.text, q.get("must_contain", []))
    citation_ok = _citation_ok(result.text, result.citations, q.get("expected_source_type"))

    is_refusal = q.get("query_type") in ("out_of_scope", "missing_dish")
    faith_chunks = [] if is_refusal else (result.chunks_used or hits[:3])
    heuristic = _heuristic_faithfulness(result.text, faith_chunks, is_refusal=is_refusal)
    if is_refusal:
        llm_score, llm_note = None, "refusal_skip_judge"
    else:
        llm_score, llm_note = _llm_faithfulness(result.text, faith_chunks)
    faithfulness = llm_score if llm_score is not None else heuristic

    return {
        "id": q["id"],
        "query": query,
        "query_type": q.get("query_type", ""),
        "expected_intent": q["expected_intent"],
        "predicted_intent": intent_result.intent,
        "intent_ok": intent_ok,
        "expected_slug": expected_slug,
        "retrieved_slugs": slugs[:5],
        "score_retrieval": score_retrieval,
        "hit_at_1": hit_at_1,
        "hit_at_3": hit_at_3,
        "citation_ok": citation_ok,
        "contains_ok": contains_ok,
        "faithfulness": faithfulness,
        "faithfulness_heuristic": heuristic,
        "faithfulness_llm": llm_score,
        "faithfulness_note": llm_note,
        "citations": result.citations,
        "answer_preview": result.text[:280].replace("\n", " "),
    }


def _pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 1) if den else 0.0


def _gate(value: float, target: float) -> str:
    return "PASS" if value >= target else "BELOW TARGET"


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    retr = [r for r in rows if r["score_retrieval"]]
    hit1 = sum(1 for r in retr if r["hit_at_1"])
    hit3 = sum(1 for r in retr if r["hit_at_3"])
    cite = sum(1 for r in rows if r["citation_ok"])
    intent = sum(1 for r in rows if r["intent_ok"])
    contain = sum(1 for r in rows if r["contains_ok"])
    faith_vals = [float(r["faithfulness"]) for r in rows]
    faith_avg = round(sum(faith_vals) / len(faith_vals), 2) if faith_vals else 0.0
    llm_used = any(r["faithfulness_llm"] is not None for r in rows)

    by_type: dict[str, dict[str, Any]] = {}
    for r in rows:
        bucket = by_type.setdefault(
            r["query_type"] or "other",
            {"total": 0, "hit_at_1": 0, "hit_at_3": 0, "retr_n": 0, "citation": 0, "faith_sum": 0.0},
        )
        bucket["total"] += 1
        bucket["citation"] += int(r["citation_ok"])
        bucket["faith_sum"] += float(r["faithfulness"])
        if r["score_retrieval"]:
            bucket["retr_n"] += 1
            bucket["hit_at_1"] += int(bool(r["hit_at_1"]))
            bucket["hit_at_3"] += int(bool(r["hit_at_3"]))

    by_type_out = {}
    for k, v in by_type.items():
        by_type_out[k] = {
            **v,
            "hit_at_1_pct": _pct(v["hit_at_1"], v["retr_n"]),
            "hit_at_3_pct": _pct(v["hit_at_3"], v["retr_n"]),
            "citation_pct": _pct(v["citation"], v["total"]),
            "faithfulness_avg": round(v["faith_sum"] / v["total"], 2) if v["total"] else 0.0,
        }

    hit1_pct = _pct(hit1, len(retr))
    hit3_pct = _pct(hit3, len(retr))
    cite_pct = _pct(cite, len(rows))
    return {
        "query_count": len(rows),
        "retrieval_n": len(retr),
        "hit_at_1": hit1,
        "hit_at_3": hit3,
        "hit_at_1_pct": hit1_pct,
        "hit_at_3_pct": hit3_pct,
        "citation": cite,
        "citation_pct": cite_pct,
        "intent": intent,
        "intent_pct": _pct(intent, len(rows)),
        "contains": contain,
        "contains_pct": _pct(contain, len(rows)),
        "faithfulness_avg": faith_avg,
        "faithfulness_llm_used": llm_used,
        "by_query_type": by_type_out,
        "gates": {
            "hit_at_1": _gate(hit1_pct, TARGETS["hit_at_1"]),
            "hit_at_3": _gate(hit3_pct, TARGETS["hit_at_3"]),
            "faithfulness": _gate(faith_avg, TARGETS["faithfulness"]),
            "citation": _gate(cite_pct, TARGETS["citation"]),
        },
    }


def write_markdown(summary: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> None:
    s = summary
    lines = [
        "# Phase 9 Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Golden set: `eval/test_queries.json` · engine path: hybrid `search_for_intent()` + `answer_query()`.",
        "",
        "## Summary vs course targets",
        "",
        "| Metric | Score | Target | Gate |",
        "|--------|-------|--------|------|",
        f"| Retrieval Hit@1 | {s['hit_at_1']}/{s['retrieval_n']} ({s['hit_at_1_pct']}%) | ≥ {TARGETS['hit_at_1']}% | {s['gates']['hit_at_1']} |",
        f"| Retrieval Hit@3 | {s['hit_at_3']}/{s['retrieval_n']} ({s['hit_at_3_pct']}%) | ≥ {TARGETS['hit_at_3']}% | {s['gates']['hit_at_3']} |",
        f"| Faithfulness (1–5) | {s['faithfulness_avg']} | ≥ {TARGETS['faithfulness']} | {s['gates']['faithfulness']} |",
        f"| Citation correctness | {s['citation']}/{s['query_count']} ({s['citation_pct']}%) | ≥ {TARGETS['citation']}% | {s['gates']['citation']} |",
        f"| Intent accuracy | {s['intent']}/{s['query_count']} ({s['intent_pct']}%) | — | — |",
        f"| Answer must-contain | {s['contains']}/{s['query_count']} ({s['contains_pct']}%) | — | — |",
        "",
        f"Faithfulness judge: {'LLM' if s['faithfulness_llm_used'] else 'lexical overlap heuristic (LLM unavailable)'}.",
        "",
        "## By query type",
        "",
        "| Type | n | Hit@1 | Hit@3 | Citation | Faithfulness |",
        "|------|---|-------|-------|----------|--------------|",
    ]
    for qtype, stats in s["by_query_type"].items():
        retr = stats["retr_n"]
        h1 = f"{stats['hit_at_1']}/{retr} ({stats['hit_at_1_pct']}%)" if retr else "—"
        h3 = f"{stats['hit_at_3']}/{retr} ({stats['hit_at_3_pct']}%)" if retr else "—"
        lines.append(
            f"| {qtype} | {stats['total']} | {h1} | {h3} | "
            f"{stats['citation']}/{stats['total']} ({stats['citation_pct']}%) | "
            f"{stats['faithfulness_avg']} |"
        )
    lines.extend(
        [
            "",
            "## Per-query results",
            "",
            "| ID | Type | Intent | Hit@1 | Hit@3 | Cite | Contain | Faith |",
            "|----|------|--------|-------|-------|------|---------|-------|",
        ]
    )
    for r in rows:
        def _yn(val: bool | None) -> str:
            if val is None:
                return "—"
            return "Y" if val else "N"

        lines.append(
            f"| {r['id']} | {r['query_type']} | {_yn(r['intent_ok'])} | "
            f"{_yn(r['hit_at_1'])} | {_yn(r['hit_at_3'])} | {_yn(r['citation_ok'])} | "
            f"{_yn(r['contains_ok'])} | {r['faithfulness']} |"
        )
    lines.extend(["", "## Failures / misses", ""])
    misses = [
        r
        for r in rows
        if (r["score_retrieval"] and not r["hit_at_3"])
        or not r["intent_ok"]
        or not r["contains_ok"]
        or not r["citation_ok"]
        or float(r["faithfulness"]) < TARGETS["faithfulness"]
    ]
    if not misses:
        lines.append("None — all scored queries met intent, contain, citation, Hit@3, and faithfulness floor.")
    else:
        for r in misses:
            flags = []
            if r["score_retrieval"] and not r["hit_at_1"]:
                flags.append("Hit@1 miss")
            if r["score_retrieval"] and not r["hit_at_3"]:
                flags.append("Hit@3 miss")
            if not r["intent_ok"]:
                flags.append(f"intent {r['predicted_intent']}≠{r['expected_intent']}")
            if not r["contains_ok"]:
                flags.append("must-contain")
            if not r["citation_ok"]:
                flags.append("citation")
            if float(r["faithfulness"]) < TARGETS["faithfulness"]:
                flags.append(f"faith {r['faithfulness']}")
            lines.append(f"- **{r['id']}** `{r['query']}` — {', '.join(flags)}")
            if r["retrieved_slugs"]:
                lines.append(f"  - retrieved: `{', '.join(r['retrieved_slugs'][:3])}`")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    RESULTS.mkdir(parents=True, exist_ok=True)

    rows = []
    for q in queries:
        row = evaluate_query(q)
        rows.append(row)
        flags = []
        if row["score_retrieval"]:
            flags.append("H1=" + ("Y" if row["hit_at_1"] else "N"))
            flags.append("H3=" + ("Y" if row["hit_at_3"] else "N"))
        flags.append("cite=" + ("Y" if row["citation_ok"] else "N"))
        flags.append(f"faith={row['faithfulness']}")
        status = "OK" if row["intent_ok"] and row["contains_ok"] and row["citation_ok"] else "WARN"
        print(f"{status} {row['id']}: intent={row['predicted_intent']} {' '.join(flags)}")

    summary = summarize(rows)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "targets": TARGETS,
        "summary": summary,
        "results": rows,
    }
    out_json = RESULTS / "phase9_eval.json"
    out_md = RESULTS / "phase9_eval.md"
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, rows, out_md)

    print("\nPHASE 9 EVAL")
    print(f"  queries: {summary['query_count']} (retrieval-scored: {summary['retrieval_n']})")
    print(f"  Hit@1: {summary['hit_at_1_pct']}%  [{summary['gates']['hit_at_1']}]")
    print(f"  Hit@3: {summary['hit_at_3_pct']}%  [{summary['gates']['hit_at_3']}]")
    print(f"  Faithfulness: {summary['faithfulness_avg']}  [{summary['gates']['faithfulness']}]")
    print(f"  Citation: {summary['citation_pct']}%  [{summary['gates']['citation']}]")
    print(f"  Intent: {summary['intent_pct']}%  contains: {summary['contains_pct']}%")
    print(f"  results: {out_md.relative_to(ROOT)}")
    gates_ok = all(v == "PASS" for v in summary["gates"].values())
    return 0 if gates_ok else 1


if __name__ == "__main__":
    sys.exit(main())
