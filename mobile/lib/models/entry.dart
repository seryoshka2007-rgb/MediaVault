/// Mirrors `sync_server.schemas.EntrySync` (see ../../../sync-server) and the
/// desktop app's `core/schemas.EntryRead` (see ../../../core/schemas.py).
/// Keeping the same field names/shapes across Python and Dart is what makes
/// "the same logic" hold even though the code itself is not shared.
library;

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
  final DateTime? deletedAt;

  const Entry({
    required this.uuid,
    required this.type,
    required this.title,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
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
        'last_watched_at': lastWatchedAt?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
        'deleted_at': deletedAt?.toIso8601String(),
      };
}
