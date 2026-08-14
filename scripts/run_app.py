#!/usr/bin/env python3
"""Launch the Khmer Kitchen Companion Streamlit app."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "interfaces" / "web" / "app.py"

os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("USE_TF", "0")


def main() -> int:
    if not APP.is_file():
        print(f"App not found: {APP}", file=sys.stderr)
        return 1
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    print("Starting Khmer Kitchen Companion at http://localhost:8501")
    return subprocess.call(cmd, cwd=str(ROOT))


if __name__ == "__main__":
    sys.exit(main())
