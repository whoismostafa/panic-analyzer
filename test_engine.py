import tempfile
from pathlib import Path

from app.classifier import extract_signals
from app.engine import rank, verdict
from app.store import Store


def info(s):
    return {"panicString": s}


def test_battery_ranks_first():
    r = rank(info("panic: Missing sensor(s): TG0B"))
    assert r[0]["id"] == "sensor_battery" and r[0]["share"] > 50


def test_thermal_vs_software_watchdog():
    t = "userspace watchdog timeout: no successful checkins from thermalmonitord in 120 seconds"
    s = "userspace watchdog timeout: no successful checkins from backboardd in 120 seconds"
    assert rank(info(t))[0]["id"] == "wd_thermal"
    assert rank(info(s))[0]["id"] == "wd_software"
    assert extract_signals(t)["watchdog_seconds"] == 120


def test_unlisted_sensor_and_unknown():
    assert rank(info("Missing sensor(s): ZZ9X"))[0]["id"] == "sensor_other"
    assert rank(info("nothing known here"))[0]["id"] == "unknown"


def test_verdict_agreement():
    r = rank(info("Missing sensor(s): TG0B"))
    agree = verdict(r, {"available": True, "likely_cause_id": "sensor_battery"})
    dis = verdict(r, {"available": True, "likely_cause_id": "nand"})
    assert agree["agreement"] == "agree" and dis["agreement"] == "disagree"
    assert agree["confidence"] == "High" and dis["confidence"] == "Medium"


def test_store_calibration():
    with tempfile.TemporaryDirectory() as d:
        st = Store(Path(d) / "c.db")
        r = rank(info("Missing sensor(s): TG0B"))
        for _ in range(3):
            st.confirm(st.save("iPhone 11", "17.5", r), "sensor_charge_flex")
        stats = st.stats()
        assert stats["sensor_battery"] == {"n": 3, "correct": 0}
        assert rank(info("Missing sensor(s): TG0B"), stats)[0]["score"] < r[0]["score"]
