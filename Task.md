🛠 1. Backend (Python / FastAPI)

Центральный узел, управляющий логикой доступа и интеграцией с CRM.
Функциональные требования:

    REST API для CRM: Эндпоинт для приема Webhook от amoCRM. Парсинг данных сделки и создание записи о бронировании.

    Генерация JWT и OAT: * Создание временных токенов доступа (JWT).

        Генерация зашифрованных оффлайн-билетов (Offline Access Tickets), подписанных закрытым ключом сервера (ED25519 или RSA).

    WebSocket Gateway: Поддержка постоянного соединения с ESP32 для мгновенной передачи команды OPEN.

    Система верификации: Логика проверки динамического QR-хэша с учетом временного окна (Time-drift).

    Webhook Manager: Отправка обратных уведомлений в CRM при успешном входе.

Технический стек:

    Framework: FastAPI (Асинхронность критична для WebSockets).

    DB: PostgreSQL + SQLAlchemy (AsyncPG).

    Auth: PyJWT / Passlib.

    Task Queue: BackgroundTasks (FastAPI) или Celery для отправки уведомлений в CRM.

🔌 2. IoT (ESP32 / C++)

Контроллер, отвечающий за физический доступ и генерацию динамических данных.
Функциональные требования:

    Dynamic QR Generation: Генерация уникального хэша каждые 2 секунды на основе DeviceID + Secret + Timestamp. Отображение на OLED-дисплее.

    WebSocket Client: Поддержание соединения с бэкендом в реальном времени.

    Relay Control: Управление электромагнитным/механическим замком через GPIO.

    BLE Server (Fallback): * Работа в режиме Beacon (для обнаружения приложением).

        Прием и локальная валидация Offline Access Ticket (OAT) через шифрованный канал.

    Time Sync: Синхронизация времени через NTP + наличие RTC (Real Time Clock) для работы в оффлайне.

Технический стек:

    Platform: ESP-IDF или Arduino Framework.

    Libraries: WebSocketsClient, NimBLE-Arduino (для эффективного BLE), U8g2 (для дисплея).

    Security: Использование публичного ключа сервера для проверки подписи оффлайн-билетов.