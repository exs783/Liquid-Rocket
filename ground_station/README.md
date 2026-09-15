# Ground Station

A single PyQt6 app merging what used to be two separate, never-integrated
prototypes in this repo:

- `main_v2.py` / `data_mainwindow.py` (PyQt5) — live sensor plots + CSV logging
- `GUI_Valve_Example.py` / `GUI_SVG_BUILT_IN_PYTHON.py` (PyQt6) — clickable P&ID valve controls

Those two were built on different, incompatible Qt bindings (PyQt5 vs PyQt6)
and shared no data model. This rebuilds both as one app, on PyQt6 throughout,
sharing one sensor/valve state.

## Run it

```
pip install -r requirements.txt
python main.py
```

No Teensy or serial hardware required — it runs against `FakeSensorSource`
(see below). Three tabs:

- **Controls** — the real P&ID (`assets/Rocket_P&ID_GUI1.svg`) for reference,
  plus working click-to-toggle valve/igniter controls.
- **Live Data** — one gauge per real sensor channel (7 pressure transducers,
  1 thermocouple, 1 load cell).
- **Logging** — start/stop a session; on stop, writes the documented
  `Raw_H-M-S.csv` (as-received, gaps between channels) and `Int_H-M-S.csv`
  (forward-filled) pair into `logs/`.

## What's real vs. simulated

- **Real**: the wire protocol (`sensors.py`'s `SENSOR_KEYS`/`parse_line`/
  `format_line` match the Teensy firmware in `../Teensy_Sketch_Flash_1.ino`
  and `../MAX31850_Temperature.ino` exactly — one line per reading,
  `<name>,<value>,<unix_timestamp>`), the P&ID diagram, and the CSV logging
  format.
- **Simulated**: `FakeSensorSource` (`sensors.py`) generates a random-walk
  reading per channel instead of reading a real Teensy over serial. Swapping
  in real hardware means writing a `SerialSensorSource` with the same
  `next_line() -> str` interface and passing it to `MainWindow(sensor_source=...)`
  in `main.py` — nothing else changes.
- **Valve control is UI-only.** The existing serial protocol only carries
  sensor *readings* — there's no command channel to actually drive a valve
  yet, so toggling MV-1/IGN-1 here only updates the on-screen state. Wiring
  real actuation needs a command protocol added to the firmware first.

## Tests

```
python -m pytest tests/ -q
# or, without pytest:
python tests/test_sensors.py
python tests/test_logging_utils.py
QT_QPA_PLATFORM=offscreen python tests/test_smoke.py   # headless GUI smoke test
```

## Layout

```
sensors.py         wire protocol + FakeSensorSource (no Qt dependency)
logging_utils.py   CSV session recorder (no Qt dependency)
svg_widgets.py      gauge/valve SVG drawing + clickable widget
main.py             MainWindow wiring the three tabs together
assets/             real P&ID/valve SVGs
```

The old loose scripts and zips at the repo root (`main_v2.py`,
`GUI_Valve_Example.py`, `GUI_SVG_BUILT_IN_PYTHON.py`, `Data_Page_GUI.zip`,
`GUI_Data_Page.zip`, ...) are left in place as history; `ground_station/`
supersedes them for actually running the app.
