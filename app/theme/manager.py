"""Loads modular Qt stylesheets (.qss) from the themes/ directory."""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
THEMES_DIR = ROOT / "themes"


def load_theme(name: str) -> str:
    """Return the QSS content for a theme, or empty string if missing."""
    qss = THEMES_DIR / f"{name}.qss"
    if not qss.exists():
        log.warning("Theme %r not found, falling back to default styling", name)
        return ""
    return qss.read_text(encoding="utf-8")
