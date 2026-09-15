import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logging_utils import SessionRecorder


def test_recorder_accumulates_raw_readings_per_channel():
    rec = SessionRecorder()
    rec.record("P0", 10.0, 100.0)
    rec.record("T0", 22.5, 100.2)
    rec.record("P0", 11.0, 100.4)
    raw = rec.raw_frame()
    assert list(raw.columns) == ["timestamp", "P0", "T0"]
    assert raw["P0"].dropna().tolist() == [10.0, 11.0]
    assert raw["T0"].dropna().tolist() == [22.5]


def test_interpolated_frame_forward_fills_between_readings():
    # Real sensors don't all report on the same tick -- the documented
    # "Int_H-M-S.csv" holds a value steady until a new reading replaces it
    # (see GUI_Data_Page.zip's readme.txt), never interpolating numerically.
    rec = SessionRecorder()
    rec.record("P0", 10.0, 0.0)
    rec.record("T0", 20.0, 0.0)
    rec.record("P0", 12.0, 1.0)
    interp = rec.interpolated_frame()
    row_at_1 = interp.loc[interp["timestamp"] == 1.0].iloc[0]
    assert row_at_1["P0"] == 12.0
    assert row_at_1["T0"] == 20.0, "T0 has no new reading at t=1 -- should hold its last value"


def test_empty_session_produces_empty_frames_not_an_error():
    rec = SessionRecorder()
    assert rec.raw_frame().empty
    assert rec.interpolated_frame().empty


def test_write_csv_pair_creates_both_files(tmp_path=None):
    import tempfile

    rec = SessionRecorder()
    rec.record("P0", 5.0, 0.0)
    rec.record("P0", 6.0, 1.0)
    with tempfile.TemporaryDirectory() as d:
        raw_path, interp_path = rec.write_csv_pair(d, started_at=1700000000.0)
        assert os.path.exists(raw_path)
        assert os.path.exists(interp_path)
        assert "Raw_" in os.path.basename(raw_path)
        assert "Int_" in os.path.basename(interp_path)


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
