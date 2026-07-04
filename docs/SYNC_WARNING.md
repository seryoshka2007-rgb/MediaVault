# ⚠️ Folder sync and SQLite (read before enabling sync)

The spec (v1) syncs the library via a shared folder (Syncthing / OneDrive / Dropbox / Google Drive).
**Syncing a live SQLite file at the file level can corrupt the database** if two machines
touch it around the same time, and WAL mode adds `-wal`/`-shm` sidecar files that must stay
consistent with the main file — file sync does not guarantee this.

Recommended approach for v1:
- Do **not** point the sync folder at the live `.db`.
- Instead sync an **export** (e.g. a consistent backup snapshot or a JSON export), and import on
  the other machine. `BackupService` already produces consistent snapshots via SQLite's backup API.
- Treat "one writer at a time" as a hard rule until v3 (real change-based sync) lands.

This is the single biggest data-loss risk in the current plan — hence a dedicated note.
