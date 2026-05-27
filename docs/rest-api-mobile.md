# LocKey REST API для мобильного приложения

Документ описывает текущий backend-контракт LocKey для мобильного разработчика. Backend написан на FastAPI, основной префикс API: `/api/v1`.

## Базовая информация

- Base URL для локальной разработки: `http://localhost:8000`
- REST API prefix: `/api/v1`
- Swagger UI FastAPI: `/docs`
- OpenAPI schema: `/openapi.json`
- Формат данных: JSON
- Формат времени: ISO 8601, желательно UTC с `Z`, например `2026-04-22T12:00:00Z`
- Авторизация в текущем MVP не реализована. `access_code` выступает временным кодом доступа для бронирования.
- Offline/BLE tickets временно отключены и не входят в текущий mobile REST flow.

## Термины

- `lock_id` - строковый идентификатор замка, например `studio-a1`.
- `access_code` - человекочитаемый код доступа к бронированию. Генерируется backend по `lock_id`, `booking_starts_at`, `booking_ends_at` и секрету CRM-интеграции.
- `lock_code` - короткий динамический код замка. Backend отправляет его на ESP32 по WebSocket, замок показывает код/QR на экране. Код действует короткое время.
- `valid_from` - момент, с которого доступ разрешен. Сейчас это `booking_starts_at - 5 минут`.
- `valid_until` - момент окончания доступа. Сейчас совпадает с `booking_ends_at`.

## Общая логика мобильного приложения

1. Пользователь получает ссылку из CRM/мессенджера после бронирования.
2. Приложение открывается по deep link и получает минимум: `lock_id`, `access_code`, `booking_starts_at`, `booking_ends_at`.
3. У двери приложение сканирует QR/код на замке и получает `lock_code`.
4. Для online-открытия приложение вызывает `POST /api/v1/locks/{lock_id}/verify-access`.
5. Backend проверяет `access_code`, окно бронирования и `lock_code`, затем отправляет команду `open` на ESP32 по WebSocket.
6. Если backend или замок недоступны, текущий MVP показывает ошибку. Offline/BLE fallback пока не реализован.

Рекомендуемый deep link для текущего MVP:

```text
lockey://open?lock_id=studio-a1&access_code=ABCDEF1234&booking_starts_at=2026-04-22T12:00:00Z&booking_ends_at=2026-04-22T14:00:00Z
```

## Endpoint Summary

| Method | Path | Для мобильного | Назначение |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | Опционально | Проверка доступности backend и БД |
| `POST` | `/api/v1/external-crm/access-code` | Обычно нет | Выпуск `access_code` для CRM/тестов |
| `POST` | `/api/v1/locks/{lock_id}/verify-access` | Да | Online-открытие замка по `access_code` + `lock_code` |
| `POST` | `/api/v1/locks/{lock_id}/open` | Нет | Прямая команда открытия, без проверки доступа |
| `WS` | `/api/v1/ws/locks/{lock_id}` | Нет | WebSocket для ESP32 |
| `GET` | `/api/v1/debug/access-tester` | Debug | HTML-страница для ручной проверки доступа |

## Health Check

Проверка состояния backend.

```http
GET /api/v1/health
```

Успешный ответ `200`:

```json
{
  "status": "ok",
  "database": "up"
}
```

Если БД недоступна, backend вернет `503`:

```json
{
  "status": "degraded",
  "database": "down"
}
```

Как использовать в мобильном приложении:

- Можно вызывать перед online-открытием, чтобы быстро понять, доступен ли backend.
- Не нужно блокировать UI только на основании health check: основной online-запрос всё равно вернет точную ошибку.

## Получение access code

Endpoint предназначен в первую очередь для внешней CRM или тестового стенда. В продуктовой логике мобильное приложение обычно получает `access_code` уже готовым через deep link.

```http
POST /api/v1/external-crm/access-code
Content-Type: application/json
```

Request:

```json
{
  "lock_id": "studio-a1",
  "booking_starts_at": "2026-04-22T12:00:00Z",
  "booking_ends_at": "2026-04-22T14:00:00Z"
}
```

