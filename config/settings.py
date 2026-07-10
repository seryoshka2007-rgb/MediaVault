"""Application settings loaded from config/settings.json (validated with pydantic).

Validation up front means a corrupted/edited config fails loudly with a clear
message instead of causing weird runtime behaviour.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from core.utils.files import atomic_write_text
from core.utils.paths import app_root

# Where user data lives: repo root in dev, the .exe's own folder when frozen.
ROOT = app_root()
CONFIG_PATH = ROOT / "config" / "settings.json"
DEFAULT_CONFIG_PATH = ROOT / "config" / "settings.default.json"


class Settings(BaseModel):
    theme: str = "neon_dark"
    language: str = "ru"
    database_path: str = "database/mediavault.db"
    backups_dir: str = "backups"
    logs_dir: str = "logs"
    backup_keep: int = Field(default=30, ge=1)
    autobackup_daily: bool = True
    sync_dir: str | None = None  # optional shared folder for v1 sync
    sync_server_url: str | None = None
    sync_device_token: str | None = None
    sync_role: str | None = None  # "admin" | "participant" - from registration
    sync_last_synced_at: str | None = None  # ISO timestamp; JSON has no native datetime

    # -- resolved absolute paths ---------------------------------------------
    def db_path(self) -> Path:
        return (ROOT / self.database_path).resolve()

    def backups_path(self) -> Path:
        return (ROOT / self.backups_dir).resolve()

    def logs_path(self) -> Path:
        return (ROOT / self.logs_dir).resolve()


def load_settings() -> Settings:
    path = CONFIG_PATH if CONFIG_PATH.exists() else DEFAULT_CONFIG_PATH
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        settings = Settings.model_validate(data)
    else:
        settings = Settings()
    # Materialize a user config on first run.
    if not CONFIG_PATH.exists():
        save_settings(settings)
    return settings


def save_settings(settings: Settings) -> None:
    atomic_write_text(
        CONFIG_PATH, json.dumps(settings.model_dump(), indent=2, ensure_ascii=False)
    )
