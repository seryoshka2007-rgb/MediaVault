"""Minimal dictionary-based i18n for the GUI layer.

No Qt `.ts`/`.qm` build pipeline - a plain nested dict, in the same spirit
as the project's pre-existing `STATUS_LABELS_RU`-style label dicts, just
extended to more than one language. Language switch takes effect after an
app restart (same pattern as the settings screen's path fields) - widgets
are built once at startup, not re-labeled live.

Default language is "ru", matching `Settings.language`'s default, so any
code that never calls `set_language()` (e.g. existing tests) behaves
exactly as before this module existed.
"""
from __future__ import annotations

from core.enums import EntryType, SortOption, Status

Language = str  # "ru" | "en" | "uk" - a presentation setting, not a domain enum

SUPPORTED_LANGUAGES: tuple[Language, ...] = ("ru", "en", "uk")

LANGUAGE_LABELS: dict[Language, str] = {
    "ru": "Русский",
    "en": "English",
    "uk": "Українська",
}

_current: Language = "ru"


def set_language(language: Language) -> None:
    global _current
    _current = language if language in SUPPORTED_LANGUAGES else "ru"


def current_language() -> Language:
    return _current


_STRINGS: dict[str, dict[Language, str]] = {
    "search_placeholder": {"ru": "Поиск…", "en": "Search…", "uk": "Пошук…"},
    "add": {"ru": "Добавить", "en": "Add", "uk": "Додати"},
    "watch": {"ru": "Смотреть", "en": "Watch", "uk": "Дивитися"},
    "edit": {"ru": "Изменить", "en": "Edit", "uk": "Змінити"},
    "delete": {"ru": "Удалить", "en": "Delete", "uk": "Видалити"},
    "sync": {"ru": "Синхронизировать", "en": "Synchronize", "uk": "Синхронізувати"},
    "participants": {"ru": "Участники", "en": "Participants", "uk": "Учасники"},
    "settings": {"ru": "Настройки", "en": "Settings", "uk": "Налаштування"},
    "backups": {"ru": "Бэкапы", "en": "Backups", "uk": "Резервні копії"},
    "all_types": {"ru": "Все типы", "en": "All types", "uk": "Усі типи"},
    "all_statuses": {"ru": "Все статусы", "en": "All statuses", "uk": "Усі статуси"},
    "favorite": {"ru": "Избранное", "en": "Favorite", "uk": "Обране"},
    "apply_status_to_selected": {
        "ru": "Применить статус к выбранным",
        "en": "Apply status to selected",
        "uk": "Застосувати статус до вибраних",
    },
    "add_entry_msgbox_title": {
        "ru": "Добавление записи", "en": "Add entry", "uk": "Додавання запису",
    },
    "how_to_add": {
        "ru": "Как добавить запись?", "en": "How would you like to add it?",
        "uk": "Як додати запис?",
    },
    "by_link": {"ru": "По ссылке", "en": "By link", "uk": "За посиланням"},
    "manually": {"ru": "Вручную", "en": "Manually", "uk": "Вручну"},
    "cancel": {"ru": "Отмена", "en": "Cancel", "uk": "Скасувати"},
    "add_by_link_title": {
        "ru": "Добавить по ссылке", "en": "Add by link", "uk": "Додати за посиланням",
    },
    "paste_link": {
        "ru": "Вставьте ссылку:", "en": "Paste the link:", "uk": "Вставте посилання:",
    },
    "validation_title": {"ru": "Проверка", "en": "Validation", "uk": "Перевірка"},
    "invalid_url": {
        "ru": "Ссылка выглядит некорректно.",
        "en": "The link doesn't look valid.",
        "uk": "Посилання виглядає некоректним.",
    },
    "already_in_library_title": {
        "ru": "Уже есть в библиотеке", "en": "Already in library",
        "uk": "Вже є в бібліотеці",
    },
    "already_added": {
        "ru": "Уже добавлено: {title}", "en": "Already added: {title}",
        "uk": "Вже додано: {title}",
    },
    "no_link_title": {"ru": "Нет ссылки", "en": "No link", "uk": "Немає посилання"},
    "no_valid_link": {
        "ru": "У этой записи нет корректной ссылки.",
        "en": "This entry doesn't have a valid link.",
        "uk": "У цього запису немає коректного посилання.",
    },
    "confirm_delete_one": {
        "ru": "Удалить «{title}»?", "en": "Delete “{title}”?",
        "uk": "Видалити «{title}»?",
    },
    "confirm_delete_many": {
        "ru": "Удалить выбранные записи ({count} шт.)?",
        "en": "Delete the selected entries ({count})?",
        "uk": "Видалити вибрані записи ({count} шт.)?",
    },
    "delete_entry_title": {"ru": "Удалить запись", "en": "Delete entry", "uk": "Видалити запис"},
    "no_selection_title": {
        "ru": "Нет выбора", "en": "Nothing selected", "uk": "Нічого не вибрано",
    },
    "select_one_or_more": {
        "ru": "Выберите одну или несколько записей в списке.",
        "en": "Select one or more entries in the list.",
        "uk": "Виберіть один або декілька записів у списку.",
    },
    "sync_title": {"ru": "Синхронизация", "en": "Synchronization", "uk": "Синхронізація"},
    "server_address_prompt": {
        "ru": "Адрес сервера (например http://100.x.x.x:8000):",
        "en": "Server address (e.g. http://100.x.x.x:8000):",
        "uk": "Адреса сервера (наприклад http://100.x.x.x:8000):",
    },
    "key_prompt": {
        "ru": "Ключ (admin key — ваш, или ключ участника):",
        "en": "Key (your admin key, or a participant key):",
        "uk": "Ключ (ваш admin-ключ або ключ учасника):",
    },
    "your_name_prompt": {
        "ru": "Ваше имя (для общего сервера с другими людьми):",
        "en": "Your name (for a server shared with other people):",
        "uk": "Ваше ім'я (для спільного сервера з іншими людьми):",
    },
    "device_label_prompt": {
        "ru": "Название этого устройства:", "en": "This device's name:",
        "uk": "Назва цього пристрою:",
    },
    "registration_error_title": {
        "ru": "Ошибка регистрации", "en": "Registration error", "uk": "Помилка реєстрації",
    },
    "syncing_ellipsis": {
        "ru": "Синхронизация…", "en": "Synchronizing…", "uk": "Синхронізація…",
    },
    "sync_complete_title": {
        "ru": "Синхронизация завершена", "en": "Sync complete", "uk": "Синхронізацію завершено",
    },
    "sync_complete_body": {
        "ru": "Отправлено: {pushed}\nПолучено: {pulled}",
        "en": "Sent: {pushed}\nReceived: {pulled}",
        "uk": "Надіслано: {pushed}\nОтримано: {pulled}",
    },
    "sync_error_title": {
        "ru": "Ошибка синхронизации", "en": "Sync error", "uk": "Помилка синхронізації",
    },
    "other_pc_rating": {
        "ru": "др.ПК: {rating}", "en": "other PC: {rating}", "uk": "ін.ПК: {rating}",
    },
    "edit_entry_title": {"ru": "Изменить запись", "en": "Edit entry", "uk": "Змінити запис"},
    "add_entry_dialog_title": {"ru": "Добавить запись", "en": "Add entry", "uk": "Додати запис"},
    "title_field": {"ru": "Название*", "en": "Title*", "uk": "Назва*"},
    "original_title_field": {
        "ru": "Оригинальное название", "en": "Original title", "uk": "Оригінальна назва",
    },
    "type_field": {"ru": "Тип", "en": "Type", "uk": "Тип"},
    "url_field": {"ru": "Ссылка", "en": "Link", "uk": "Посилання"},
    "status_field": {"ru": "Статус", "en": "Status", "uk": "Статус"},
    "year_field": {"ru": "Год выпуска", "en": "Release year", "uk": "Рік випуску"},
    "my_rating_field": {"ru": "Моя оценка", "en": "My rating", "uk": "Моя оцінка"},
    "other_rating_field": {
        "ru": "Оценка (др. ПК)", "en": "Rating (other PC)", "uk": "Оцінка (ін. ПК)",
    },
    "season_field": {"ru": "Сезон", "en": "Season", "uk": "Сезон"},
    "episode_field": {"ru": "Серия", "en": "Episode", "uk": "Серія"},
    "description_field": {"ru": "Описание", "en": "Description", "uk": "Опис"},
    "comment_field": {"ru": "Комментарий", "en": "Comment", "uk": "Коментар"},
    "title_required": {
        "ru": "Название не может быть пустым.", "en": "Title can't be empty.",
        "uk": "Назва не може бути порожньою.",
    },
    "theme_field": {"ru": "Тема", "en": "Theme", "uk": "Тема"},
    "language_field": {"ru": "Язык", "en": "Language", "uk": "Мова"},
    "backup_keep_field": {
        "ru": "Хранить резервных копий (шт.)", "en": "Backups to keep",
        "uk": "Зберігати резервних копій (шт.)",
    },
    "autobackup_daily_field": {
        "ru": "Ежедневный автоматический бэкап", "en": "Automatic daily backup",
        "uk": "Щоденний автоматичний бекап",
    },
    "db_path_field": {
        "ru": "Путь к базе данных", "en": "Database path", "uk": "Шлях до бази даних",
    },
    "backups_dir_field": {
        "ru": "Папка резервных копий", "en": "Backups folder", "uk": "Папка резервних копій",
    },
    "logs_dir_field": {"ru": "Папка логов", "en": "Logs folder", "uk": "Папка логів"},
    "settings_restart_note": {
        "ru": "Путь к базе данных, папки резервных копий/логов и язык "
        "применяются после перезапуска приложения.",
        "en": "The database path, backups/logs folders, and language take "
        "effect after restarting the app.",
        "uk": "Шлях до бази даних, папки резервних копій/логів та мова "
        "застосовуються після перезапуску застосунку.",
    },
    "revoke_device_button": {
        "ru": "Отозвать токен устройства", "en": "Revoke device token",
        "uk": "Відкликати токен пристрою",
    },
    "error_title": {"ru": "Ошибка", "en": "Error", "uk": "Помилка"},
    "selection_title": {"ru": "Выбор", "en": "Selection", "uk": "Вибір"},
    "select_device_not_header": {
        "ru": "Выберите устройство (не строку с именем).",
        "en": "Select a device (not a person's name row).",
        "uk": "Виберіть пристрій (не рядок з іменем).",
    },
    "revoke_token_title": {
        "ru": "Отозвать токен", "en": "Revoke token", "uk": "Відкликати токен",
    },
    "confirm_revoke": {
        "ru": "Отозвать токен «{label}»?", "en": "Revoke the token for “{label}”?",
        "uk": "Відкликати токен «{label}»?",
    },
    "backups_window_title": {
        "ru": "Резервные копии", "en": "Backups", "uk": "Резервні копії",
    },
    "create_now_button": {"ru": "Создать сейчас", "en": "Create now", "uk": "Створити зараз"},
    "restore_selected_button": {
        "ru": "Восстановить выбранную", "en": "Restore selected", "uk": "Відновити вибрану",
    },
    "done_title": {"ru": "Готово", "en": "Done", "uk": "Готово"},
    "backup_created_message": {
        "ru": "Резервная копия создана.", "en": "Backup created.",
        "uk": "Резервну копію створено.",
    },
    "select_backup_from_list": {
        "ru": "Выберите резервную копию из списка.", "en": "Select a backup from the list.",
        "uk": "Виберіть резервну копію зі списку.",
    },
    "restore_title": {"ru": "Восстановить", "en": "Restore", "uk": "Відновити"},
    "confirm_restore_body": {
        "ru": "Текущие данные будут заменены выбранной резервной копией "
        "(текущее состояние тоже сохранится в отдельный бэкап перед этим).\n"
        "Изменения вступят в силу после перезапуска приложения. Продолжить?",
        "en": "The current data will be replaced with the selected backup "
        "(the current state will also be saved as a backup first).\n"
        "The change takes effect after restarting the app. Continue?",
        "uk": "Поточні дані буде замінено вибраною резервною копією (поточний "
        "стан теж буде збережено в окремий бекап перед цим).\n"
        "Зміни набудуть чинності після перезапуску застосунку. Продовжити?",
    },
    "restored_title": {"ru": "Восстановлено", "en": "Restored", "uk": "Відновлено"},
    "restored_message": {
        "ru": "Готово. Перезапустите приложение, чтобы увидеть восстановленные данные.",
        "en": "Done. Restart the app to see the restored data.",
        "uk": "Готово. Перезапустіть застосунок, щоб побачити відновлені дані.",
    },
}


