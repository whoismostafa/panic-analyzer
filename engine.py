"""Scoring engine: signatures -> ranked candidates with evidence, then a final verdict."""
import re
from urllib.parse import quote_plus

from app.devices import device_name
from app.knowledge import SIGNATURES

LEVELS = ["Low", "Medium", "High"]
UNKNOWN = dict(id="unknown", title="No known signature matched", area="unknown", component="Unknown",
               base=0.2, patterns=[], steps=["Clean DFU restore (no backup) to separate software from hardware",
                                              "Collect more panic logs and compare the repeating pattern"])


def _line_of(text: str, pos: int) -> str:
    s = text.rfind("\n", 0, pos) + 1
    e = text.find("\n", pos)
    return text[s: len(text) if e == -1 else e].strip()[:180]


def rank(info: dict, stats: dict | None = None) -> list:
    text, stats, cands = info.get("panicString", ""), stats or {}, []
    for sig in SIGNATURES:
        ev = []
        for p in sig["patterns"]:
            m = re.search(p, text, re.I)
            if m:
                line = _line_of(text, m.start())
                if line not in ev:
                    ev.append(line)
        if not ev:
            continue
        score = min(0.95, sig["base"] + 0.05 * (len(ev) - 1))
        hist = None
        s = stats.get(sig["id"])
        if s and s["n"] >= 3:  # calibrate with the user's own confirmed cases
            acc = s["correct"] / s["n"]
            score = round(0.7 * score + 0.3 * acc, 3)
            hist = {"cases": s["n"], "correct": s["correct"]}
        cands.append({**{k: sig[k] for k in ("id", "title", "area", "component", "steps")},
                      "score": round(score, 3), "evidence": ev, "history": hist})
    if not cands:
        cands = [{**{k: UNKNOWN[k] for k in ("id", "title", "area", "component", "steps")},
                  "score": UNKNOWN["base"], "evidence": [], "history": None}]
    cands.sort(key=lambda c: -c["score"])
    total = sum(c["score"] for c in cands) or 1
    for i, c in enumerate(cands, 1):
        c["rank"], c["share"] = i, round(100 * c["score"] / total)
    return cands


def _label(top: float, margin: float) -> str:
    if top >= 0.75 and margin >= 0.2:
        return "High"
    return "Medium" if top >= 0.5 else "Low"


def verdict(ranked: list, ai: dict) -> dict:
    top = ranked[0]
    margin = top["score"] - (ranked[1]["score"] if len(ranked) > 1 else 0)
    idx = LEVELS.index(_label(top["score"], margin))
    if not ai.get("available"):
        agreement = "unavailable"
    elif ai.get("likely_cause_id") == top["id"]:
        agreement = "agree"
        idx = min(2, idx + 1) if top["score"] >= 0.5 else idx
    else:
        agreement = "disagree"
        idx = max(0, idx - 1)
    return {"fault": top["title"], "component": top["component"], "area": top["area"],
            "confidence": LEVELS[idx], "agreement": agreement}


def links_for(info: dict, top: dict) -> list:
    q = " ".join(filter(None, [device_name(info.get("product")), "panic",
                               info.get("missing_sensors") or top["title"]]))
    qq = quote_plus(q)
    return [{"label": "Google", "url": f"https://www.google.com/search?q={qq}"},
            {"label": "iFixit", "url": f"https://www.ifixit.com/Search?query={qq}"}]
