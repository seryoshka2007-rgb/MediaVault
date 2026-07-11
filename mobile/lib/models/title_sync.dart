/// Wire format for the shared-catalog half of the sync protocol - mirrors
/// `sync_server.schemas.TitleSync` / desktop's `core.schemas.TitleSyncData`.
/// No personal fields here (see UserStateSync) - catalog data is the same
/// for everyone on the server, unlike status/rating/favorite/...
library;

class TitleSync {
  final String uuid;
  final String type; // "movie" | "series"
  final String title;
  final String? originalTitle;
  final int? year;
  final String? url;
  final String? description;
  final DateTime createdAt;
  final DateTime updatedAt;
  final DateTime? deletedAt;

  const TitleSync({
    required this.uuid,
    required this.type,
    required this.title,
    required this.createdAt,
    required this.updatedAt,
    this.originalTitle,
    this.year,
    this.url,
    this.description,
    this.deletedAt,
  });

  factory TitleSync.fromJson(Map<String, dynamic> json) => TitleSync(
        uuid: json['uuid'] as String,
        type: json['type'] as String,
        title: json['title'] as String,
        originalTitle: json['original_title'] as String?,
        year: json['year'] as int?,
        url: json['url'] as String?,
        description: json['description'] as String?,
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
        'year': year,
        'url': url,
        'description': description,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
        'deleted_at': deletedAt?.toIso8601String(),
      };
}
