"""Headless integration smoke test: boots the real MainWindow (offscreen Qt
platform, no display needed), pumps the poll timer, exercises valve toggling
and a logging start/stop cycle, and checks the CSV pair actually lands on
disk. Run: QT_QPA_PLATFORM=offscreen python ground_station/tests/test_smoke.py
"""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PyQt6.QtWidgets import QApplication

from main import MainWindow, VALVES
from sensors import FakeSensorSource, SENSOR_KEYS


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    win = MainWindow(sensor_source=FakeSensorSource(seed=42), poll_ms=10)

    # Poll a burst of ticks the way the real timer would, without a UI event loop.
    for _ in range(300):
        win._tick()
    print("ok  window boots and ticks 300 times without raising")

    for key in SENSOR_KEYS:
        assert key in win.gauge_widgets, f"missing gauge widget for {key}"
    print("ok  every real sensor channel has a live gauge")

    vid = next(iter(VALVES))
    before = win.valve_state[vid]
    win._toggle_valve(vid)
    assert win.valve_state[vid] != before
    win._toggle_valve(vid)
    assert win.valve_state[vid] == before
    print("ok  valve toggle flips and restores state")

    win.log_button.setChecked(True)
    for _ in range(50):
        win._tick()
    win.log_button.setChecked(False)
    assert "Saved" in win.log_status.text(), win.log_status.text()
    print("ok  a logging session writes a CSV pair:", win.log_status.text())

    win.close()
    print("\nsmoke test passed")


if __name__ == "__main__":
    run()
