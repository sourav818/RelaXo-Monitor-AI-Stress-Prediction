#include <Wire.h>
#include "MAX30105.h"
#include <DHT.h>

// ---------- DHT11 ----------
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// ---------- MAX30102 ----------
MAX30105 particleSensor;

long lastBeat = 0;
int bpm = 0;
int avgBPM = 0;

long prevValue = 0;

// averaging
int bpmBuffer[5] = {0};
int index = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  dht.begin();

  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found!");
    while (1);
  }

  particleSensor.setup();
  particleSensor.setPulseAmplitudeRed(0x3F);
  particleSensor.setPulseAmplitudeIR(0x3F);
}

void loop() {

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  long irValue = particleSensor.getIR();

  // ❤️ Manual peak detection
  if (irValue > prevValue && irValue > 50000) {

    long currentTime = millis();

    if (currentTime - lastBeat > 500) {
      bpm = 60000 / (currentTime - lastBeat);
      lastBeat = currentTime;

      if (bpm > 40 && bpm < 180) {
        bpmBuffer[index++] = bpm;
        index %= 5;

        int sum = 0;
        for (int i = 0; i < 5; i++) {
          sum += bpmBuffer[i];
        }
        avgBPM = sum / 5;
      }
    }
  }

  prevValue = irValue;

  // ✅ SEND CLEAN DATA TO PYTHON
  if (irValue > 30000 && avgBPM > 0) {
    Serial.print(avgBPM);
    Serial.print(",");
    Serial.print(temp);
    Serial.print(",");
    Serial.println(hum);
  } else {
    Serial.println("0,0,0");
  }

  delay(200);
}