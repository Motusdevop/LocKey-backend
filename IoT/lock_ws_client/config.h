#pragma once

#include <Arduino.h>

// WiFi & Backend
extern const char* const WIFI_SSID;
extern const char* const WIFI_PASS;
extern const char* const BACKEND_HOST;
extern const uint16_t BACKEND_PORT;
extern const char* const LOCK_ID;
extern const char* const LOCK_NAME;
extern const char* const LOCK_PUBLIC_BASE_URL;

// Pins
extern const uint8_t RELAY_PIN;
extern const uint8_t RELAY_ACTIVE_LEVEL;
extern const uint8_t RELAY_INACTIVE_LEVEL;

// Intervals
extern const unsigned long OPEN_DURATION_MS;
extern const unsigned long WS_RECONNECT_INTERVAL_MS;

// Display constants
extern const uint16_t COLOR_BG;
extern const uint16_t COLOR_FG;
extern const uint16_t COLOR_ACCENT;
