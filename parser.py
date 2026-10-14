"""Parse iPhone panic-full logs (.ips new format + old plain-text)."""
import json
import re

FIELDS = {
    "product": r'"product"\s*:\s*"([^"]+)"',
    "os_version": r'"os_version"\s*:\s*"([^"]+)"',
    "bug_type": r'"bug_type"\s*:\s*"([^"]+)"',
    "timestamp": r'"timestamp"\s*:\s*"([^"]+)"',
}


def parse_panic(raw: str) -> dict:
    info = {"panicString": "", "product": None, "os_version": None,
            "bug_type": None, "timestamp": None}

    # New .ips: first line = JSON header, rest = JSON body
    parts = raw.split("\n", 1)
    try:
        header = json.loads(parts[0])
        info["os_version"] = header.get("os_version")
        info["bug_type"] = header.get("bug_type")
        info["timestamp"] = header.get("timestamp")
        body = json.loads(parts[1]) if len(parts) > 1 else {}
        info["product"] = body.get("product")
        info["panicString"] = body.get("panicString", "")
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    # Fallback: regex over raw text
    if not info["panicString"]:
        m = re.search(r'"panicString"\s*:\s*"(.*?)"\s*[,}]', raw, re.S)
        info["panicString"] = (m.group(1) if m else raw).replace("\\n", "\n")
    for key, pat in FIELDS.items():
        if not info[key]:
            m = re.search(pat, raw)
            info[key] = m.group(1) if m else None

    s = info["panicString"]
    m = re.search(r"Missing sensor\(s\):\s*(.+)", s)
    info["missing_sensors"] = m.group(1).strip() if m else None
    m = re.search(r"panicked task.*?pid \d+: (\S+)", s)
    info["panicked_task"] = m.group(1) if m else None
    m = re.search(r"service:\s*(\w+)", s)
    info["service"] = m.group(1) if m else None
    return info


def sanitize(text: str) -> str:
    """Remove device identifiers before sending anything to an external AI."""
    text = re.sub(r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{16}\b", "<UDID>", text)
    text = re.sub(r"(?i)(serial(?:Number)?\W{1,4})[A-Z0-9]{8,14}", r"\1<SERIAL>", text)
    return text
