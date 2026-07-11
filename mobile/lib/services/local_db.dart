/// Local on-device storage. STUB - Phase C work, not implemented yet.
///
/// Mirrors the role of core/repositories/entry_repository.py on the desktop
/// side: this is the *only* place that should touch the local sqflite
/// database once this is filled in - screens/services must go through here,
/// not query the database directly (same layering rule as the Python app).
library;

import 'package:sqflite/sqflite.dart';

import '../models/entry.dart';

class LocalEntryRepository {
  final Database _db;

  const LocalEntryRepository(this._db);

  static Future<Database> open(String path) {
    return openDatabase(
      path,
      version: 1,
      onCreate: (db, version) => db.execute('''
        CREATE TABLE entries (
          uuid TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          title TEXT NOT NULL,
          original_title TEXT,
          status TEXT NOT NULL,
          rating INTEGER,
          rating_other INTEGER,
          year INTEGER,
          url TEXT,
          open_count INTEGER NOT NULL DEFAULT 0,
          description TEXT,
          comment TEXT,
          is_favorite INTEGER NOT NULL DEFAULT 0,
          season INTEGER,
          episode INTEGER,
          last_watched_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          catalog_updated_at TEXT NOT NULL,
          deleted_at TEXT
        )
      '''),
    );
  }

  // TODO(Phase C): listAll/search/create/update/delete + upsert-from-sync,
  // following the same shape as EntryRepository in
  // core/repositories/entry_repository.py. Not implemented in this skeleton.
}
