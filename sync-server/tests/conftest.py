from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from sync_server.database import init_db, make_session_factory
from sync_server.main import create_app
from sync_server.service import SyncService


@pytest.fixture()
def service() -> SyncService:
    # StaticPool + check_same_thread=False: FastAPI runs sync endpoints in a
    # worker thread pool, and a plain ":memory:" engine would otherwise hand
    # out a fresh empty database per connection/thread.
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    init_db(engine)
    return SyncService(make_session_factory(engine))


@pytest.fixture()
def app(service: SyncService) -> FastAPI:
    return create_app(service=service)


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c
