# Architecture

## Layers
1. **app/** — PySide6 GUI. No business logic, no SQL. Calls services.
2. **core/services/** — business logic; the only entry point for the GUI.
3. **core/repositories/** — data access (Repository pattern). Only place with ORM queries.
4. **core/models/** — SQLAlchemy ORM models.
5. **database/** — engine, session factory, first-run init.
6. **providers/** — optional external metadata sources (link import), behind a Protocol.
7. **config/** — validated settings (pydantic).

## Extensibility
- New entry types: add to `EntryType`. Episodic behaviour is driven by `EntryType.is_episodic`,
  not by hardcoded branches, so movies/books/games slot in without core changes.
- New providers: implement the `Provider` protocol and register in `ProviderRegistry`.
- Themes: drop a `<name>.qss` into `themes/` (modular, hot-swappable).

## Why DTOs
The GUI never touches ORM objects. `EntryCreate/Update/Read` decouple UI from schema and
centralise validation, so a DB schema change doesn't ripple into every dialog.
