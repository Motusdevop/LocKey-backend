# LocKey: Smart Access System

## Project Overview
LocKey is a smart lock ecosystem designed for rehearsal studios and automated spaces. It bridges the gap between booking systems (amoCRM) and physical hardware (ESP32) using a hybrid Online (QR/WebSocket) and Offline (BLE/OAT) approach.

### Core Workflows
1.  **Booking:** Client books via CRM -> Backend generates JWT & Offline Access Ticket (OAT).
2.  **Online Access:** Client scans dynamic QR on ESP32 -> App validates via Backend -> Backend sends `OPEN` via WebSocket to ESP32.
3.  **Offline Access:** App detects ESP32 via BLE beacon -> Transmits OAT -> ESP32 validates signature locally via public key and RTC.

## Tech Stack
- **Backend:** Python 3.12, FastAPI (Async), PostgreSQL + SQLAlchemy, WebSockets, `uv` for management.
- **IoT:** ESP32 (Arduino/ESP-IDF), BLE (NimBLE), WebSockets, OLED (U8g2).
- **Mobile:** Kotlin Compose (not in this repo, but interacts with it).
- **Security:** JWT for API, ED25519/RSA for Offline Tickets, Time-based OTP for QR.

## Development Standards (from codexstyle.md)
- **Pattern:** Pragmatic FastAPI (Routes -> Services -> DB). Avoid over-engineering.
- **Async First:** Mandatory for I/O operations.
- **TDD:** Write tests before implementation. Use `pytest` with async support.
- **Logging:** Centralized via `loguru`. No secrets in logs.
- **Hygiene:** Keep repo clean of `__pycache__`, `.pytest_cache`, etc. Use `uv`.

## Key Files
- `backend/app/main.py`: Entry point.
- `backend/app/api/routes/locks.py`: WebSocket and lock management.
- `backend/app/api/routes/qr.py`: Dynamic QR validation.
- `IoT/lock_ws_client/`: ESP32 firmware logic.

## AI Guidelines
- **Language:** Code in English, comments only when necessary.
- **Refactoring:** Always include regression tests for bug fixes.
- **Dependencies:** Use `uv add` for new packages. Ensure `uv.lock` is updated.
- **Tooling:** Prefer `ruff` for formatting if available.
