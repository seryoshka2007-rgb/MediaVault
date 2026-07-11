"""SQLite engine and session factory.

PRAGMAs enforce foreign keys and enable WAL for better local concurrency.
NOTE: WAL creates -wal/-shm sidecar files. Do NOT sync a live WAL database
through file-level sync tools (see docs/SYNC_WARNING.md).
"""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry


def make_engine(db_path: Path, *, echo: bool = False) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False: the background sync worker (app/workers/sync_worker.py)
    # opens sessions on this same engine from a QThread, while the GUI thread may
    # still be reading. SQLAlchemy's pool already ensures a connection is only
    # checked out to one caller at a time; this just lifts pysqlite's own
    # same-thread-as-creation restriction so pooled connections can move
    # between threads across checkouts.
    engine = create_engine(
        f"sqlite:///{db_path}", echo=echo, future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(
        dbapi_conn: DBAPIConnection, _record: ConnectionPoolEntry
    ) -> None:
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine, class_=Session, expire_on_commit=False, future=True
    )
