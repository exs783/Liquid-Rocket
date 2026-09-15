"""CWRU Liquid Rocket ground-station GUI -- merges the two prototypes that
previously lived as separate, never-integrated scripts:

  - main2_test.py / data_mainwindow.py: live sensor plots + CSV logging
  - GUI_Valve_Example.py / GUI_SVG_BUILT_IN_PYTHON.py: P&ID valve controls

into one PyQt6 app sharing a single sensor/valve state (see sensors.py,
logging_utils.py, svg_widgets.py). Runs entirely against FakeSensorSource --
no Teensy/serial connection required. Swapping in real hardware later means
writing a SerialSensorSource with the same next_line() interface (see
sensors.py's module docstring); nothing else in this file changes.

Run: python ground_station/main.py
"""
from __future__ import annotations

import os
import sys
import time

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

from logging_utils import SessionRecorder
from sensors import SENSOR_KEYS, SENSOR_META, FakeSensorSource, parse_line
from svg_widgets import ClickableSvgWidget, gauge_svg_for, valve_svg

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

VALVES = {
    "MV-1": "Main Propellant Valve",
    "IGN-1": "Igniter",
}

PANEL_QSS = """
    QMainWindow, QWidget { background: #0a0c0a; color: #d7d9d4; font-family: 'Segoe UI', sans-serif; }
    QTabWidget::pane { border: 1px solid #2c3a30; background: #0a0c0a; }
    QTabBar::tab { background: #10160f; color: #8a8f86; padding: 8px 18px; border: 1px solid #2c3a30; border-bottom: none; }
    QTabBar::tab:selected { color: #f5c518; border-bottom: 2px solid #f5c518; }
    QGroupBox {
        border: 1px solid #2c3a30; border-radius: 4px; margin-top: 14px;
        font-weight: bold; color: #8fffb0; letter-spacing: 1px;
    }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 6px; }
    QLabel { color: #d7d9d4; }
    QPushButton {
        background: #10160f; color: #f5c518; border: 1px solid #f5c518;
        border-radius: 3px; padding: 6px 14px; font-weight: bold; letter-spacing: 1px;
    }
    QPushButton:hover { background: #1a2418; }
    QPushButton:checked { background: #f5c518; color: #0a0c0a; }
"""


