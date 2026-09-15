"""Self-check for sensors.py. Run: python -m pytest ground_station/tests -q
(or, with no pytest installed: python ground_station/tests/test_sensors.py)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sensors import SENSOR_KEYS, SENSOR_META, parse_line, format_line, FakeSensorSource


def test_sensor_keys_match_real_teensy_protocol():
    # Real firmware (Teensy_Sketch_Flash_1.ino / MAX31850_Temperature.ino) and the
    # existing main2_test.py prototype both send exactly these 9 channel names --
    # a fake source that drifts from this list can't be swapped for the real one later.
    assert SENSOR_KEYS == ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "T0", "L0"]
    assert set(SENSOR_META.keys()) == set(SENSOR_KEYS)


def test_format_and_parse_round_trip():
    line = format_line("P3", 42.5, 1700000000.1)
    assert line == "P3,42.5,1700000000.1"
    name, value, ts = parse_line(line)
    assert name == "P3" and value == 42.5 and ts == 1700000000.1


def test_parse_line_rejects_malformed_input():
    for bad in ["", "P3,42.5", "P3", "not,a,number", "P3,,1700000000.1"]:
        assert parse_line(bad) is None, f"expected None for malformed line {bad!r}"


def test_parse_line_rejects_unknown_sensor_name():
    # A real Teensy firmware bug (typo'd channel name) shouldn't crash the GUI --
    # it should be dropped like any other malformed packet.
    assert parse_line("Q9,1.0,1700000000.1") is None


def test_fake_source_emits_only_known_sensors_in_range():
    src = FakeSensorSource(seed=1)
    seen = set()
    for _ in range(500):
        line = src.next_line()
        parsed = parse_line(line)
        assert parsed is not None, f"FakeSensorSource produced an unparseable line: {line!r}"
        name, value, _ts = parsed
        seen.add(name)
        lo, hi = SENSOR_META[name]["range"]
        assert lo <= value <= hi, f"{name}={value} outside documented range [{lo}, {hi}]"
    assert seen == set(SENSOR_KEYS), "500 samples should have touched every channel at least once"


def test_fake_source_is_deterministic_for_a_given_seed():
    a = FakeSensorSource(seed=7)
    b = FakeSensorSource(seed=7)
    lines_a = [a.next_line() for _ in range(20)]
    lines_b = [b.next_line() for _ in range(20)]
    assert lines_a == lines_b, "same seed should reproduce the same sequence for repeatable demos/tests"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
