"""First-run database initialization.

For v0.1 we create tables directly from metadata. From v0.2 onward, schema
changes should go through Alembic migrations instead of create_all().
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import Engine, inspect

from core.models.base import Base
from core.models.entry import Entry  # noqa: F401  (registers the table)

log = logging.getLogger(__name__)


def init_database(engine: Engine, db_path: Path) -> bool:
    """Create tables if the database is empty. Returns True if it was created."""
    created = not db_path.exists() or "entries" not in inspect(engine).get_table_names()
    Base.metadata.create_all(engine)
    if created:
        log.info("Database initialized at %s", db_path)
    return created
