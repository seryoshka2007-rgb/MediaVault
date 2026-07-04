"""Server configuration via environment variables (typical for a deployable
service, unlike the desktop app's JSON config file)."""
from __future__ import annotations

import os
from pathlib import Path


def db_path() -> Path:
    return Path(os.environ.get("MEDIAVAULT_SYNC_DB", "sync.db")).resolve()


def setup_key() -> str:
    """Shared secret required once, to pair a new device (issue it a token).

    Must be set explicitly before exposing this server to a network - there
    is no built-in default, so an unconfigured deployment fails loudly
    instead of accepting devices with a well-known key.
    """
    key = os.environ.get("MEDIAVAULT_SYNC_SETUP_KEY")
    if not key:
        raise RuntimeError(
            "MEDIAVAULT_SYNC_SETUP_KEY is not set - refusing to start without a "
            "device-pairing secret."
        )
    return key
