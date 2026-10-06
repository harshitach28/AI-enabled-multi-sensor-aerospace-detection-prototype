#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ============================================================
// WIFI & TELEGRAM CREDENTIALS
// ============================================================
const char* WIFI_SSID = "saaas";
const char* WIFI_PASS = "hrishiHM@28";

#define BOT_TOKEN "8933941414:AAGjzPwHWIW30-v-B5YgARWzpFj0JTLHErw"
#define CHAT_ID   "8877314594"

// ============================================================
// HARDWARE PINS
// ============================================================
#define TRIG_PIN  5    // Ultrasonic Trigger Pin
#define ECHO_PIN  18   // Ultrasonic Echo Pin
#define FLAME_PIN 19   // IR Flame Sensor DO Pin

bool flameDetectedState = false;
unsigned long lastSensorRead = 0;

void sendTelegramMessage(String message) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClientSecure client;
    client.setInsecure(); // Skip SSL cert validation
    client.setTimeout(5000); // 5s timeout to prevent hanging
    
    HTTPClient http;
    String url = "https://api.telegram.org/bot" + String(BOT_TOKEN) + "/sendMessage?chat_id=" + String(CHAT_ID) + "&text=" + message;
    
    http.begin(client, url);
    int httpCode = http.GET();
    
    if (httpCode > 0) {
      Serial.println("[SUCCESS] Telegram message sent!");
    } else {
      Serial.print("[ERROR] Telegram request failed, error: ");
      Serial.println(http.errorToString(httpCode));
    }
    http.end();
  }
}

float readUltrasonicDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 30ms timeout
  if (duration == 0) return 400.0;
  return (duration * 0.0343) / 2.0;
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(FLAME_PIN, INPUT);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 20) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[SUCCESS] WiFi Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    sendTelegramMessage("%F0%9F%9A%80%20Missile%20Radar%20System%20Online%20%26%20Ready!");
  } else {
    Serial.println("\n[ERROR] WiFi Connection Failed!");
  }
}

void loop() {
  if (millis() - lastSensorRead > 50) {
    lastSensorRead = millis();

    int flameState = digitalRead(FLAME_PIN);

    if (flameState == LOW) {
      Serial.println("FLAME");

      if (!flameDetectedState) {
        flameDetectedState = true;
        Serial.println("Sending FLAME Alert to Telegram...");
        sendTelegramMessage("%F0%9F%94%A5%20ALARM:%20External%20entity%20on%20the%20sky%20TARGET%20LOCKED!");
      }
    } 
    else {
      if (flameDetectedState) {
        flameDetectedState = false;
        Serial.println("CLEAR");
      }

      float distance = readUltrasonicDistance();
      Serial.println(distance);
    }
  }
}
