import json

from app.parser import parse_panic, sanitize

PANIC = (
    "panic(cpu 4 caller 0xfffffff0): Missing sensor(s): TG0B\n"
    "panicked task 0xffff: 123 pages, 4 threads: pid 0: kernel_task\n"
)
IPS = json.dumps({"bug_type": "210", "os_version": "iPhone OS 17.5 (21F79)",
                  "timestamp": "2026-10-14 10:00:00.00 +0300"}) + "\n" + \
      json.dumps({"product": "iPhone12,1", "panicString": PANIC})


def test_parse_ips():
    info = parse_panic(IPS)
    assert info["product"] == "iPhone12,1"
    assert info["missing_sensors"] == "TG0B"
    assert info["panicked_task"] == "kernel_task"


def test_plain_text_fallback():
    assert parse_panic(PANIC)["missing_sensors"] == "TG0B"


def test_sanitize_udid():
    assert "<UDID>" in sanitize("id 00008030-001A2B3C4D5E6F70 end")
