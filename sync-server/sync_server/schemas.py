"""Pydantic DTOs for the sync API. These are the only shapes that cross the
HTTP boundary - handlers never return ORM objects directly."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class TitleSync(BaseModel):
    """Shared catalog entry as exchanged over the sync protocol - no
    personal fields (status/rating/...) here, see UserStateSync."""

    model_config = ConfigDict(from_attributes=True)

    uuid: str = Field(min_length=1, max_length=36)
    type: str
    title: str
    original_title: str | None = None
    year: int | None = None
    url: str | None = None
    description: str | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None


class UserStateSync(BaseModel):
    """One person's personal state for one title. ``person_id`` is
    deliberately absent - the server always derives it from the
    authenticated device, a client can never claim to push someone else's
    state."""

    model_config = ConfigDict(from_attributes=True)

    title_uuid: str = Field(min_length=1, max_length=36)
    status: str
    rating: int | None = Field(default=None, ge=0, le=10)
    rating_other: int | None = Field(default=None, ge=0, le=10)
    is_favorite: bool = False
    season: int | None = None
    episode: int | None = None
    open_count: int = 0
    last_watched_at: dt.datetime | None = None
    comment: str | None = None
    updated_at: dt.datetime


class PushRequest(BaseModel):
    titles: list[TitleSync] = Field(default_factory=list)
    states: list[UserStateSync] = Field(default_factory=list)


class PushResult(BaseModel):
    key: str  # a title uuid, for both title and state results
    applied: bool
    reason: str | None = None  # set when applied=False, e.g. "requires admin role"


class PushResponse(BaseModel):
    title_results: list[PushResult]
    state_results: list[PushResult]


class PullResponse(BaseModel):
    titles: list[TitleSync]
    states: list[UserStateSync]
    server_time: dt.datetime


class RegisterRequest(BaseModel):
    key: str
    person_name: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=200)


class RegisterResponse(BaseModel):
    device_id: int
    token: str
    person_name: str
    role: str
