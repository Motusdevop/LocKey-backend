#include <WiFi.h>
#include <ArduinoWebsockets.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <TFT_eSPI.h>
#include <qrcode.h>

using namespace websockets;

const char* WIFI_SSID = "MGTS_GPON_BE34";
const char* WIFI_PASS = "XQkRrnGW";

const char* WS_URL = "ws://192.168.1.10:8000/ws/device";
const char* QR_API_URL = "http://192.168.1.10:8000/qr/generate";

const char* DEVICE_ID = "door_1";
const char* API_TOKEN = "TEST_TOKEN";

#define RELAY_PIN 26

WebsocketsClient client;
TFT_eSPI tft = TFT_eSPI();

unsigned long lastPing = 0;
unsigned long lastQrFetch = 0;
const unsigned long QR_FETCH_INTERVAL_MS = 2000;
String lastQrText = "";

const uint16_t COLOR_BG = TFT_WHITE;
const uint16_t COLOR_FG = TFT_BLACK;
const uint16_t COLOR_ACCENT = TFT_GREEN;
const int HEADER_HEIGHT = 52;
const int QR_MARGIN = 1;
const int QR_QUIET_ZONE = 1; // Required by QR spec for reliable scanning.

void drawHeader() {
  tft.fillRect(0, 0, tft.width(), HEADER_HEIGHT, COLOR_BG);
  tft.drawFastHLine(0, HEADER_HEIGHT - 1, tft.width(), COLOR_ACCENT);
  tft.setTextColor(COLOR_ACCENT, COLOR_BG);
  tft.setTextDatum(TC_DATUM);
  tft.drawString("myhelsy.com", tft.width() / 2, 16, 4);
}

void drawQrFromHandle(esp_qrcode_handle_t qrcode) {
  const int size = esp_qrcode_get_size(qrcode);
  const int availableW = tft.width() - QR_MARGIN * 2;
  const int availableH = tft.height() - HEADER_HEIGHT - QR_MARGIN;
  const int qrSizePx = min(availableW, availableH);
  const int fullModules = size + (QR_QUIET_ZONE * 2);
  const int scale = max(1, qrSizePx / fullModules);
  const int drawSize = fullModules * scale;
  const int xOffset = (tft.width() - drawSize) / 2;
  const int yOffset = HEADER_HEIGHT + (availableH - drawSize) / 2;

  tft.fillScreen(COLOR_BG);
  drawHeader();

  tft.startWrite();
  for (int y = 0; y < size; y++) {
    for (int x = 0; x < size; x++) {
      if (esp_qrcode_get_module(qrcode, x, y)) {
        tft.fillRect(
          xOffset + ((x + QR_QUIET_ZONE) * scale),
          yOffset + ((y + QR_QUIET_ZONE) * scale),
          scale,
          scale,
          COLOR_FG
        );
      }
    }
  }
  tft.endWrite();
}

void drawStatus(const String& line1, const String& line2 = "") {
  tft.fillRect(0, 0, tft.width(), 52, COLOR_BG);
  tft.setTextColor(COLOR_FG, COLOR_BG);
  tft.setTextDatum(TL_DATUM);
  tft.drawString(line1, 8, 8, 2);
  if (line2.length() > 0) {
    tft.drawString(line2, 8, 28, 2);
  }
}

void drawQr(const String& text) {
  esp_qrcode_config_t cfg = ESP_QRCODE_CONFIG_DEFAULT();
  cfg.max_qrcode_version = 8;
  cfg.qrcode_ecc_level = ESP_QRCODE_ECC_LOW;
  cfg.display_func = drawQrFromHandle;

  esp_err_t err = esp_qrcode_generate(&cfg, text.c_str());
  if (err != ESP_OK) {
    drawStatus("QR encode error", String("ESP err: ") + err);
  }
}

void fetchAndDisplayQr() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  http.begin(QR_API_URL);
  http.addHeader("Authorization", String("Bearer ") + API_TOKEN);
  const int code = http.GET();

  if (code != HTTP_CODE_OK) {
    drawStatus("QR fetch error", String("HTTP: ") + code);
    http.end();
    return;
  }

  String payload = http.getString();
  http.end();

  StaticJsonDocument<512> doc;
  DeserializationError err = deserializeJson(doc, payload);
  if (err) {
    drawStatus("JSON parse error", err.c_str());
    return;
  }

  const char* qrText = doc["qr_text"] | "";
  if (strlen(qrText) == 0) {
    drawStatus("Empty QR payload");
    return;
  }

  String qrValue = String(qrText);
  if (qrValue != lastQrText) {
    drawQr(qrValue);
    lastQrText = qrValue;
    Serial.println("QR updated");
  }
}

void openDoor(int durationMs) {
  digitalWrite(RELAY_PIN, HIGH);
  delay(durationMs);
  digitalWrite(RELAY_PIN, LOW);
}

void onMessageCallback(WebsocketsMessage message) {
  Serial.print("WS Message: ");
  Serial.println(message.data());

  StaticJsonDocument<200> doc;
  deserializeJson(doc, message.data());

  const char* cmd = doc["cmd"];

  if (strcmp(cmd, "OPEN") == 0) {
    int duration = doc["duration"] | 1500;
    openDoor(duration);

    StaticJsonDocument<100> ack;
    ack["status"] = "OK";
    ack["device"] = DEVICE_ID;

    String out;
    serializeJson(ack, out);
    client.send(out);
  }
}

void connectWiFi() {
  drawStatus("WiFi connecting...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected");
  drawStatus("WiFi connected", WiFi.localIP().toString());
}

void connectWS() {
  drawStatus("WS connecting...");
  Serial.println("Connecting WS...");
  client.onMessage(onMessageCallback);

  while (!client.connect(WS_URL)) {
    Serial.println("WS failed, retry...");
    drawStatus("WS retry...");
    delay(2000);
  }

  Serial.println("WS connected");
  drawStatus("WS connected", String("Device: ") + DEVICE_ID);

  StaticJsonDocument<200> auth;
  auth["device_id"] = DEVICE_ID;
  auth["token"] = API_TOKEN;

  String msg;
  serializeJson(auth, msg);
  client.send(msg);
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  tft.init();
  tft.setRotation(0);
  tft.fillScreen(COLOR_BG);
  tft.setTextFont(2);
  drawHeader();

  connectWiFi();
  connectWS();
  fetchAndDisplayQr();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!client.available()) {
    connectWS();
  }

  client.poll();

  if (millis() - lastPing > 10000) {
    client.send("{\"ping\":1}");
    lastPing = millis();
  }

  if (millis() - lastQrFetch > QR_FETCH_INTERVAL_MS) {
    fetchAndDisplayQr();
    lastQrFetch = millis();
  }
}
