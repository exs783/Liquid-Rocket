"""Session CSV logging -- matches the raw + interpolated pair documented in
GUI_Data_Page.zip's readme.txt (Raw_H-M-S.csv / Int_H-M-S.csv), reimplemented
against the live sensors.SENSOR_KEYS protocol instead of main_v2.py's
PyQt5/Custom_Widgets-coupled version.
"""
from __future__ import annotations

import os
import time
from typing import Optional

import pandas as pd


class SessionRecorder:
    """Buffers (timestamp, channel, value) readings for one logging session
    and exports them as the documented raw/interpolated CSV pair. Import-only
    -- no Qt dependency, so it's unit-testable headless."""

    def __init__(self):
        self._rows: list[tuple[float, str, float]] = []

    def record(self, name: str, value: float, timestamp: float) -> None:
        self._rows.append((timestamp, name, value))

    def __len__(self) -> int:
        return len(self._rows)

    def raw_frame(self) -> pd.DataFrame:
        """One row per reading as it arrived: timestamp plus whichever single
        channel column had a value at that instant (others are NaN)."""
        if not self._rows:
            return pd.DataFrame(columns=["timestamp"])
        df = pd.DataFrame(self._rows, columns=["timestamp", "name", "value"])
        wide = df.pivot_table(index="timestamp", columns="name", values="value", aggfunc="last")
        wide = wide.reset_index().sort_values("timestamp")
        # Preserve first-seen channel order rather than pivot_table's alphabetical default.
        seen_order = list(dict.fromkeys(name for _, name, _ in self._rows))
        return wide[["timestamp", *seen_order]]

    def interpolated_frame(self) -> pd.DataFrame:
        """Same rows, but every channel holds its last known value at every
        timestamp instead of leaving gaps -- matches the documented
        "assumes a value received for a given data point remains the same
        until a new one is received" behavior, a forward-fill, not a
        numerical interpolation."""
        raw = self.raw_frame()
        if raw.empty:
            return raw
        channels = [c for c in raw.columns if c != "timestamp"]
        return raw.assign(**{c: raw[c].ffill() for c in channels})

    def write_csv_pair(self, out_dir: str, started_at: Optional[float] = None) -> tuple[str, str]:
        """Writes Raw_H-M-S.csv and Int_H-M-S.csv into out_dir, timestamped by
        when the session started (falls back to now)."""
        os.makedirs(out_dir, exist_ok=True)
        stamp = time.strftime("%H-%M-%S", time.localtime(started_at if started_at is not None else time.time()))
        raw_path = os.path.join(out_dir, f"Raw_{stamp}.csv")
        interp_path = os.path.join(out_dir, f"Int_{stamp}.csv")
        self.raw_frame().to_csv(raw_path, index=False)
        self.interpolated_frame().to_csv(interp_path, index=False)
        return raw_path, interp_path
