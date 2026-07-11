/// Local on-device row - one entry, catalog + personal fields together
/// (same as the desktop app's single `Entry` table: the Title/UserState
/// split is a *sync-wire-protocol* concern only, see title_sync.dart /
/// user_state_sync.dart, not a local storage concern - mirrors
/// `core/models/entry.py` + `core/schemas.EntryRead`).
library;

import 'title_sync.dart';
import 'user_state_sync.dart';

class Entry {
  final String uuid;
  final String type; // "movie" | "series"
  final String title;
  final String? originalTitle;
  final String status; // planned | watching | paused | completed | dropped
  final int? rating;
  final int? ratingOther;
  final int? year;
  final String? url;
  final int openCount;
  final String? description;
  final String? comment;
  final bool isFavorite;
  final int? season;
  final int? episode;
  final DateTime? lastWatchedAt;
  final DateTime createdAt;
  final DateTime updatedAt;
  // Bumped only when a catalog field changes (title/original_title/year/
  // url/description) - NOT on every personal-field edit. Same reasoning as
  // `Entry.catalog_updated_at` on the desktop side: without this split, an
  // edit to just your own rating/status would look like a catalog edit to
  // the sync protocol and could wrongly clobber someone else's newer title
  // edit. See core/models/entry.py for the full explanation.
  final DateTime catalogUpdatedAt;
  final DateTime? deletedAt;

  const Entry({
    required this.uuid,
    required this.type,
    required this.title,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    required this.catalogUpdatedAt,
    this.originalTitle,
    this.rating,
    this.ratingOther,
    this.year,
    this.url,
    this.openCount = 0,
    this.description,
    this.comment,
    this.isFavorite = false,
    this.season,
    this.episode,
    this.lastWatchedAt,
    this.deletedAt,
  });

  /// The catalog half of this row, as sent to POST /sync/push.
  TitleSync toTitleSync() => TitleSync(
        uuid: uuid,
        type: type,
        title: title,
        originalTitle: originalTitle,
        year: year,
        url: url,
        description: description,
        createdAt: createdAt,
        updatedAt: catalogUpdatedAt,
        deletedAt: deletedAt,
      );

  /// The personal half of this row, as sent to POST /sync/push. The server
  /// always derives person_id from the authenticated device - never sent
  /// here, same as desktop's UserStateSyncData.
  UserStateSync toUserStateSync() => UserStateSync(
        titleUuid: uuid,
        status: status,
        rating: rating,
        ratingOther: ratingOther,
        isFavorite: isFavorite,
        season: season,
        episode: episode,
        openCount: openCount,
        lastWatchedAt: lastWatchedAt,
        comment: comment,
        updatedAt: updatedAt,
      );

  factory Entry.fromJson(Map<String, dynamic> json) => Entry(
        uuid: json['uuid'] as String,
        type: json['type'] as String,
        title: json['title'] as String,
        originalTitle: json['original_title'] as String?,
        status: json['status'] as String,
        rating: json['rating'] as int?,
        ratingOther: json['rating_other'] as int?,
        year: json['year'] as int?,
        url: json['url'] as String?,
        openCount: (json['open_count'] as int?) ?? 0,
        description: json['description'] as String?,
        comment: json['comment'] as String?,
        isFavorite: (json['is_favorite'] as bool?) ?? false,
        season: json['season'] as int?,
        episode: json['episode'] as int?,
        lastWatchedAt: json['last_watched_at'] == null
            ? null
            : DateTime.parse(json['last_watched_at'] as String),
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
        catalogUpdatedAt: json['catalog_updated_at'] == null
            ? DateTime.parse(json['updated_at'] as String)
            : DateTime.parse(json['catalog_updated_at'] as String),
        deletedAt: json['deleted_at'] == null
            ? null
            : DateTime.parse(json['deleted_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'uuid': uuid,
        'type': type,
        'title': title,
        'original_title': originalTitle,
        'status': status,
        'rating': rating,
        'rating_other': ratingOther,
        'year': year,
        'url': url,
        'open_count': openCount,
        'description': description,
        'comment': comment,
        'is_favorite': isFavorite,
        'season': season,
        'episode': episode,
        'catalog_updated_at': catalogUpdatedAt.toIso8601String(),
        'last_watched_at': lastWatchedAt?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
        'deleted_at': deletedAt?.toIso8601String(),
      };
}
