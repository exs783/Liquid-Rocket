"""Sensor protocol + data sources for the rocket ground-station GUI.

Wire format matches the real Teensy firmware (../Teensy_Sketch_Flash_1.ino,
../MAX31850_Temperature.ino) and the existing main2_test.py prototype exactly:
one line per reading, "<name>,<value>,<unix_timestamp>", e.g. "P3,42.5,1700000000.1".
Keeping FakeSensorSource emitting this same format means a future
SerialSensorSource (reading the real Teensy over USB) is a drop-in replacement
for FakeSensorSource everywhere in main.py -- nothing else has to change.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Optional

# Real channel set: 7 pressure transducers, 1 thermocouple (MAX31850), 1 load cell.
SENSOR_KEYS = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "T0", "L0"]

SENSOR_META = {
    "P0": {"label": "Pressure Transducer 0", "unit": "PSI", "range": (0.0, 200.0)},
    "P1": {"label": "Pressure Transducer 1", "unit": "PSI", "range": (0.0, 200.0)},
    "P2": {"label": "Pressure Transducer 2", "unit": "PSI", "range": (0.0, 200.0)},
    "P3": {"label": "Pressure Transducer 3", "unit": "PSI", "range": (0.0, 200.0)},
    "P4": {"label": "Pressure Transducer 4", "unit": "PSI", "range": (0.0, 200.0)},
    "P5": {"label": "Pressure Transducer 5", "unit": "PSI", "range": (0.0, 200.0)},
    "P6": {"label": "Pressure Transducer 6", "unit": "PSI", "range": (0.0, 200.0)},
    "T0": {"label": "Thermocouple 0", "unit": "°C", "range": (0.0, 100.0)},
    "L0": {"label": "Load Cell 0", "unit": "kg", "range": (0.0, 1000.0)},
}


def format_line(name: str, value: float, timestamp: float) -> str:
    return f"{name},{value},{timestamp}"


def parse_line(line: str) -> Optional[tuple[str, float, float]]:
    """Parse one wire-format line. Returns None for anything malformed or for
    an unrecognized sensor name, instead of raising -- a corrupted serial byte
    or a firmware typo should drop one reading, not crash the GUI."""
    parts = line.split(",")
    if len(parts) != 3:
        return None
    name, value_str, ts_str = parts
    if name not in SENSOR_META:
        return None
    try:
        return name, float(value_str), float(ts_str)
    except ValueError:
        return None


class FakeSensorSource:
    """Deterministic (given a seed) fake data source standing in for the real
    Teensy connection -- same wire format, so main.py's read loop doesn't know
    the difference. Each call to next_line() emits one reading for a randomly
    chosen channel, mirroring the real firmware's one-reading-per-line stream
    rather than a full-vector update every tick.

    Values random-walk within each channel's documented range (SENSOR_META)
    instead of jumping independently every call, so a live plot looks like a
    real noisy signal instead of white noise.
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._state = {key: (meta["range"][0] + meta["range"][1]) / 2 for key, meta in SENSOR_META.items()}

    def next_line(self) -> str:
        name = self._rng.choice(SENSOR_KEYS)
        lo, hi = SENSOR_META[name]["range"]
        step = (hi - lo) * 0.02
        value = self._state[name] + self._rng.uniform(-step, step)
        value = max(lo, min(hi, value))
        self._state[name] = value
        return format_line(name, round(value, 2), round(time.time(), 3))
