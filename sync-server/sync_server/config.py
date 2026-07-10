"""Server configuration via environment variables (typical for a deployable
service, unlike the desktop app's JSON config file)."""
from __future__ import annotations

import os
from pathlib import Path


def db_path() -> Path:
    return Path(os.environ.get("MEDIAVAULT_SYNC_DB", "sync.db")).resolve()


def admin_key() -> str:
    """Shared secret for the server owner - registering with this key always
    resolves to the single admin Person (only admin devices may delete
    catalog Titles, see service.py).

    Must be set explicitly before exposing this server to a network - there
    is no built-in default, so an unconfigured deployment fails loudly
    instead of accepting devices with a well-known key. Env var name kept
    as MEDIAVAULT_SYNC_SETUP_KEY for compatibility with already-deployed
    systemd units from before roles existed.
    """
    key = os.environ.get("MEDIAVAULT_SYNC_SETUP_KEY")
    if not key:
        raise RuntimeError(
            "MEDIAVAULT_SYNC_SETUP_KEY is not set - refusing to start without a "
            "device-pairing secret."
        )
    return key


def participant_key() -> str | None:
    """Shared secret for participants (lower privilege - can add/edit catalog
    Titles and their own UserState, but never delete a Title). Optional: if
    unset, participant registration is simply disabled until configured."""
    return os.environ.get("MEDIAVAULT_SYNC_PARTICIPANT_KEY")
