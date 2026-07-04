"""Path helpers that work both from source and from a frozen PyInstaller build.

``__file__``-relative paths break once bundled: PyInstaller extracts modules
into a temp/internal directory that has nothing to do with where the actual
``.exe`` sits, so anything computed from ``__file__`` alone would either lose
data between runs (onefile) or bury it inside ``_internal/`` instead of next
to the executable.
"""
from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Where user data (db/backups/logs/config) lives.

    The folder containing the running ``.exe`` when frozen, else the repo root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def resource_root() -> Path:
    """Where bundled read-only resources (themes, icons) live.

    PyInstaller's extraction directory when frozen, else the repo root.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_root()))
    return Path(__file__).resolve().parent.parent.parent
