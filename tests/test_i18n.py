"""app.i18n - dictionary-based translations, no Qt .ts/.qm pipeline."""
from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.i18n import (
    SUPPORTED_LANGUAGES,
    current_language,
    entry_type_label,
    set_language,
    sort_label,
    status_label,
    t,
)
from core.enums import EntryType, SortOption, Status


@pytest.fixture(autouse=True)
def _reset_language() -> Iterator[None]:
    yield
    set_language("ru")


def test_default_language_is_russian() -> None:
    assert current_language() == "ru"
    assert t("add") == "Добавить"


def test_set_language_changes_translation() -> None:
    set_language("en")
    assert t("add") == "Add"
    set_language("uk")
    assert t("add") == "Додати"


def test_unsupported_language_falls_back_to_russian() -> None:
    set_language("fr")
    assert current_language() == "ru"
    assert t("add") == "Добавить"


def test_format_placeholders() -> None:
    set_language("en")
    assert t("already_added", title="Dune") == "Already added: Dune"


def test_status_entry_type_sort_labels_per_language() -> None:
    assert status_label(Status.WATCHING) == "Смотрю"
    assert entry_type_label(EntryType.MOVIE) == "Фильм"
    assert sort_label(SortOption.YEAR_DESC) == "Год"

    set_language("en")
    assert status_label(Status.WATCHING) == "Watching"
    assert entry_type_label(EntryType.MOVIE) == "Movie"
    assert sort_label(SortOption.YEAR_DESC) == "Year"


def test_supported_languages_lists_ru_en_uk() -> None:
    assert set(SUPPORTED_LANGUAGES) == {"ru", "en", "uk"}
