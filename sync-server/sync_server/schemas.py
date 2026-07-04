"""Pydantic DTOs for the sync API. These are the only shapes that cross the
HTTP boundary - handlers never return ORM objects directly."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class EntrySync(BaseModel):
    """One library entry as exchanged over the sync protocol."""

    model_config = ConfigDict(from_attributes=True)

    uuid: str = Field(min_length=1, max_length=36)
    type: str
    title: str
    original_title: str | None = None
    status: str
    rating: int | None = Field(default=None, ge=0, le=10)
    rating_other: int | None = Field(default=None, ge=0, le=10)
    year: int | None = None
    url: str | None = None
    open_count: int = 0
    description: str | None = None
    comment: str | None = None
    is_favorite: bool = False
    season: int | None = None
    episode: int | None = None
    last_watched_at: dt.datetime | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None


class PushRequest(BaseModel):
    entries: list[EntrySync]


class PushResult(BaseModel):
    uuid: str
    applied: bool  # False means the server already had a newer version (LWW)


class PushResponse(BaseModel):
    results: list[PushResult]


class PullResponse(BaseModel):
    entries: list[EntrySync]
    server_time: dt.datetime


class RegisterDeviceRequest(BaseModel):
    setup_key: str
    label: str = Field(min_length=1, max_length=200)


class RegisterDeviceResponse(BaseModel):
    device_id: int
    token: str
