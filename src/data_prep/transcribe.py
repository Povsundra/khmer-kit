"""Vision-LLM transcription: recipe scan PNG → Khmer raw text draft."""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path

import requests

from src.config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_URL

SYSTEM_PROMPT = """You are a Khmer recipe transcription assistant for the Khmer Kitchen Companion project.

TASK: Transcribe the recipe in the image EXACTLY into Khmer.

RULES:
- Preserve original Khmer wording — do not modernize or correct culinary terms
- Mark unclear characters as [UNCLEAR: best guess] — never silently guess
- IGNORE page footers, page numbers, URLs, watermarks, decorative symbols
- IGNORE bleed-through ghost text from the reverse side of the page
- Output ONLY the recipe content in this structure:

[Khmer dish title on first line]

គ្រឿងផ្សំ
[ingredients text exactly as printed]

របៀបធ្វើ
1- [first step]
2- [second step]
(continue numbering if the method has clear sequential actions; otherwise one paragraph split logically)

- Do NOT add technique notes, common mistakes, or English translation
- Do NOT add markdown fences or commentary
"""


def _encode_image(image_path: Path) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(str(image_path))
    mime = mime or "image/png"
    data = base64.standard_b64encode(image_path.read_bytes()).decode("ascii")
    return mime, data


def transcribe_image(image_path: Path, *, dish_hint: str = "") -> str:
    """Send recipe scan to Vision LLM and return Khmer transcription."""
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key."
        )
    if not image_path.is_file():
        raise FileNotFoundError(f"Scan not found: {image_path}")

    mime, b64 = _encode_image(image_path)
    user_text = "Transcribe this Khmer recipe image."
    if dish_hint:
        user_text += f" Expected dish (verify against image): {dish_hint}"

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                ],
            },
        ],
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/khmer-kit",
        "X-Title": "Khmer Kitchen Companion",
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return _strip_fences(content.strip())


def _strip_fences(text: str) -> str:
    text = re.sub(r"^```(?:\w+)?\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def build_raw_draft(
    *,
    slug: str,
    source_type: str,
    source_citation: str,
    khmer_body: str,
    scan_path: str,
) -> str:
    """Wrap Khmer transcription with metadata header for human review."""
    return (
        f"# slug: {slug}\n"
        f"# source_type: {source_type}\n"
        f"# source_citation: {source_citation}\n"
        f"# verified: no\n"
        f"# notes: DRAFT from Vision-LLM — review every character against scan\n"
        f"# scan: {scan_path}\n"
        f"\n"
        f"{khmer_body.strip()}\n"
    )


def draft_output_path(raw_path: str | Path) -> Path:
    """Map data/raw/.../slug.txt → slug.DRAFT.txt"""
    p = Path(raw_path)
    return p.with_name(p.stem + ".DRAFT.txt")
