"""Domain enumerations shared across layers."""
from __future__ import annotations

from enum import StrEnum


class EntryType(StrEnum):
    """Type of catalogued item. New types can be added without touching the core."""

    MOVIE = "movie"          # 🎬 фильм
    SERIES = "series"        # 📺 сериал
    # Reserved for future releases (no core changes required):
    # MINI_SERIES = "mini_series"
    # DOCUMENTARY = "documentary"
    # ANIME = "anime"
    # BOOK = "book"
    # GAME = "game"

    @property
    def is_episodic(self) -> bool:
        """Whether this type tracks seasons/episodes."""
        return self in {EntryType.SERIES}


class Status(StrEnum):
    """Watch/progress status."""

    PLANNED = "planned"      # Хочу посмотреть
    WATCHING = "watching"    # Смотрю
    PAUSED = "paused"        # На паузе
    COMPLETED = "completed"  # Просмотрено
    DROPPED = "dropped"      # Заброшено


STATUS_LABELS_RU: dict[Status, str] = {
    Status.PLANNED: "Хочу посмотреть",
    Status.WATCHING: "Смотрю",
    Status.PAUSED: "На паузе",
    Status.COMPLETED: "Просмотрено",
    Status.DROPPED: "Заброшено",
}

ENTRY_TYPE_LABELS_RU: dict[EntryType, str] = {
    EntryType.MOVIE: "Фильм",
    EntryType.SERIES: "Сериал",
}
