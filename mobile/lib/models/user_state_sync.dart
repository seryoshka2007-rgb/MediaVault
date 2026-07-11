/// Wire format for the personal half of the sync protocol - mirrors
/// `sync_server.schemas.UserStateSync` / desktop's
/// `core.schemas.UserStateSyncData`. No `person_id` of its own: the server
/// always attributes this to the authenticated device's Person - a client
/// can never claim to push someone else's state.
library;

class UserStateSync {
  final String titleUuid;
  final String status; // planned | watching | paused | completed | dropped
  final int? rating;
  final int? ratingOther;
  final bool isFavorite;
  final int? season;
  final int? episode;
  final int openCount;
  final DateTime? lastWatchedAt;
  final String? comment;
  final DateTime updatedAt;

  const UserStateSync({
    required this.titleUuid,
    required this.status,
    required this.updatedAt,
    this.rating,
    this.ratingOther,
    this.isFavorite = false,
    this.season,
    this.episode,
    this.openCount = 0,
    this.lastWatchedAt,
    this.comment,
  });

  factory UserStateSync.fromJson(Map<String, dynamic> json) => UserStateSync(
        titleUuid: json['title_uuid'] as String,
        status: json['status'] as String,
        rating: json['rating'] as int?,
        ratingOther: json['rating_other'] as int?,
        isFavorite: (json['is_favorite'] as bool?) ?? false,
        season: json['season'] as int?,
        episode: json['episode'] as int?,
        openCount: (json['open_count'] as int?) ?? 0,
        lastWatchedAt: json['last_watched_at'] == null
            ? null
            : DateTime.parse(json['last_watched_at'] as String),
        comment: json['comment'] as String?,
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'title_uuid': titleUuid,
        'status': status,
        'rating': rating,
        'rating_other': ratingOther,
        'is_favorite': isFavorite,
        'season': season,
        'episode': episode,
        'open_count': openCount,
        'last_watched_at': lastWatchedAt?.toIso8601String(),
        'comment': comment,
        'updated_at': updatedAt.toIso8601String(),
      };
}
