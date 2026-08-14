#!/usr/bin/env python3
"""Phase 6: compare retrieval configs and write results."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.retrieve import search  # noqa: E402

EVAL = ROOT / "eval"
RESULTS = EVAL / "results"
CONFIGS_PATH = EVAL / "retrieval_configs.json"
QUERIES_PATH = EVAL / "test_queries_retrieval.json"
WINNER_PATH = EVAL / "retrieval_winner.json"


def slug_from_hit(hit: dict) -> str:
    if hit.get("chunk_type") == "parent":
        return hit.get("slug", f"_parent_{hit.get('category', '')}")
    return hit.get("slug", "")


def evaluate_config(config: dict, queries: list[dict], *, top_k: int = 3) -> dict:
    hits_at_1 = 0
    hits_at_3 = 0
    by_type: dict[str, dict[str, int]] = {}

    for q in queries:
        qtype = q.get("query_type", "exact_lookup")
        bucket = by_type.setdefault(qtype, {"total": 0, "hit_at_1": 0, "hit_at_3": 0})
        bucket["total"] += 1

        results = search(
            q["query"],
            mode=config["mode"],
            top_k=top_k,
            semantic_weight=config.get("semantic_weight", 0.6),
            bm25_weight=config.get("bm25_weight", 0.4),
        )
        slugs = [slug_from_hit(r) for r in results]
        expected = q["expected_slug"]

        if slugs and slugs[0] == expected:
            hits_at_1 += 1
            bucket["hit_at_1"] += 1
        if expected in slugs[:top_k]:
            hits_at_3 += 1
            bucket["hit_at_3"] += 1

    total = len(queries)
    return {
        "config_id": config["id"],
        "label": config["label"],
        "hit_at_1": hits_at_1,
        "hit_at_3": hits_at_3,
        "hit_at_1_pct": round(100 * hits_at_1 / total, 1),
        "hit_at_3_pct": round(100 * hits_at_3 / total, 1),
        "by_query_type": {
            k: {
                **v,
                "hit_at_1_pct": round(100 * v["hit_at_1"] / v["total"], 1),
                "hit_at_3_pct": round(100 * v["hit_at_3"] / v["total"], 1),
            }
            for k, v in by_type.items()
        },
    }


def pick_winner(rows: list[dict]) -> dict:
    return max(rows, key=lambda r: (r["hit_at_3"], r["hit_at_1"]))


def write_markdown(rows: list[dict], winner: dict, path: Path, *, query_count: int) -> None:
    lines = [
        "# Retrieval Comparison (Phase 6)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Summary",
        "",
        "| Config | Hit@1 | Hit@3 |",
        "|--------|-------|-------|",
    ]
    for r in rows:
        lines.append(
            f"| {r['label']} | {r['hit_at_1']}/{query_count} ({r['hit_at_1_pct']}%) | "
            f"{r['hit_at_3']}/{query_count} ({r['hit_at_3_pct']}%) |"
        )
    lines.extend(
        [
            "",
            f"**Winner for Phase 7:** `{winner['config_id']}` — {winner['label']}",
            "",
            "## By query type",
            "",
        ]
    )
    for r in rows:
        lines.append(f"### {r['label']}")
        lines.append("")
        lines.append("| Type | Hit@1 | Hit@3 |")
        lines.append("|------|-------|-------|")
        for qtype, stats in r["by_query_type"].items():
            lines.append(
                f"| {qtype} | {stats['hit_at_1']}/{stats['total']} ({stats['hit_at_1_pct']}%) | "
                f"{stats['hit_at_3']}/{stats['total']} ({stats['hit_at_3_pct']}%) |"
            )
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    configs = json.loads(CONFIGS_PATH.read_text(encoding="utf-8"))
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))

    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [evaluate_config(cfg, queries) for cfg in configs]
    winner = pick_winner(rows)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query_count": len(queries),
        "results": rows,
        "winner": winner,
    }
    out_json = RESULTS / "retrieval_comparison.json"
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_markdown(rows, winner, RESULTS / "retrieval_comparison.md", query_count=len(queries))

    WINNER_PATH.write_text(
        json.dumps(
            {
                "config_id": winner["config_id"],
                "label": winner["label"],
                "hit_at_1_pct": winner["hit_at_1_pct"],
                "hit_at_3_pct": winner["hit_at_3_pct"],
                "locked_for_phase_7": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("RETRIEVAL EXPERIMENTS: PASS")
    print(f"  - queries: {len(queries)}")
    for r in rows:
        print(f"  - {r['config_id']}: Hit@1={r['hit_at_1_pct']}% Hit@3={r['hit_at_3_pct']}%")
    print(f"  - winner: {winner['config_id']}")
    print(f"  - results: {out_json.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