class Placard(QLabel):
    """A riveted stencil-style label -- the borrowed identity mark from the
    direction's raise (see PRODUCT.md / DESIGN.md)."""

    def __init__(self, text: str, parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet("""
            background: #f5c518; color: #0a0c0a; font-weight: bold;
            letter-spacing: 2px; padding: 3px 10px; border-radius: 2px;
        """)


class MainWindow(QMainWindow):
    def __init__(self, sensor_source=None, poll_ms: int = 150):
        super().__init__()
        self.setWindowTitle("CWRU Liquid Rocket — Ground Station")
        self.setStyleSheet(PANEL_QSS)
        self.resize(1100, 720)

        self.source = sensor_source or FakeSensorSource()
        self.recorder = SessionRecorder()
        self.logging_active = False
        self._session_started_at = None

        self.state = {key: (meta["range"][0] + meta["range"][1]) / 2 for key, meta in SENSOR_META.items()}
        self.valve_state = {vid: False for vid in VALVES}  # start closed/safe

        self.gauge_widgets: dict[str, ClickableSvgWidget] = {}
        self.valve_widgets: dict[str, ClickableSvgWidget] = {}

        tabs = QTabWidget()
        tabs.addTab(self._build_controls_tab(), "Controls")
        tabs.addTab(self._build_data_tab(), "Live Data")
        tabs.addTab(self._build_logging_tab(), "Logging")
        self.setCentralWidget(tabs)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(poll_ms)

    # ---- Controls tab: real P&ID schematic (reference) + working valve toggles ----
    def _build_controls_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)

        schematic_group = QGroupBox("P&ID — Rocket_P&ID_GUI1.svg")
        schematic_layout = QVBoxLayout(schematic_group)
        schematic = QSvgWidget(os.path.join(ASSETS_DIR, "Rocket_P&ID_GUI1.svg"))
        schematic.setMinimumWidth(160)
        schematic.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        schematic_layout.addWidget(schematic)
        layout.addWidget(schematic_group, 1)

        controls_group = QGroupBox("Manual Overrides")
        controls_layout = QVBoxLayout(controls_group)
        for vid, name in VALVES.items():
            row = QFrame()
            row_layout = QHBoxLayout(row)
            widget = ClickableSvgWidget(vid)
            widget.load_svg(valve_svg(self.valve_state[vid]))
            widget.clicked.connect(self._toggle_valve)
            self.valve_widgets[vid] = widget

            label_col = QVBoxLayout()
            label_col.addWidget(Placard(f"{vid} — {name}"))
            status = QLabel("CLOSED")
            status.setObjectName(f"status_{vid}")
            label_col.addWidget(status)
            row_layout.addWidget(widget)
            row_layout.addLayout(label_col)
            row_layout.addStretch()
            controls_layout.addWidget(row)
        controls_layout.addStretch()
        layout.addWidget(controls_group, 1)
        return page

    def _toggle_valve(self, vid: str) -> None:
        self.valve_state[vid] = not self.valve_state[vid]
        self.valve_widgets[vid].load_svg(valve_svg(self.valve_state[vid]))
        status = self.valve_widgets[vid].parent().findChild(QLabel, f"status_{vid}")
        if status is not None:
            status.setText("OPEN" if self.valve_state[vid] else "CLOSED")
            status.setStyleSheet(f"color: {'#8fffb0' if self.valve_state[vid] else '#ff4d4d'}; font-weight: bold;")

    # ---- Live Data tab: one gauge per real sensor channel ----
    def _build_data_tab(self) -> QWidget:
        page = QWidget()
        grid = QGridLayout(page)
        for i, key in enumerate(SENSOR_KEYS):
            meta = SENSOR_META[key]
            group = QGroupBox(f"{key} — {meta['label']}")
            v = QVBoxLayout(group)
            widget = ClickableSvgWidget(key)
            widget.setCursor(Qt.CursorShape.ArrowCursor)
            lo, hi = meta["range"]
            widget.load_svg(gauge_svg_for(key, self.state[key], hi))
            self.gauge_widgets[key] = widget
            v.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
            value_label = QLabel(f"{self.state[key]:.1f} {meta['unit']}")
            value_label.setObjectName(f"value_{key}")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(value_label)
            grid.addWidget(group, i // 3, i % 3)
        return page

    # ---- Logging tab: start/stop -> Raw/Int CSV pair, matches documented behavior ----
    def _build_logging_tab(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        group = QGroupBox("Session Recorder")
        layout = QVBoxLayout(group)

        self.log_button = QPushButton("START LOGGING")
        self.log_button.setCheckable(True)
        self.log_button.setFixedWidth(220)
        self.log_button.toggled.connect(self._toggle_logging)
        layout.addWidget(self.log_button, alignment=Qt.AlignmentFlag.AlignLeft)

        self.log_status = QLabel("Idle — no session recording.")
        layout.addWidget(self.log_status)

        self.log_readout = QLabel(f"Writes to: {os.path.relpath(LOG_DIR)}/Raw_H-M-S.csv + Int_H-M-S.csv")
        self.log_readout.setStyleSheet("color: #6f7a71;")
        layout.addWidget(self.log_readout)
        layout.addStretch()

        outer.addWidget(group)
        outer.addStretch()
        return page

    def _toggle_logging(self, active: bool) -> None:
        self.logging_active = active
        if active:
            self.recorder = SessionRecorder()
            self._session_started_at = time.time()
            self.log_button.setText("STOP LOGGING")
            self.log_status.setText("Recording…")
        else:
            self.log_button.setText("START LOGGING")
            raw_path, interp_path = self.recorder.write_csv_pair(LOG_DIR, started_at=self._session_started_at)
            self.log_status.setText(f"Saved {os.path.basename(raw_path)} / {os.path.basename(interp_path)}")

    # ---- Poll loop ----
    def _tick(self) -> None:
        parsed = parse_line(self.source.next_line())
        if parsed is None:
            return
        name, value, ts = parsed
        self.state[name] = value
        if self.logging_active:
            self.recorder.record(name, value, ts)
            elapsed = time.time() - self._session_started_at
            self.log_status.setText(f"Recording… {len(self.recorder)} readings, {elapsed:.0f}s elapsed")

        widget = self.gauge_widgets.get(name)
        if widget is not None:
            hi = SENSOR_META[name]["range"][1]
            widget.load_svg(gauge_svg_for(name, value, hi))
            label = widget.parent().findChild(QLabel, f"value_{name}")
            if label is not None:
                label.setText(f"{value:.1f} {SENSOR_META[name]['unit']}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
