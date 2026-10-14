"""Extract structured signals from a panic string."""
import re

TYPES = [
    (r"Missing sensor\(s\)", "Missing sensor"),
    (r"userspace watchdog timeout", "Userspace watchdog"),
    (r"Kernel data abort", "Kernel data abort"),
    (r"SMC (PANIC|ASSERTION)|Unexpected SMC", "SMC panic"),
    (r"\bAOP\b|NMI", "AOP / NMI"),
    (r"\bANS2?\b|NVMe", "Storage (ANS/NVMe)"),
    (r"zone[ _]map|zalloc", "Memory"),
]


def extract_signals(s: str) -> dict:
    m = re.search(r"Missing sensor\(s\):\s*([^\n]+)", s)
    sensors = [x for x in re.split(r"[,\s]+", m.group(1).strip()) if x] if m else []
    wd = re.search(r"no successful checkins from (\w+)[^\n]*?in (\d+) seconds", s)
    ptype = next((label for pat, label in TYPES if re.search(pat, s, re.I)), "Unclassified")
    kexts = list(dict.fromkeys(re.findall(r"com\.apple\.[\w.]+", s)))[:8]
    return {
        "panic_type": ptype,
        "missing_sensors_list": sensors,
        "watchdog_service": wd.group(1) if wd else None,
        "watchdog_seconds": int(wd.group(2)) if wd else None,
        "kexts": kexts,
    }
