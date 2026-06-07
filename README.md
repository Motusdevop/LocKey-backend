# LocKey

LocKey - MVP системы доступа к забронированным комнатам и студиям через умный замок.

В репозитории лежат backend на FastAPI и прошивка ESP32. Текущий фокус - online-сценарий: замок держит WebSocket-соединение с backend, показывает короткий динамический код/QR, мобильное приложение отправляет код на backend, а backend после проверки бронирования отправляет замку команду `open`.

## Текущий сценарий

1. CRM или тестовый клиент запрашивает у backend `access_code` для окна бронирования.
2. ESP32 подключается к backend по WebSocket и получает обновляемый `lock_code`.
3. Замок показывает код и QR-ссылку на экране.
4. Мобильное приложение сканирует код и вызывает `POST /api/v1/locks/{lock_id}/verify-access`.
5. Backend проверяет `access_code`, окно бронирования и `lock_code`.
6. Если замок online, backend отправляет ESP32 команду `open`.

## Структура

| Путь | Назначение |
| --- | --- |
| `backend/` | FastAPI-приложение, сервисы, схемы, тесты, Dockerfile |
| `IoT/lock_ws_client/` | Arduino-прошивка ESP32 для WebSocket, QR-дисплея и реле |
| `docs/rest-api-mobile.md` | REST API контракт для мобильного приложения |
| `BOOKING_ACCESS_SPEC.md` | Продуктовые заметки по доступу через бронирования |
| `docker-compose.yml` | Локальный стек PostgreSQL + backend |

## Уже реализовано

- Health check backend и базы данных.
- Endpoint для выдачи детерминированного `access_code` под бронирование.
- Проверка окна бронирования с буфером раннего входа 5 минут.
- Генерация и проверка динамического кода замка.
- WebSocket-подключение ESP32 к backend.
- REST-команда открытия online-замка.
- Debug HTML-страница для ручной проверки доступа.
- ESP32-прошивка для Wi-Fi, WebSocket, QR и управления реле.

## Пока не реализовано

- User/JWT авторизация мобильного приложения.
- Постоянное хранение бронирований и поиск бронирования по `access_code`.
- CRM webhooks и обратные CRM-уведомления после входа.
- Аудит попыток доступа.
- Offline/BLE fallback tickets.
- Исходный код мобильного приложения.

## Быстрый старт через Docker

Нужны Docker и Docker Compose.

```bash
docker compose up --build
```

Локальные URL:

- Backend API: `http://localhost:8000/api/v1`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`
- Debug tester: `http://localhost:8000/api/v1/debug/access-tester`

## Backend Development

Нужны Python 3.12 и `uv`.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Тесты:

```bash
cd backend
uv run pytest
```

Конфигурация читается из переменных окружения с префиксом `LOCKEY_` или из `backend/.env`.

| Переменная | Значение по умолчанию | Назначение |
| --- | --- | --- |
| `LOCKEY_API_PREFIX` | `/api/v1` | Префикс REST и WebSocket API |
| `LOCKEY_QR_SECRET` | `change-me-in-production` | HMAC-секрет для динамических кодов замка |
| `LOCKEY_QR_STEP_SECONDS` | `20` | Интервал обновления кода замка |
| `LOCKEY_QR_ALLOWED_DRIFT_STEPS` | `1` | Допустимое окно предыдущего/следующего кода |
| `LOCKEY_EXTERNAL_CRM_CODE_SECRET` | `change-me-external-crm-secret` | HMAC-секрет для кодов бронирования |
| `LOCKEY_BOOKING_EARLY_ACCESS_BUFFER_MINUTES` | `5` | Буфер раннего входа до начала бронирования |
| Backend timezone | `MSK / UTC+03:00` | Naive datetime значения трактуются как московское время |
| `LOCKEY_DB_HOST` | `postgres` | PostgreSQL host |
| `LOCKEY_DB_PORT` | `5432` | PostgreSQL port |
| `LOCKEY_DB_NAME` | `lockey` | PostgreSQL database |
| `LOCKEY_DB_USER` | `lockey` | PostgreSQL user |
| `LOCKEY_DB_PASSWORD` | `lockey` | PostgreSQL password |

## Основные API endpoints

| Method | Path | Назначение |
| --- | --- | --- |
| `GET` | `/api/v1/health` | Health check backend и БД |
| `POST` | `/api/v1/external-crm/access-code` | Выдача `access_code` и deep link для бронирования |
| `POST` | `/api/v1/locks/{lock_id}/verify-access` | Проверка мобильного запроса и открытие замка |
| `POST` | `/api/v1/locks/{lock_id}/open` | Прямая test/admin команда открытия |
| `WS` | `/api/v1/ws/locks/{lock_id}` | WebSocket-соединение ESP32 |

Подробный контракт для мобильного приложения: `docs/rest-api-mobile.md`.

## ESP32 Firmware

Прошивка находится в `IoT/lock_ws_client/` и рассчитана на Arduino-compatible ESP32 tooling.

Нужные библиотеки:

- `ArduinoJson`
- `ArduinoWebsockets`
- `TFT_eSPI`
- `qrcode`

Локальные секреты прошивки должны лежать в `IoT/lock_ws_client/config_private.h`. Этот файл игнорируется git. Шаблон: `IoT/lock_ws_client/config_private.example.h`.

Важные параметры прошивки:

- `LOCKEY_WIFI_SSID` и `LOCKEY_WIFI_PASS` для Wi-Fi.
- `LOCKEY_BACKEND_HOST` без протокола, например `localhost` или `example.com/LocKey`.
- `LOCKEY_BACKEND_PORT` для WebSocket-соединения.
- `LOCKEY_LOCK_ID`, который должен совпадать с идентификатором замка в backend.
- `LOCKEY_LOCK_PUBLIC_BASE_URL` для QR-ссылок на экране замка.

## Security Notes

- Не коммитьте `.env`, `config_private.h`, Wi-Fi credentials, API keys и production secrets.
- Замените backend-секреты по умолчанию перед использованием вне локальной разработки.
- Если реальные credentials уже попадали в git, их нужно ротировать: удаление из текущего дерева не удаляет их из истории git.

## Документация

- `docs/rest-api-mobile.md` описывает текущий REST-контракт для мобильного приложения.
- `BOOKING_ACCESS_SPEC.md` хранит продуктовые заметки и решения по доступу через бронирования.
