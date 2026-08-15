"""Configuration paths and environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def secrets_toml_exists() -> bool:
    """True when a Streamlit secrets.toml is on disk (local file or Cloud-injected)."""
    return any(
        path.is_file()
        for path in (
            ROOT / ".streamlit" / "secrets.toml",
            Path.cwd() / ".streamlit" / "secrets.toml",
            Path.home() / ".streamlit" / "secrets.toml",
        )
    )


def _secret(name: str, default: str = "") -> str:
    val = os.getenv(name, "")
    if val:
        return val
    if not secrets_toml_exists():
        return default
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        if get_script_run_ctx() is None:
            return default
        import streamlit as st

        return str(st.secrets[name])
    except Exception:
        return default


DATA = ROOT / "data"
DOCS = ROOT / "docs"
PROCESSED = DATA / "processed"
INDEX_DIR = DATA / "index"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "paraphrase-multilingual-mpnet-base-v2"
)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

RETRIEVAL_MIN_SCORE = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.35"))

CHECKLIST_PATH = DOCS / "dish_checklist.json"
ALIASES_PATH = DATA / "knowledge" / "dish_aliases.json"

CATEGORIES = ("samlor", "cha", "other", "dessert")

FAISS_PATH = INDEX_DIR / "faiss.index"
DOCSTORE_PATH = INDEX_DIR / "docstore.json"
BM25_PATH = INDEX_DIR / "bm25_corpus.json"
MANIFEST_PATH = INDEX_DIR / "manifest.json"


def openrouter_api_key() -> str:
    return _secret("OPENROUTER_API_KEY")


def openrouter_model() -> str:
    return _secret("OPENROUTER_MODEL", "google/gemini-2.0-flash-001")
