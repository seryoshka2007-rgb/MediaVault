"""Logging configuration. Writes to logs/<YYYY-MM-DD>.log and rotates daily."""
from __future__ import annotations

import datetime as dt
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(logs_dir: Path, level: int = logging.INFO) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    logfile = logs_dir / f"{today}.log"

    handler = TimedRotatingFileHandler(
        logfile, when="midnight", backupCount=30, encoding="utf-8", utc=False
    )
    handler.setFormatter(logging.Formatter(_FORMAT))

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on re-init (e.g. in tests).
    if not any(isinstance(h, TimedRotatingFileHandler) for h in root.handlers):
        root.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT))
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(console)

    logging.getLogger(__name__).info("Logging initialized -> %s", logfile)
