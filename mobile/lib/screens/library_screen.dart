/// Placeholder library list screen. Phase C work: wire up to
/// LocalEntryRepository once it has real CRUD methods.
library;

import 'package:flutter/material.dart';

class LibraryScreen extends StatelessWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('MediaVault')),
      body: const Center(
        child: Text('Библиотека пуста. Экран-заглушка (Phase C).'),
      ),
    );
  }
}
