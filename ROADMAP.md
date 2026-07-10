# Roadmap

| Version | Scope | Status |
|---|---|---|
| v0.1 | Project skeleton, layering | done (this archive) |
| v0.2 | SQLite + Alembic baseline migration | in progress |
| v0.3 | Main window (search / filter / list) | |
| v0.4 | Full CRUD dialogs | |
| v0.5 | Search across fields + filters | |
| v0.6 | Series navigation (next/prev episode) | core done |
| v0.7 | Settings screen | |
| v0.8 | Scheduled + pre-operation backups | core done |
| v0.9 | Link import via providers | scaffolded |
| v1.0 | First full release | |
| v2.0-A | Multiplatform design + sync-server skeleton + mobile/ scaffold | done (this session) |
| v2.0-B | `Entry.uuid`/`deleted_at` + migration, `core/services/sync_service.py`, "Синхронизировать" в GUI | done — sync-server deployed on user's Debian server (Tailscale), desktop client wired up |
| v2.0-C | Flutter mobile app (iOS+Android) — screens, local DB, sync client | |
| v2.0-D | macOS build of the desktop app via GitHub Actions CI (no physical Mac needed) | done — `.github/workflows/build-macos.yml`, unsigned .app (Gatekeeper warning on first run) |

See `docs/MULTIPLATFORM.md` for the full architecture (sync protocol, conflict
resolution, why iOS/Android need a separate Flutter codebase instead of
reusing PySide6).

## Post-v1 ideas (parking lot)
- Additional entry types (anime, book, game) — architecture already supports.
- Theme editor, posters, plugin system.
