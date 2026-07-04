# MediaVault Mobile (iOS + Android, Flutter)

**Статус: скелет, НЕ собран и НЕ проверен.** Написан текстом по знанию формата
Flutter/Dart на машине без Flutter SDK, Xcode или Android SDK — здесь физически
нельзя было выполнить `flutter create`/`flutter run`/`flutter analyze`. Прежде
чем считать это рабочим кодом, нужно на машине с Flutter SDK:

```
flutter create --project-name mediavault_mobile .   # если pubspec.yaml конфликтует — сверить руками
flutter pub get
flutter analyze
flutter run
```

Возможны мелкие несостыковки версий пакетов (`http`/`sqflite`/`uuid`/
`flutter_lints` в `pubspec.yaml`) — подобраны по последним известным мне
мажорным версиям, но не проверены `pub get` вживую.

## Архитектура

Тот же принцип и контракт данных, что у desktop-приложения (`../core/`),
но не общий код — PySide6/Qt не поддерживает iOS. Полная схема — в
[`../docs/MULTIPLATFORM.md`](../docs/MULTIPLATFORM.md).

- `lib/models/entry.dart` — зеркалит `EntrySync` из `../sync-server` /
  `EntryRead` из `../core/schemas.py`. Те же имена полей, чтобы поведение
  совпадало на всех платформах, даже если код не общий.
- `lib/services/local_db.dart` — **не реализовано** (только `CREATE TABLE` +
  TODO). Должно стать аналогом `core/repositories/entry_repository.py`:
  единственное место, которое трогает локальную sqflite-БД. Экраны не должны
  ходить в БД напрямую — то же правило слоёв, что в desktop-приложении.
- `lib/services/sync_client.dart` — HTTP-клиент к `../sync-server`
  (push/pull, per-device токен). Написан по протоколу из
  `docs/MULTIPLATFORM.md`, не проверен реальным вызовом.
- `lib/screens/library_screen.dart` — заглушка экрана списка.

## Что предстоит сделать (Phase C, не в этой сессии)
1. Проверить, что скелет вообще собирается (`flutter analyze`/`flutter run`)
   на машине с Flutter SDK — это первый шаг, до всего остального.
2. Реализовать `LocalEntryRepository` (CRUD + upsert из sync).
3. Экраны: список/поиск, добавление/редактирование (аналог
   `app/dialogs/entry_dialog.py`), просмотр по ссылке.
4. Подключить `SyncClient` к реальному потоку: push локальных изменений,
   pull с сервера, применение по `updated_at`.
5. Для iOS: сборка/подпись/публикация требуют физического Mac с Xcode —
   отдельная задача, недоступная с этой машины.
