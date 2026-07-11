/// HTTP client for the MediaVault sync server (see ../../../sync-server).
/// Mirrors desktop's core/services/sync_service.py: bidirectional push/pull
/// of a shared catalog (Title) and this person's own state (UserState),
/// each with independent last-write-wins conflict resolution by
/// `updated_at`. Only an admin device may push a catalog deletion - the
/// server enforces this too, but the client avoids even trying, same as
/// the desktop client.
///
/// NOT verified end-to-end from this codebase (no Flutter SDK was
/// available when this was written) - review against the server's actual
/// OpenAPI schema (`/docs` on a running instance) before relying on it.
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/entry.dart';
import '../models/title_sync.dart';
import '../models/user_state_sync.dart';

const String adminRole = 'admin';

class RegisteredDevice {
  final String token;
  final String role; // "admin" | "participant"

  const RegisteredDevice({required this.token, required this.role});
}

class SyncClient {
  final String baseUrl;
  final String deviceToken;

  const SyncClient({required this.baseUrl, required this.deviceToken});

  /// Pairs this installation with the server. `key` is either the admin key
  /// (always resolves to the single admin Person) or a participant key
  /// (finds-or-creates a Person by `personName`).
  static Future<RegisteredDevice> registerDevice({
    required String baseUrl,
    required String key,
    required String personName,
    required String label,
  }) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/devices/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'key': key, 'person_name': personName, 'label': label}),
    );
    if (resp.statusCode != 200) {
      throw Exception('Device registration failed: ${resp.statusCode} ${resp.body}');
    }
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    return RegisteredDevice(
      token: body['token'] as String,
      role: body['role'] as String,
    );
  }

  Map<String, String> get _authHeaders => {
        'Authorization': 'Bearer $deviceToken',
        'Content-Type': 'application/json',
      };

  /// Splits each entry into its Title/UserState halves and pushes both.
  /// A participant's local delete never even attempts to push the Title
  /// deletion - there's nothing else to push either, so that entry is
  /// skipped entirely (the server would reject it anyway).
  Future<void> push(List<Entry> entries, {required String role}) async {
    final titles = <Map<String, dynamic>>[];
    final states = <Map<String, dynamic>>[];
    for (final entry in entries) {
      if (entry.deletedAt != null && role != adminRole) {
        continue;
      }
      titles.add(entry.toTitleSync().toJson());
      states.add(entry.toUserStateSync().toJson());
    }
    if (titles.isEmpty && states.isEmpty) {
      return;
    }
    final resp = await http.post(
      Uri.parse('$baseUrl/sync/push'),
      headers: _authHeaders,
      body: jsonEncode({'titles': titles, 'states': states}),
    );
    if (resp.statusCode != 200) {
      throw Exception('Push failed: ${resp.statusCode} ${resp.body}');
    }
  }

  /// Returns the changed titles/states since `since`. `states` only ever
  /// contains this device's own person - the server never sends anyone
  /// else's status/rating/favorite/progress.
  Future<({List<TitleSync> titles, List<UserStateSync> states})> pull(
    DateTime since,
  ) async {
    final uri = Uri.parse('$baseUrl/sync/pull')
        .replace(queryParameters: {'since': since.toIso8601String()});
    final resp = await http.get(uri, headers: _authHeaders);
    if (resp.statusCode != 200) {
      throw Exception('Pull failed: ${resp.statusCode} ${resp.body}');
    }
    final body = jsonDecode(resp.body) as Map<String, dynamic>;
    final titles = (body['titles'] as List<dynamic>)
        .map((t) => TitleSync.fromJson(t as Map<String, dynamic>))
        .toList();
    final states = (body['states'] as List<dynamic>)
        .map((s) => UserStateSync.fromJson(s as Map<String, dynamic>))
        .toList();
    return (titles: titles, states: states);
  }
}
