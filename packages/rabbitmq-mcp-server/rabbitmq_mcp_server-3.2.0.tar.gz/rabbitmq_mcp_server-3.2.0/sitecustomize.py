"""Ensure the project src/ directory is importable for all Python entrypoints."""

from __future__ import annotations

import logging as _  # noqa: F401  # CRITICAL: Import stdlib logging BEFORE adding src/ to path
import sys
from pathlib import Path

SRC_PATH = str(Path(__file__).resolve().parent / "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
