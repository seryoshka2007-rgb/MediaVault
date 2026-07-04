"""FastAPI app for the MediaVault sync server.

Run with: ``uvicorn sync_server.main:create_app --factory``
(the factory form avoids touching disk / requiring env vars at import time,
so tests can call ``create_app(service=...)`` with an in-memory test service
instead of the real one).

Dependency functions (``get_service``/``get_device``) live at module level,
not as closures inside ``create_app()``: FastAPI resolves ``Annotated[...,
Depends(...)]`` string annotations (from ``from __future__ import
annotations``) via the function's ``__globals__`` only, not its enclosing
closure - a locally-defined dependency silently fails to resolve and the
parameter gets treated as a plain query param instead.
"""
from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sync_server.config import db_path, setup_key
from sync_server.database import init_db, make_engine, make_session_factory
from sync_server.models import Device
from sync_server.schemas import (
    PullResponse,
    PushRequest,
    PushResponse,
    RegisterDeviceRequest,
    RegisterDeviceResponse,
)
from sync_server.service import SyncService

_bearer = HTTPBearer()


def get_service(request: Request) -> SyncService:
    service: SyncService = request.app.state.service
    return service


def get_device(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    svc: Annotated[SyncService, Depends(get_service)],
) -> Device:
    device = svc.authenticate(creds.credentials)
    if device is None:
        raise HTTPException(status_code=401, detail="Invalid or unknown device token")
    return device


def create_app(service: SyncService | None = None) -> FastAPI:
    app = FastAPI(title="MediaVault Sync Server")

    if service is None:
        engine = make_engine(db_path())
        init_db(engine)
        service = SyncService(make_session_factory(engine))
    app.state.service = service

    @app.post("/devices/register", response_model=RegisterDeviceResponse)
    def register_device(
        body: RegisterDeviceRequest,
        svc: Annotated[SyncService, Depends(get_service)],
    ) -> RegisterDeviceResponse:
        if body.setup_key != setup_key():
            raise HTTPException(status_code=403, detail="Invalid setup key")
        return svc.register_device(body.label)

    @app.post("/sync/push", response_model=PushResponse)
    def push(
        body: PushRequest,
        svc: Annotated[SyncService, Depends(get_service)],
        _device: Annotated[Device, Depends(get_device)],
    ) -> PushResponse:
        return PushResponse(results=svc.push(body.entries))

    @app.get("/sync/pull", response_model=PullResponse)
    def pull(
        since: dt.datetime,
        svc: Annotated[SyncService, Depends(get_service)],
        _device: Annotated[Device, Depends(get_device)],
    ) -> PullResponse:
        return svc.pull(since)

    return app
