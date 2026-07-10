from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.models.base import Base
from core.models.entry import Entry  # noqa: F401
from core.services.entry_service import EntryService
from core.services.sync_service import SyncService
from database.engine import make_session_factory


@pytest.fixture()
def session_factory() -> sessionmaker[Session]:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return make_session_factory(engine)


@pytest.fixture()
def service(session_factory: sessionmaker[Session]) -> EntryService:
    return EntryService(session_factory)


@pytest.fixture()
def sync_service(session_factory: sessionmaker[Session]) -> SyncService:
    return SyncService(session_factory)
