from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.ai import ask_ai, build_payload  # noqa: E402
from app.classifier import extract_signals  # noqa: E402
from app.devices import device_name  # noqa: E402
from app.engine import links_for, rank, verdict  # noqa: E402
from app.knowledge import SIGNATURES  # noqa: E402
from app.parser import parse_panic, sanitize  # noqa: E402
from app.store import Store  # noqa: E402

MAX_BYTES = 2 * 1024 * 1024
STATIC = Path(__file__).resolve().parent.parent / "static"
app = FastAPI(title="iPhone Panic Analyzer")
store = Store()


class Confirm(BaseModel):
    signature_id: str
    notes: str = ""


@app.post("/api/analyze")
async def analyze(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None)):
    if file is not None:
        raw = await file.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise HTTPException(413, "File too large (max 2 MB)")
    elif text:
        raw = text.encode("utf-8")[:MAX_BYTES]
    else:
        raise HTTPException(400, "Upload a file or paste the log text")
    info = parse_panic(raw.decode("utf-8", errors="ignore"))
    if not info["panicString"].strip():
        raise HTTPException(422, "No panic data found")
    signals = extract_signals(info["panicString"])
    ranked = rank(info, store.stats())
    ai = await ask_ai(build_payload(info, signals, ranked, sanitize))
    name = device_name(info["product"])
    return {
        "case_id": store.save(name, info["os_version"], ranked),
        "device": {"name": name, "model": info["product"], "ios": info["os_version"],
                   "timestamp": info["timestamp"]},
        "signals": signals, "verdict": verdict(ranked, ai), "ranked": ranked, "ai": ai,
        "links": links_for(info, ranked[0]),
    }


@app.post("/api/cases/{case_id}/confirm")
def confirm(case_id: int, body: Confirm):
    store.confirm(case_id, body.signature_id, body.notes)
    return {"ok": True}


@app.get("/api/history")
def history():
    return store.history()


@app.get("/api/signatures")
def signatures():
    return [{"id": s["id"], "title": s["title"]} for s in SIGNATURES]


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
