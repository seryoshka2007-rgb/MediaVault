"""Pydantic DTOs. These are the ONLY data shapes that cross the GUI <-> service boundary.

The GUI never sees ORM objects directly; services accept/return validated DTOs.
This keeps validation in one place and decouples the UI from the database schema.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.enums import EntryType, Status


class EntryCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    type: EntryType = EntryType.MOVIE
    title: str = Field(min_length=1, max_length=500)
    original_title: str | None = Field(default=None, max_length=500)
    status: Status = Status.PLANNED
    rating: int | None = Field(default=None, ge=0, le=10)
    rating_other: int | None = Field(default=None, ge=0, le=10)
    year: int | None = Field(default=None, ge=1870, le=2100)
    url: str | None = Field(default=None, max_length=2000)
    description: str | None = None
    comment: str | None = None
    is_favorite: bool = False
    season: int | None = Field(default=None, ge=0)
    episode: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_episodic(self) -> EntryCreate:
        if not self.type.is_episodic and (self.season or self.episode):
            # Silently ignore episodic fields on non-episodic types.
            object.__setattr__(self, "season", None)
            object.__setattr__(self, "episode", None)
        return self


class EntryUpdate(BaseModel):
    """All fields optional — only provided fields are changed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=500)
    original_title: str | None = Field(default=None, max_length=500)
    status: Status | None = None
    rating: int | None = Field(default=None, ge=0, le=10)
    rating_other: int | None = Field(default=None, ge=0, le=10)
    year: int | None = Field(default=None, ge=1870, le=2100)
    url: str | None = Field(default=None, max_length=2000)
    description: str | None = None
    comment: str | None = None
    is_favorite: bool | None = None
    season: int | None = Field(default=None, ge=0)
    episode: int | None = Field(default=None, ge=0)


class EntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uuid: str
    type: EntryType
    title: str
    original_title: str | None
    status: Status
    rating: int | None
    rating_other: int | None
    year: int | None
    url: str | None
    open_count: int
    description: str | None
    comment: str | None
    is_favorite: bool
    season: int | None
    episode: int | None
    last_watched_at: dt.datetime | None
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None


class EntrySyncData(BaseModel):
    """Wire format for the sync protocol — mirrors sync-server's EntrySync.

    Deliberately separate from EntryRead: this has no `id` (local ids don't
    mean anything across devices — `uuid` is the sync identity), and unlike
    EntryRead it's also used to validate incoming JSON from the server, not
    just to read local ORM state.
    """

    model_config = ConfigDict(from_attributes=True)

    uuid: str
    type: EntryType
    title: str
    original_title: str | None = None
    status: Status
    rating: int | None = None
    rating_other: int | None = None
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


class SyncResult(BaseModel):
    pushed: int
    pulled: int
    synced_at: dt.datetime
