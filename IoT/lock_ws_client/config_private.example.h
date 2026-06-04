#pragma once

// Copy values into config_private.h. The real file is ignored by git.
#define LOCKEY_WIFI_SSID "your-wifi-ssid"
#define LOCKEY_WIFI_PASS "your-wifi-password"

// Include the production prefix here when the backend is served behind /LocKey.
#define LOCKEY_BACKEND_HOST "example.com/LocKey"
#define LOCKEY_BACKEND_PORT 8000

#define LOCKEY_LOCK_ID "studio-a1"
#define LOCKEY_LOCK_NAME "Studio A1"
#define LOCKEY_LOCK_PUBLIC_BASE_URL "http://example.com/LocKey/open"
