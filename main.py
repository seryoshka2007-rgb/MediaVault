"""MediaVault entry point.

Boot order: config -> logging -> database -> daily backup -> GUI.
Core (config/db/services) works without PySide6; only the GUI needs it.
"""
from __future__ import annotations

import logging
import sys

from config.settings import Settings, load_settings
from core.services.backup_service import BackupService
from core.services.entry_service import EntryService
from core.services.sync_service import SyncService
from core.utils.logging_setup import setup_logging
from core.utils.paths import resource_root
from database.engine import make_engine, make_session_factory
from database.init import init_database


def bootstrap() -> tuple[EntryService, SyncService, Settings]:
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

    session_factory = make_session_factory(engine)
    return EntryService(session_factory), SyncService(session_factory), settings


def main() -> int:
    entry_service, sync_service, settings = bootstrap()
    try:
        from PySide6.QtGui import QIcon
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
    app.setWindowIcon(QIcon(str(resource_root() / "resources" / "icon.ico")))
    window = MainWindow(entry_service, sync_service, settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