def t(key: str, **kwargs: object) -> str:
    entry = _STRINGS[key]
    text = entry.get(_current, entry["ru"])
    return text.format(**kwargs) if kwargs else text


_STATUS_LABELS: dict[Status, dict[Language, str]] = {
    Status.PLANNED: {"ru": "Хочу посмотреть", "en": "Want to watch", "uk": "Хочу подивитися"},
    Status.WATCHING: {"ru": "Смотрю", "en": "Watching", "uk": "Дивлюся"},
    Status.PAUSED: {"ru": "На паузе", "en": "Paused", "uk": "На паузі"},
    Status.COMPLETED: {"ru": "Просмотрено", "en": "Completed", "uk": "Переглянуто"},
    Status.DROPPED: {"ru": "Заброшено", "en": "Dropped", "uk": "Покинуто"},
}

_ENTRY_TYPE_LABELS: dict[EntryType, dict[Language, str]] = {
    EntryType.MOVIE: {"ru": "Фильм", "en": "Movie", "uk": "Фільм"},
    EntryType.SERIES: {"ru": "Сериал", "en": "TV Series", "uk": "Серіал"},
}

_SORT_LABELS: dict[SortOption, dict[Language, str]] = {
    SortOption.UPDATED_DESC: {
        "ru": "Дата изменения", "en": "Date modified", "uk": "Дата зміни",
    },
    SortOption.TITLE_ASC: {
        "ru": "Название (А-Я)", "en": "Title (A-Z)", "uk": "Назва (А-Я)",
    },
    SortOption.YEAR_DESC: {"ru": "Год", "en": "Year", "uk": "Рік"},
    SortOption.RATING_DESC: {"ru": "Оценка", "en": "Rating", "uk": "Оцінка"},
}


def status_label(status: Status) -> str:
    entry = _STATUS_LABELS[status]
    return entry.get(_current, entry["ru"])


def entry_type_label(entry_type: EntryType) -> str:
    entry = _ENTRY_TYPE_LABELS[entry_type]
    return entry.get(_current, entry["ru"])


def sort_label(option: SortOption) -> str:
    entry = _SORT_LABELS[option]
    return entry.get(_current, entry["ru"])
