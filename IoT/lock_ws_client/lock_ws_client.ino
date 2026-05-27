#include <WiFi.h>
#include <ArduinoJson.h>
#include <ArduinoWebsockets.h>
#include <TFT_eSPI.h>
#include <qrcode.h>

#include "config.h"

using namespace websockets;

WebsocketsClient websocketClient;
TFT_eSPI tft = TFT_eSPI();

bool relayActive = false;
unsigned long relayReleaseAtMs = 0;
unsigned long lastConnectAttemptAtMs = 0;

String currentCode = "------";
unsigned long currentCodeExpiresAt = 0;

String buildWebSocketUrl() {
  return "ws://" + String(BACKEND_HOST) + "/api/v1/ws/locks/" + LOCK_ID;
}

String buildOpenUrl() {
  return String(LOCK_PUBLIC_BASE_URL) + "/" + LOCK_ID + "?s=" + currentCode;
}

void drawCenteredText(const String &text, int y, int font, uint16_t fg, uint16_t bg) {
  tft.setTextDatum(MC_DATUM);
  tft.setTextColor(fg, bg);
  tft.drawString(text, tft.width() / 2, y, font);
}

void drawScreen(const String &title, const String &value, const String &footer = "") {
  tft.fillScreen(COLOR_BG);
  drawCenteredText(title, 24, 2, COLOR_ACCENT, COLOR_BG);
  drawCenteredText(value, tft.height() / 2, 7, COLOR_FG, COLOR_BG);
  if (footer.length() > 0) {
    drawCenteredText(footer, tft.height() - 20, 2, COLOR_FG, COLOR_BG);
  }
}

void showStatus(const String &status, const String &detail = "") {
  drawScreen(status, LOCK_ID, detail);
}

void drawQrModules(esp_qrcode_handle_t qrcode) {
  const int quietZone = 2;
  const int qrSize = esp_qrcode_get_size(qrcode);
  const int topPadding = 8;
  const int bottomArea = 70;
  const int availableWidth = tft.width() - 16;
  const int availableHeight = tft.height() - bottomArea - topPadding;
  const int fullModules = qrSize + quietZone * 2;
  const int scale = max(1, min(availableWidth, availableHeight) / fullModules);
  const int drawSize = fullModules * scale;
  const int xOffset = (tft.width() - drawSize) / 2;
  const int yOffset = topPadding + (availableHeight - drawSize) / 2;

  tft.fillScreen(COLOR_BG);

  tft.startWrite();
  for (int y = 0; y < qrSize; y++) {
    for (int x = 0; x < qrSize; x++) {
      if (esp_qrcode_get_module(qrcode, x, y)) {
        tft.fillRect(
          xOffset + (x + quietZone) * scale,
          yOffset + (y + quietZone) * scale,
          scale,
          scale,
          COLOR_FG
        );
      }
    }
  }
  tft.endWrite();
}

void drawQrFooter() {
  tft.fillRect(0, tft.height() - 70, tft.width(), 70, COLOR_BG);
  drawCenteredText(LOCK_NAME, tft.height() - 48, 2, COLOR_ACCENT, COLOR_BG);
  drawCenteredText(currentCode, tft.height() - 22, 4, COLOR_FG, COLOR_BG);
}

void showQrCode() {
  esp_qrcode_config_t cfg = ESP_QRCODE_CONFIG_DEFAULT();
  cfg.max_qrcode_version = 8;
  cfg.qrcode_ecc_level = ESP_QRCODE_ECC_LOW;
  cfg.display_func = drawQrModules;

  const String openUrl = buildOpenUrl();
  esp_err_t err = esp_qrcode_generate(&cfg, openUrl.c_str());
  if (err != ESP_OK) {
    drawScreen("QR error", currentCode, String("ESP err: ") + err);
    return;
  }

  drawQrFooter();
}

void setRelayState(uint8_t state) {
  digitalWrite(RELAY_PIN, state);
}

void openRelay(unsigned long durationMs) {
  setRelayState(RELAY_ACTIVE_LEVEL);
  relayActive = true;
  relayReleaseAtMs = millis() + durationMs;
  Serial.printf("Relay opened for %lu ms\n", durationMs);
}

void releaseRelayIfNeeded() {
  if (!relayActive) {
    return;
  }

  if (static_cast<long>(millis() - relayReleaseAtMs) >= 0) {
    setRelayState(RELAY_INACTIVE_LEVEL);
    relayActive = false;
    Serial.println("Relay released");
  }
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  showStatus("WiFi", "connecting");
  Serial.printf("Connecting WiFi to %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi connected, IP: ");
  Serial.println(WiFi.localIP());
}

void connectWebSocket() {
  if (WiFi.status() != WL_CONNECTED || websocketClient.available()) {
    return;
  }

  if (millis() - lastConnectAttemptAtMs < WS_RECONNECT_INTERVAL_MS) {
    return;
  }

  lastConnectAttemptAtMs = millis();

  const String wsUrl = buildWebSocketUrl();
  Serial.print("Connecting WS to ");
  Serial.println(wsUrl);
  showStatus("WS", "connecting");

  if (!websocketClient.connect(wsUrl)) {
    Serial.println("WS connect failed");
    showStatus("WS", "connect failed");
    return;
  }

  Serial.println("WS connected");
  showStatus("WS", "connected");
}

void handleCodeMessage(const JsonDocument &document) {
  const char *value = document["value"] | "";
  const unsigned long expiresAt = document["expires_at"] | 0;

  if (strlen(value) == 0) {
    Serial.println("Code message ignored: empty value");
    return;
  }

  currentCode = String(value);
  currentCodeExpiresAt = expiresAt;
  showQrCode();

  Serial.print("Code updated: ");
  Serial.println(currentCode);
  Serial.print("Open URL: ");
  Serial.println(buildOpenUrl());
}

void handleOpenMessage(const JsonDocument &document) {
  const unsigned long durationMs = document["duration_ms"] | OPEN_DURATION_MS;
  openRelay(durationMs);
}

void handleMessage(const String &payload) {
  Serial.print("WS <- ");
  Serial.println(payload);

  StaticJsonDocument<256> document;
  DeserializationError error = deserializeJson(document, payload);
  if (error) {
    Serial.printf("Invalid JSON: %s\n", error.c_str());
    return;
  }

  const char *type = document["type"] | "";

  if (strcmp(type, "code") == 0) {
    handleCodeMessage(document);
    return;
  }

  if (strcmp(type, "open") == 0) {
    handleOpenMessage(document);
    return;
  }

  Serial.printf("Unhandled message type: %s\n", type);
}

void maintainConnection() {
  if (!websocketClient.available()) {
    connectWebSocket();
    return;
  }

  websocketClient.poll();
}

void setup() {
  Serial.begin(115200);

  pinMode(RELAY_PIN, OUTPUT);
  setRelayState(RELAY_INACTIVE_LEVEL);

  tft.init();
  tft.setRotation(0);
  tft.fillScreen(COLOR_BG);
  tft.setTextFont(2);

  websocketClient.onMessage([](WebsocketsMessage message) {
    handleMessage(message.data());
  });

  connectWiFi();
  connectWebSocket();
  showStatus("Boot", LOCK_ID);
}

void loop() {
  connectWiFi();
  maintainConnection();
  releaseRelayIfNeeded();
}
