# MediaVault Sync Server

Лёгкий self-hosted сервис синхронизации библиотеки MediaVault между
устройствами (desktop + будущий Flutter mobile). Личный однопользовательский
сервис, не multi-tenant SaaS. Полная архитектура и протокол — в
[`../docs/MULTIPLATFORM.md`](../docs/MULTIPLATFORM.md).

Пока **не подключён** ни к desktop-приложению, ни к mobile — это отдельный,
самостоятельно тестируемый сервис (Phase A), интеграция — Phase B/C.

## Установка

```
py -3.13 -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
```

## Запуск

Обязательно задать `MEDIAVAULT_SYNC_SETUP_KEY` — общий секрет для привязки
нового устройства (без него сервер откажется обслуживать `/devices/register`):

```
set MEDIAVAULT_SYNC_SETUP_KEY=<ваш-секрет>
.venv\Scripts\uvicorn sync_server.main:create_app --factory --host 0.0.0.0 --port 8000
```

БД по умолчанию — `sync.db` рядом с точкой запуска; путь переопределяется
через `MEDIAVAULT_SYNC_DB`.

## Проверка

```
.venv\Scripts\pytest
.venv\Scripts\ruff check .
.venv\Scripts\mypy .
```

## Перед реальным разворачиванием в сеть
Сейчас это только протестированный локально скелет. Перед тем как открывать
порт наружу (даже в домашней сети):
- поставить за reverse-proxy с TLS (сам сервис по HTTP, без шифрования);
- продумать отзыв/ротацию токенов устройств (сейчас только выпуск, отзыва нет);
- ограничить частоту запросов к `/devices/register` (сейчас не ограничена).
