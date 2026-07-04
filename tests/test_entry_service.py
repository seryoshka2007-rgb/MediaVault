from __future__ import annotations

from core.enums import EntryType, Status
from core.schemas import EntryCreate, EntryUpdate
from core.services.entry_service import EntryService


def test_quick_add_and_list(service: EntryService) -> None:
    created = service.quick_add("Inception")
    assert created.title == "Inception"
    assert created.status == Status.PLANNED
    assert len(service.list_all()) == 1


def test_search(service: EntryService) -> None:
    service.quick_add("The Matrix")
    service.quick_add("Interstellar")
    assert len(service.search("matrix")) == 1
    assert len(service.search("")) == 2


def test_update_and_delete(service: EntryService) -> None:
    e = service.quick_add("Dune")
    updated = service.update(e.id, EntryUpdate(status=Status.COMPLETED, rating=9))
    assert updated is not None and updated.rating == 9
    assert service.delete(e.id) is True
    assert service.get(e.id) is None


def test_series_navigation(service: EntryService) -> None:
    s = service.create(EntryCreate(title="Breaking Bad", type=EntryType.SERIES,
                                   season=1, episode=1))
    nxt = service.next_episode(s.id)
    assert nxt is not None and nxt.episode == 2 and nxt.status == Status.WATCHING


def test_find_duplicate_by_url(service: EntryService) -> None:
    url = "https://kinogo.ec/125434-mandalorec-i-grogu.html"
    service.create(EntryCreate(title="The Mandalorian", url=url))
    dup = service.find_duplicate(title="Something Else", entry_type=EntryType.MOVIE, url=url)
    assert dup is not None and dup.title == "The Mandalorian"


def test_find_duplicate_by_title_and_type(service: EntryService) -> None:
    service.create(EntryCreate(title="Dune", type=EntryType.MOVIE))
    same_type = service.find_duplicate(title="dune", entry_type=EntryType.MOVIE, url=None)
    other_type = service.find_duplicate(title="Dune", entry_type=EntryType.SERIES, url=None)
    assert same_type is not None
    assert other_type is None


def test_year_and_rating_other_roundtrip(service: EntryService) -> None:
    created = service.create(
        EntryCreate(title="Dune", year=2021, rating=8, rating_other=6)
    )
    assert created.year == 2021
    assert created.rating == 8
    assert created.rating_other == 6