Response `200`:

```json
{
  "lock_id": "studio-a1",
  "access_code": "JBSWY3DPEH",
  "access_url": "lockey://open?lock_id=studio-a1&access_code=JBSWY3DPEH&booking_starts_at=2026-04-22T12:00:00Z&booking_ends_at=2026-04-22T14:00:00Z",
  "booking_starts_at": "2026-04-22T12:00:00Z",
  "booking_ends_at": "2026-04-22T14:00:00Z",
  "valid_from": "2026-04-22T11:55:00Z",
  "valid_until": "2026-04-22T14:00:00Z"
}
```

Правила:

- `lock_id` не может быть пустым.
- `booking_ends_at` должен быть строго больше `booking_starts_at`.
- Если время приходит без timezone, backend трактует его как UTC.
- `access_code` детерминирован для одной комбинации `lock_id + booking_starts_at + booking_ends_at`.
- `access_url` соответствует формату `lockey://open?lock_id={lock_id}&access_code={access_code}&booking_starts_at={booking_starts_at}&booking_ends_at={booking_ends_at}`.

Возможные ошибки:

- `422 Unprocessable Entity` - пустой `lock_id`, некорректный формат даты или `booking_ends_at <= booking_starts_at`.

## Online-открытие замка

Основной endpoint для мобильного приложения у двери.

```http
POST /api/v1/locks/{lock_id}/verify-access
Content-Type: application/json
```

Path parameters:

| Name | Type | Description |
| --- | --- | --- |
| `lock_id` | `string` | Идентификатор замка из deep link или QR |

Request:

```json
{
  "access_code": "JBSWY3DPEH",
  "lock_code": "A1B2C3",
  "booking_starts_at": "2026-04-22T12:00:00Z",
  "booking_ends_at": "2026-04-22T14:00:00Z"
}
```

Response `202 Accepted`:

```json
{
  "status": "sent",
  "lock_id": "studio-a1",
  "command_id": "81dfcf86-6bb9-47d8-8e8c-51d03f3a3b3d"
}
```

Что делает backend:

- Проверяет, что `lock_code` актуален для указанного `lock_id`.
- Проверяет, что `access_code` соответствует `lock_id + booking_starts_at + booking_ends_at`.
- Проверяет текущее время: открыть можно с `booking_starts_at - 5 минут` до `booking_ends_at`.
- Проверяет, что замок подключен к backend по WebSocket.
- Отправляет замку сообщение `{"type":"open","command_id":"..."}`.

Как мобильному приложению получить `lock_code`:

- Считать QR-код с экрана замка.
- Либо дать пользователю ввести короткий код вручную.
- Ожидаемый размер текущего кода: `6` символов, hex uppercase, например `A1B2C3`.
- Код меняется каждые `20` секунд.
- Backend допускает drift в `1` временной шаг, то есть обычно принимает предыдущий, текущий и следующий код.

Возможные ошибки:

- `400 Bad Request` с `{"detail":"Lock code is invalid or expired"}` - QR/код устарел или относится к другому замку.
- `400 Bad Request` с `{"detail":"Access code is invalid"}` - неверный `access_code` или не совпадает окно бронирования.
- `403 Forbidden` с `{"detail":"Booking access window is closed"}` - попытка открыть слишком рано или после окончания бронирования.
- `404 Not Found` с `{"detail":"Lock is offline"}` - ESP32 не подключен к backend по WebSocket.
- `422 Unprocessable Entity` - некорректный формат запроса.

Рекомендованная обработка в UI:

- `202` - показать состояние `Открываем...`, затем `Команда отправлена`. В текущем API нет REST-подтверждения физического открытия.
- `400 Lock code` - попросить пересканировать QR/обновить код.
- `400 Access code` - показать ошибку доступа и предложить обратиться в поддержку/проверить ссылку.
- `403 Booking access window` - показать время начала/окончания бронирования.
- `404 Lock is offline` или network error - показать, что online-открытие сейчас недоступно.

## Прямая команда открытия

