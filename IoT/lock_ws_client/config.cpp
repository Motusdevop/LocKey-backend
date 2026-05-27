#include <TFT_eSPI.h>

#include "config.h"

// WiFi & Backend
const char* const WIFI_SSID = "Motus";
const char* const WIFI_PASS = "Merstop1";
const char* const BACKEND_HOST = "45.154.35.214/LocKey";
const uint16_t BACKEND_PORT = 8000;
const char* const LOCK_ID = "studio-a1";
const char* const LOCK_NAME = "Studio A1";
const char* const LOCK_PUBLIC_BASE_URL = "http://45.154.35.214/LocKey/open";

// Pins
const uint8_t RELAY_PIN = 26;
const uint8_t RELAY_ACTIVE_LEVEL = HIGH;
const uint8_t RELAY_INACTIVE_LEVEL = LOW;

// Intervals
const unsigned long OPEN_DURATION_MS = 1500;
const unsigned long WS_RECONNECT_INTERVAL_MS = 3000;

// Display constants
const uint16_t COLOR_BG = TFT_WHITE;
const uint16_t COLOR_FG = TFT_BLACK;
const uint16_t COLOR_ACCENT = TFT_GREEN;
