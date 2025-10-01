
#include <Servo.h>

const int numServos = 6;
Servo servos[numServos];
const int servoPins[numServos] = {2, 3, 4, 5, 6, 7}; 

void setup() {
  // Initialize serial communication at 9600 baud.
  // This must match the baud rate in the Python script.
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial port to connect.
  }

  // Attach servos to their pins.
  for (int i = 0; i < numServos; i++) {
    servos[i].attach(servoPins[i]);
    // Set initial position to 0 degrees (or a safe position).
    servos[i].write(0);
  }

  Serial.println("Teensy Servo Controller Initialized.");
}

void loop() {
  // Check if any data is available on the serial port.
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 

    if (command.startsWith("S")) {
      // The command is for a servo.
      // Expected format: S<servo_id>:<state>
      // e.g., "S0:1" to turn on servo 0
      int colonIndex = command.indexOf(':');
      if (colonIndex != -1) {
        // Extract servo ID and state.
        String servoIdStr = command.substring(1, colonIndex);
        String stateStr = command.substring(colonIndex + 1);

        int servoId = servoIdStr.toInt();
        int state = stateStr.toInt();

        // Validate the servo ID.
        if (servoId >= 0 && servoId < numServos) {
          Serial.print("Received command for Servo ");
          Serial.print(servoId + 1);
          Serial.print(": State ");
          Serial.println(state);

          // Control the servo based on the received state.
          if (state == 1) { // ON (rotate to 90 degrees)
            servos[servoId].write(90);
          } else { // OFF (rotate to 0 degrees)
            servos[servoId].write(0);
          }
        } else {
          Serial.print("Invalid servo ID: ");
          Serial.println(servoId);
        }
      } else {
        Serial.println("Invalid command format.");
      }
    } else {
      Serial.println("Unknown command.");
    }
  }
}
