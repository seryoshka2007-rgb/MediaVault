"""Loads modular Qt stylesheets (.qss) from the themes/ directory."""
from __future__ import annotations

import logging

from core.utils.paths import resource_root

log = logging.getLogger(__name__)

THEMES_DIR = resource_root() / "themes"


def load_theme(name: str) -> str:
    """Return the QSS content for a theme, or empty string if missing."""
    qss = THEMES_DIR / f"{name}.qss"
    if not qss.exists():
        log.warning("Theme %r not found, falling back to default styling", name)
        return ""
    return qss.read_text(encoding="utf-8")
