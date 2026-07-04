from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from core.models.base import Base
from core.models.entry import Entry  # noqa: F401
from core.services.entry_service import EntryService
from database.engine import make_session_factory


@pytest.fixture()
def service() -> EntryService:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return EntryService(make_session_factory(engine))
