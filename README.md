# MediaVault

Local, offline-first personal media library for Windows (movies & series, extensible).

## Quick start
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements-dev.txt
python main.py
```
The core (config, database, services) runs even without PySide6 installed; only the GUI requires it.

## Architecture (strict layering)
```
GUI (app/)  ->  Services (core/services)  ->  Repositories (core/repositories)  ->  ORM (core/models)  ->  SQLite
```
Rules:
- The GUI calls **services only** — never repositories, ORM, or SQL.
- All DB access goes through repositories; **no raw SQL** anywhere.
- Data crossing the GUI/service boundary is a validated **pydantic DTO** (`core/schemas.py`), not an ORM object.

## Testing / quality
```bash
pytest
ruff check .
mypy .
```

## Build
```bash
pyinstaller --noconfirm --windowed --name MediaVault main.py
```

See `docs/SYNC_WARNING.md` before enabling folder sync, and `ROADMAP.md` for the release plan.
