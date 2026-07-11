"""FastAPI app for the MediaVault sync server.

Run with: ``uvicorn sync_server.main:create_app --factory``
(the factory form avoids touching disk / requiring env vars at import time,
so tests can call ``create_app(service=...)`` with an in-memory test service
instead of the real one).

Dependency functions (``get_service``/``get_auth``) live at module level,
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

from sync_server.config import db_path
from sync_server.database import init_db, make_engine, make_session_factory
from sync_server.schemas import (
    PersonSummary,
    PullResponse,
    PushRequest,
    PushResponse,
    RegisterRequest,
    RegisterResponse,
)
from sync_server.service import (
    AuthenticatedDevice,
    SyncAuthError,
    SyncNotFoundError,
    SyncPermissionError,
    SyncService,
)

_bearer = HTTPBearer()


def get_service(request: Request) -> SyncService:
    service: SyncService = request.app.state.service
    return service


def get_auth(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    svc: Annotated[SyncService, Depends(get_service)],
) -> AuthenticatedDevice:
    auth = svc.authenticate(creds.credentials)
    if auth is None:
        raise HTTPException(status_code=401, detail="Invalid or unknown device token")
    return auth


def create_app(service: SyncService | None = None) -> FastAPI:
    app = FastAPI(title="MediaVault Sync Server")

    if service is None:
        engine = make_engine(db_path())
        init_db(engine)
        service = SyncService(make_session_factory(engine))
    app.state.service = service

    @app.post("/devices/register", response_model=RegisterResponse)
    def register_device(
        body: RegisterRequest,
        svc: Annotated[SyncService, Depends(get_service)],
    ) -> RegisterResponse:
        try:
            return svc.register(body.key, body.person_name, body.label)
        except SyncAuthError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except SyncPermissionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/sync/push", response_model=PushResponse)
    def push(
        body: PushRequest,
        svc: Annotated[SyncService, Depends(get_service)],
        auth: Annotated[AuthenticatedDevice, Depends(get_auth)],
    ) -> PushResponse:
        title_results, state_results = svc.push(auth, body.titles, body.states)
        return PushResponse(title_results=title_results, state_results=state_results)

    @app.get("/sync/pull", response_model=PullResponse)
    def pull(
        since: dt.datetime,
        svc: Annotated[SyncService, Depends(get_service)],
        auth: Annotated[AuthenticatedDevice, Depends(get_auth)],
    ) -> PullResponse:
        return svc.pull(auth, since)

    @app.get("/admin/people", response_model=list[PersonSummary])
    def list_people(
        svc: Annotated[SyncService, Depends(get_service)],
        auth: Annotated[AuthenticatedDevice, Depends(get_auth)],
    ) -> list[PersonSummary]:
        try:
            return svc.list_people(auth)
        except SyncPermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.delete("/admin/devices/{device_id}", status_code=204)
    def revoke_device(
        device_id: int,
        svc: Annotated[SyncService, Depends(get_service)],
        auth: Annotated[AuthenticatedDevice, Depends(get_auth)],
    ) -> None:
        try:
            svc.revoke_device(auth, device_id)
        except SyncPermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except SyncNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app
