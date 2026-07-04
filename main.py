"""MediaVault entry point.

Boot order: config -> logging -> database -> daily backup -> GUI.
Core (config/db/services) works without PySide6; only the GUI needs it.
"""
from __future__ import annotations

import logging
import sys

from config.settings import load_settings
from core.services.backup_service import BackupService
from core.services.entry_service import EntryService
from core.utils.logging_setup import setup_logging
from database.engine import make_engine, make_session_factory
from database.init import init_database


def bootstrap() -> EntryService:
    settings = load_settings()
    setup_logging(settings.logs_path())
    log = logging.getLogger("mediavault")
    log.info("Starting MediaVault")

    engine = make_engine(settings.db_path())
    init_database(engine, settings.db_path())

    if settings.autobackup_daily:
        BackupService(
            settings.db_path(), settings.backups_path(), keep=settings.backup_keep
        ).create_daily_if_needed()

    return EntryService(make_session_factory(engine))


def main() -> int:
    service = bootstrap()
    try:
        from PySide6.QtWidgets import QApplication

        from app.theme.manager import load_theme
        from app.windows.main_window import MainWindow
    except ImportError:
        print(
            "Core initialized OK. GUI unavailable (PySide6 not installed).\n"
            "Install dependencies with: pip install -r requirements.txt"
        )
        return 0

    app = QApplication(sys.argv)
    app.setStyleSheet(load_theme("neon_dark"))
    window = MainWindow(service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
