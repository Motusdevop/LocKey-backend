#include <TFT_eSPI.h>

#include "config.h"

#if __has_include("config_private.h")
#include "config_private.h"
#endif

#ifndef LOCKEY_WIFI_SSID
#define LOCKEY_WIFI_SSID "CHANGE_ME"
#endif

#ifndef LOCKEY_WIFI_PASS
#define LOCKEY_WIFI_PASS "CHANGE_ME"
#endif

#ifndef LOCKEY_BACKEND_HOST
#define LOCKEY_BACKEND_HOST "localhost"
#endif

#ifndef LOCKEY_BACKEND_PORT
#define LOCKEY_BACKEND_PORT 8000
#endif

#ifndef LOCKEY_LOCK_ID
#define LOCKEY_LOCK_ID "studio-a1"
#endif

#ifndef LOCKEY_LOCK_NAME
#define LOCKEY_LOCK_NAME "Studio A1"
#endif

#ifndef LOCKEY_LOCK_PUBLIC_BASE_URL
#define LOCKEY_LOCK_PUBLIC_BASE_URL "http://localhost:8000/open"
#endif

// WiFi & Backend
const char* const WIFI_SSID = LOCKEY_WIFI_SSID;
const char* const WIFI_PASS = LOCKEY_WIFI_PASS;
const char* const BACKEND_HOST = LOCKEY_BACKEND_HOST;
const uint16_t BACKEND_PORT = LOCKEY_BACKEND_PORT;
const char* const LOCK_ID = LOCKEY_LOCK_ID;
const char* const LOCK_NAME = LOCKEY_LOCK_NAME;
const char* const LOCK_PUBLIC_BASE_URL = LOCKEY_LOCK_PUBLIC_BASE_URL;

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
