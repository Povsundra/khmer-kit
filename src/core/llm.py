"""OpenRouter LLM client for grounded generation."""

from __future__ import annotations

import re

import requests

from src.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL


def llm_available() -> bool:
    return bool(OPENROUTER_API_KEY)


def generate(messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key."
        )

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/khmer-kit",
        "X-Title": "Khmer Kitchen Companion",
    }
    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _strip_fences(content.strip())


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```(?:\w+)?\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()
