import sys
import random
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer


# -------------------------------------------------------------------------------
# GUI Creation

class ServoPressureGUI(QWidget):


    def __init__(self):
        super().__init__()
        self.setWindowTitle("Teensy Servo Control and Pressure Monitor")

        # Initialize serial port connection
        self.serial_port = None
        self.connect_to_teensy()

        # Start timer for pressure simulation (this can be replaced with reading from serial)
        self.pressure_timer = QTimer(self)
        self.pressure_timer.timeout.connect(self.update_pressures)
        self.pressure_timer.start(1000)

        self.init_ui()

    def connect_to_teensy(self):

        teensy_port = None
        ports = serial.tools.list_ports.comports()
        for p in ports:
            # Teensy 4.1 often appears with a specific VID/PID.
            # Teensy (Product ID 0x0483, Vendor ID 0x16C0)
            if p.vid == 0x16C0 and p.pid == 0x0483:
                teensy_port = p.device
                break

        if teensy_port:
            try:
                self.serial_port = serial.Serial(teensy_port, 9600, timeout=1)
                print(f"Connected to Teensy on {teensy_port}")
            except serial.SerialException as e:
                QMessageBox.critical(
                    self,
                    "Serial Connection Error",
                    f"Could not open serial port {teensy_port}: {e}"
                )
        else:
            QMessageBox.warning(
                self,
                "Device Not Found",
                "Teensy not found. Please ensure it is connected and the drivers are installed."
            )

    def init_ui(self):
        # Create layout
        main_layout = QVBoxLayout()

        # Create servo buttons section
        servo_group = QGroupBox("Servo Controls")
        servo_layout = QGridLayout()

        # Name servos
        self.servo_names = [
            "Servo One", "Servo Two", "Servo Three",
            "Servo Four", "Servo Five", "Servo Six"
        ]

        # Create and add the servo buttons to the grid
        self.servo_buttons = []
        for i, name in enumerate(self.servo_names):
            btn = QPushButton(name)
            btn.setProperty("servo_id", i)  # Store servo ID
            # Set initial color to red
            btn.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; padding: 10px;"
            )
            # Connect each button's clicked signal to the handle_servo_click method.
            btn.clicked.connect(lambda _, b=btn: self.handle_servo_click(b))

            row = i // 2
            col = i % 2
            servo_layout.addWidget(btn, row, col)
            self.servo_buttons.append(btn)

        servo_group.setLayout(servo_layout)
        main_layout.addWidget(servo_group)

        # Pressure Displays Section
        pressure_group = QGroupBox("Pressure Readings")
        pressure_layout = QGridLayout()

        self.pressure1_label = QLabel("Pressure 1: -- psi")
        self.pressure2_label = QLabel("Pressure 2: -- psi")

        self.pressure1_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; background-color: green; padding: 10px; border: 1px solid gray;")
        self.pressure2_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; background-color: green; padding: 10px; border: 1px solid gray;")

        pressure_layout.addWidget(self.pressure1_label, 0, 0)
        pressure_layout.addWidget(self.pressure2_label, 0, 1)

        pressure_group.setLayout(pressure_layout)
        main_layout.addWidget(pressure_group)

        self.setLayout(main_layout)

    def update_pressures(self):
        """Simulates a subroutine feeding new pressure values."""
        pressure1 = random.uniform(50.0, 70.0)
        pressure2 = random.uniform(100.0, 120.0)

        self.pressure1_label.setText(f"Pressure 1: {pressure1:.2f} psi")
        self.pressure2_label.setText(f"Pressure 2: {pressure2:.2f} psi")

    def handle_servo_click(self, clicked_button):
        """
        Toggles servo state (ON/OFF) and sends a command to the Teensy.
        """
        servo_id = clicked_button.property("servo_id")
        servo_name = clicked_button.text()

        current_style = clicked_button.styleSheet()
        is_selected = False

        if "background-color: green" in current_style:
            # If it's currently green, change it to red (turn OFF)
            clicked_button.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; padding: 10px;"
            )
            is_selected = False
        else:
            # If it's currently red, change it to green (turn ON)
            clicked_button.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; padding: 10px;"
            )
            is_selected = True

        # Construct and send the command to the Teensy
        # Protocol: S<servo_id>:<state>\n
        # <servo_id> is 0-indexed (0 to 5), <state> is 1 (ON) or 0 (OFF)
        # Example command: "S0:1\n" for turning on Servo 1
        state_value = 1 if is_selected else 0
        command = f"S{servo_id}:{state_value}\n"

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(command.encode('utf-8'))
                print(f"Sent command: {command.strip()}")
            except serial.SerialException as e:
                print(f"Error sending command: {e}")
                QMessageBox.critical(
                    self,
                    "Serial Communication Error",
                    f"Lost connection to Teensy: {e}"
                )
                self.serial_port.close()
                self.serial_port = None
        else:
            print("Serial port not connected.")
            QMessageBox.warning(
                self,
                "Connection Issue",
                "Serial port is not connected. Please check your Teensy."
            )

    def closeEvent(self, event):
        """
        Closes the serial port gracefully when the application is exited.
        """
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            print("Serial port closed.")
        print("Closing GUI window.")
        event.accept()


# Main application logic
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServoPressureGUI()
    window.show()
    sys.exit(app.exec())
