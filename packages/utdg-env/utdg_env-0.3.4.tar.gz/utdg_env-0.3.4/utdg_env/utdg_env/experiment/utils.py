# utdg_env/experiment/utils.py

"""
Utility helpers for the ExperimentManager module.
"""

from __future__ import annotations

import os
from pathlib import Path
import datetime


def ensure_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def timestamp_utc() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def indent_block(text: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(pad + line for line in text.splitlines())
