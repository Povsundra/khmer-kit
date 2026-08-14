#!/usr/bin/env python3
"""Phase 5: build FAISS + BM25 index from processed corpus."""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_prep.build_index import build_index  # noqa: E402


def main() -> int:
    try:
        manifest = build_index(show_progress=True)
    except Exception as e:
        print(f"BUILD INDEX: FAIL — {e}", file=sys.stderr)
        return 1

    print("BUILD INDEX: PASS")
    print(
        f"  - chunks: {manifest['chunk_count']} "
        f"({manifest['ingredient_chunks']} ingredients + {manifest['step_chunks']} steps + "
        f"{manifest['parent_chunks']} parents)"
    )
    print(f"  - model: {manifest['embedding_model']}")
    print(f"  - output: data/index/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
