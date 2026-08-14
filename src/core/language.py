"""Detect query language and pick monolingual display text from chunks."""

from __future__ import annotations

import re
from typing import Any, Literal

QueryLanguage = Literal["en", "kh"]

KHMER_RE = re.compile(r"[\u1780-\u17FF]")


def detect_query_language(query: str) -> QueryLanguage:
    """Khmer if the query contains Khmer script; otherwise English."""
    return "kh" if KHMER_RE.search(query) else "en"


def chunk_title(hit: dict[str, Any], lang: QueryLanguage) -> str:
    if hit.get("chunk_type") == "parent":
        return hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
    name = hit["dish_name_kh"] if lang == "kh" else hit["dish_name_en"]
    if hit.get("chunk_type") == "ingredients":
        label = "គ្រឿងផ្សំ" if lang == "kh" else "ingredients"
        return f"{name} · {label}"
    step = hit.get("step")
    if step is None:
        return name
    if lang == "kh":
        return f"{name} · ជំហាន {step}"
    return f"{name} · step {step}"


def chunk_body(hit: dict[str, Any], lang: QueryLanguage) -> str:
    if hit.get("chunk_type") == "ingredients":
        items = hit.get("ingredients") or []
        if items:
            if lang == "kh":
                return "\n".join(f"- {item['raw_kh']}" for item in items)
            return "\n".join(f"- {item['standardized_en']}" for item in items)
    if lang == "kh":
        return hit.get("text_kh", "").strip()
    return hit.get("text_en", "").strip()
