"""Rule table: regex over panicString -> candidate fault.
Extend this file with your own repair experience (PRs welcome)."""
import re

# (pattern, fault, area, confidence 0-1, next steps)
RULES = [
    (r"Missing sensor\(s\):.*\b(TG0B|TG0V)\b", "Battery / battery flex",
     "hardware", 0.8, ["Test with a known-good battery", "Inspect battery connector"]),
    (r"Missing sensor\(s\):.*\b(Prs0|mic1|mic2)\b", "Charging port flex / mic / barometer",
     "hardware", 0.7, ["Swap charging flex", "Check for liquid damage near the port"]),
    (r"Missing sensor\(s\):.*\b(TP\w+|TS\w+)\b", "Temperature sensor line",
     "hardware", 0.5, ["Inspect the flex of the missing sensor", "Check the board"]),
    (r"userspace watchdog timeout", "Software issue (iOS or an app)",
     "software", 0.6, ["Update/restore iOS", "Check the service named in the log"]),
    (r"(ANS2|NVMe|NAND|apfs.*panic)", "Storage (NAND) problem",
     "hardware", 0.6, ["Try DFU restore", "If it repeats, suspect NAND"]),
    (r"(AOP|i2c|I2C).*(timeout|NMI|error)", "Board-level bus issue (i2c / AOP)",
     "hardware", 0.5, ["Disconnect flexes one by one", "Micro-soldering diagnosis"]),
    (r"SMC (PANIC|ASSERTION)", "Power management (SMC / PMIC)",
     "hardware", 0.6, ["Check for shorts on power lines", "Measure current draw"]),
    (r"thermal", "Thermal issue",
     "hardware", 0.4, ["Check sensors and battery", "Look for overheating"]),
]


def match_rules(info: dict) -> list:
    text = info.get("panicString", "")
    hits = [
        {"fault": f, "area": a, "confidence": c, "next_steps": s}
        for p, f, a, c, s in RULES if re.search(p, text, re.I)
    ]
    return sorted(hits, key=lambda r: -r["confidence"])