Этот endpoint не должен использоваться мобильным приложением в клиентском сценарии, потому что он не проверяет `access_code` и `lock_code`. Он полезен только для внутренних тестов/админских сценариев.

```http
POST /api/v1/locks/{lock_id}/open
```

Response `202 Accepted`:

```json
{
  "status": "sent",
  "lock_id": "studio-a1",
  "command_id": "81dfcf86-6bb9-47d8-8e8c-51d03f3a3b3d"
}
```

Ошибка:

- `404 Not Found` с `{"detail":"Lock is offline"}` - замок не подключен.

## WebSocket замка

Это не мобильный endpoint, но важно понимать механику online-открытия. ESP32 подключается к backend и держит соединение открытым.

```text
WS /api/v1/ws/locks/{lock_id}
```

Сообщение с динамическим кодом от backend к ESP32:

```json
{
  "type": "code",
  "value": "A1B2C3",
  "expires_at": 1776868810
}
```

Поля:

- `value` - код, который ESP32 показывает на экране и/или кодирует в QR.
- `expires_at` - Unix timestamp, когда код истекает.

Сообщение на открытие от backend к ESP32:

```json
{
  "type": "open",
  "command_id": "81dfcf86-6bb9-47d8-8e8c-51d03f3a3b3d"
}
```

Мобильное приложение напрямую к этому WebSocket не подключается.

## Формат QR-кода на замке

В спецификации описан такой формат ссылки:

```text
lockey://open?lock_id={lock_id}&lock_code={lock_code}
```

Пример:

```text
lockey://open?lock_id=studio-a1&lock_code=A1B2C3
```

Рекомендация для мобильного приложения:

- Из query parameter `lock_id` взять `lock_id`.
- Из query parameter `lock_code` взять `lock_code`.
- Если `lock_id` из QR отличается от `lock_id` сохраненного бронирования, показать предупреждение и не отправлять запрос на открытие.

## Типовые HTTP ошибки

FastAPI возвращает ошибки в формате:

```json
{
  "detail": "Описание ошибки"
}
```

Для `422` формат будет стандартным pydantic validation error:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, booking_ends_at must be greater than booking_starts_at"
    }
  ]
}
```

Общие рекомендации:

- Network error или timeout - показать ошибку online-соединения и предложить повторить попытку.
- `400` - ошибка входных данных, чаще всего неверный/устаревший код.
- `403` - доступ существует, но сейчас не разрешен по времени.
- `404 Lock is offline` - замок не держит WebSocket с backend.
- `503` на health check - backend/БД недоступны, online flow не использовать.

## Минимальный mobile flow

### При открытии deep link

1. Распарсить `lock_id`, `access_code`, `booking_starts_at`, `booking_ends_at`.
2. Сохранить их в локальное хранилище.
3. Показать пользователю окно бронирования и кнопку перехода к открытию.

### У двери при наличии интернета

1. Сканировать QR на замке.
2. Проверить совпадение `lock_id` из QR с `lock_id` бронирования.
3. Отправить `POST /api/v1/locks/{lock_id}/verify-access`.
4. При `202` показать пользователю, что команда отправлена.
5. При ошибках обработать их по таблице выше.

### У двери без интернета

1. Показать, что online-открытие недоступно.
2. Предложить проверить соединение и повторить попытку.

## Пример curl для online-открытия

```bash
curl -X POST "http://localhost:8000/api/v1/locks/studio-a1/verify-access" \
  -H "Content-Type: application/json" \
  -d '{
    "access_code": "JBSWY3DPEH",
    "lock_code": "A1B2C3",
    "booking_starts_at": "2026-04-22T12:00:00Z",
    "booking_ends_at": "2026-04-22T14:00:00Z"
  }'
```

## Что еще не реализовано в backend

- JWT/user auth для мобильного приложения.
- Постоянное хранение бронирований в PostgreSQL.
- Lookup бронирования по `access_code` без передачи `booking_starts_at` и `booking_ends_at` с клиента.
- REST-подтверждение фактического открытия замка после команды `open`.
- Аудит попыток открытия.
- Webhook обратно в CRM после успешного входа.
- Offline/BLE fallback и offline tickets.
