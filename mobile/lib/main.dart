import 'package:flutter/material.dart';

import 'screens/library_screen.dart';

void main() {
  runApp(const MediaVaultApp());
}

class MediaVaultApp extends StatelessWidget {
  const MediaVaultApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MediaVault',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.deepPurple,
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const LibraryScreen(),
    );
  }
}
