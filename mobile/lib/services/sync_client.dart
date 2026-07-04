/// HTTP client for the MediaVault sync server (see ../../../sync-server).
/// NOT verified end-to-end from this codebase (no Flutter SDK available in
/// the environment this was written in) - review against the server's
/// actual OpenAPI schema (`/docs` on a running instance) before relying on it.
library;

import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/entry.dart';

class SyncClient {
  final String baseUrl;
  final String deviceToken;

  const SyncClient({required this.baseUrl, required this.deviceToken});

  static Future<String> registerDevice({
    required String baseUrl,
    required String setupKey,
    required String label,
  }) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/devices/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'setup_key': setupKey, 'label': label}),
    );
    if (resp.statusCode != 200) {
      throw Exception('Device registration failed: ${resp.statusCode} ${resp.body}');
    }
    return jsonDecode(resp.body)['token'] as String;
  }

  Map<String, String> get _authHeaders => {
        'Authorization': 'Bearer $deviceToken',
        'Content-Type': 'application/json',
      };

  /// Returns which uuids the server actually applied (rejected ones lost a
  /// last-write-wins conflict and should be re-pulled, not re-pushed).
  Future<Map<String, bool>> push(List<Entry> entries) async {
    final resp = await http.post(
      Uri.parse('$baseUrl/sync/push'),
      headers: _authHeaders,
      body: jsonEncode({'entries': entries.map((e) => e.toJson()).toList()}),
    );
    if (resp.statusCode != 200) {
      throw Exception('Push failed: ${resp.statusCode} ${resp.body}');
    }
    final results = jsonDecode(resp.body)['results'] as List<dynamic>;
    return {
      for (final r in results) r['uuid'] as String: r['applied'] as bool,
    };
  }

  Future<List<Entry>> pull(DateTime since) async {
    final uri = Uri.parse('$baseUrl/sync/pull')
        .replace(queryParameters: {'since': since.toIso8601String()});
    final resp = await http.get(uri, headers: _authHeaders);
    if (resp.statusCode != 200) {
      throw Exception('Pull failed: ${resp.statusCode} ${resp.body}');
    }
    final entries = jsonDecode(resp.body)['entries'] as List<dynamic>;
    return entries.map((e) => Entry.fromJson(e as Map<String, dynamic>)).toList();
  }
}
