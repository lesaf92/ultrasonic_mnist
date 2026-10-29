// Reads two HC-SR04 sensors in turn and sends each pair of distances to server.py over WiFi as one UDP packet,
// "<sensor A mm> <sensor B mm>", -1 for no echo. The same line goes to the USB serial port for debugging.
#include <WiFi.h>
#include <WiFiUdp.h>

#if !__has_include("config.h")
#error "copy firmware/config.example.h to firmware/config.h and fill in your WiFi, computer address and pins"
#endif
#include "config.h"

WiFiUDP udp;

int readMm(int trig, int echo) {
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  // ~5.8 us of echo per mm of distance, plus up to ~3 ms before some modules raise ECHO
  unsigned long us = pulseIn(echo, HIGH, MAX_MM * 6 + 3000);
  return us ? us * 343 / 2000 : -1;  // sound at 343 m/s (20 °C), there and back
}

void setup() {
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);  // don't stall when no serial monitor is reading
  pinMode(TRIG_A, OUTPUT);
  pinMode(TRIG_B, OUTPUT);
  pinMode(ECHO_A, INPUT);
  pinMode(ECHO_B, INPUT);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);  // power saving delays packets
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);  // reconnects by itself if the network drops
}

void loop() {
  int a = readMm(TRIG_A, ECHO_A);
  delay(PING_GAP_MS);
  int b = readMm(TRIG_B, ECHO_B);
  delay(PING_GAP_MS);

  char msg[24];
  int n = snprintf(msg, sizeof msg, "%d %d", a, b);
  static bool online = false;
  if (online != (WiFi.status() == WL_CONNECTED)) {
    online = !online;
    if (online) Serial.printf("WiFi up, %s sending to %s:%d\n", WiFi.localIP().toString().c_str(), SERVER_IP, SERVER_PORT);
    else Serial.println("WiFi down, retrying");
  }
  if (online) {
    udp.beginPacket(SERVER_IP, SERVER_PORT);
    udp.write((const uint8_t *)msg, n);
    udp.endPacket();
  }
  Serial.println(msg);
}
