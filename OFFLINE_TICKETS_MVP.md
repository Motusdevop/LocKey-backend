# Offline Tickets MVP

## Что реализовано
- Backend выпускает offline ticket после проверки `access_code`.
- Билет самодостаточный и не требует backend в момент открытия.
- Билет подписан `HMAC-SHA256` и кодируется как строка:
  `ot1.<payload_base64url>.<signature_base64url>`
- Backend содержит эталонную валидацию билета, по которой можно собирать такую же проверку на ESP32.

## Что внутри билета
Payload содержит:
- `v`
- `ticket_id`
- `lock_id`
- `issued_at`
- `valid_from`
- `valid_until`

Все временные поля хранятся как Unix timestamp UTC.

## Как Android получает билет
1. Пользователь вводит `access_code`.
2. Приложение отправляет:
   `POST /api/v1/offline-tickets/issue`
3. Backend проверяет, что `access_code` соответствует `lock_id + booking window`.
4. Backend возвращает `offline_ticket`.
5. Приложение сохраняет билет локально.

Важно:
- в текущем MVP backend всё ещё stateless относительно бронирования
- поэтому приложение отправляет вместе с `access_code` ещё и `booking_starts_at`, `booking_ends_at`
- позже это нужно заменить на lookup по БД

## Как ESP32 должен проверять билет
1. Получить строку `offline_ticket` по BLE.
2. Разбить по `.` на `version`, `payload`, `signature`.
3. Проверить, что `version == "ot1"`.
4. Пересчитать `HMAC-SHA256(payload_base64url, offline_ticket_secret)`.
5. Сравнить подпись в постоянное время.
6. Декодировать payload JSON.
7. Проверить:
   - `lock_id` совпадает с ID замка
   - текущее время попадает в `valid_from..valid_until`
   - ticket version поддерживается
8. Если всё валидно, открыть реле.

## Ограничения MVP
- Это shared-secret схема: backend и замок знают один и тот же секрет.
- Если секрет извлечён из прошивки одного замка, можно подделывать билеты для других замков с тем же секретом.
- Билет не привязан к конкретному телефону.
- Нет защиты от replay по BLE.

## Следующий безопасный шаг после MVP
- Перейти на подпись сервера приватным ключом и проверку публичным ключом на замке.
- Привязать билет к `phone_pubkey`.
- Добавить BLE challenge-response.
