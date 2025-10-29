#include <OneWire.h>

#define ONE_WIRE_PIN 10  // Change to your MAX31850 data pin

OneWire ds(ONE_WIRE_PIN);

void setup() {
  Serial.begin(9600);
  while (!Serial); // Wait for Serial Monitor (Teensy only)
}

void loop() {
  byte data[9];
  int16_t raw;
  float celsius;

  // Trigger temperature conversion
  ds.reset();
  ds.skip();           // Skip ROM, only one sensor
  ds.write(0x44, 1);   // Start conversion
  delay(1000);         // Wait for conversion (~750 ms)

  // Read scratchpad
  ds.reset();
  ds.skip();
  ds.write(0xBE);      // Read scratchpad
  for (byte i = 0; i < 9; i++) {
    data[i] = ds.read();
  }

  // Convert raw to Celsius
  raw = (data[1] << 8) | data[0];
  if (raw & 0x01) {
    // Fault detected
    Serial.println("NaN");
  } else {
    celsius = (float)raw / 16.0;
    Serial.println(celsius, 2);  // Print Celsius with 2 decimal places
  }

  delay(1000);  // Print once per second
}
