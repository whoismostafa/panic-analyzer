"""SQLite history of analyses + confirmed outcomes (raw logs are NOT stored)."""
import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, path=None):
        self.path = Path(path or os.getenv("PANIC_DB", "data/cases.db"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._run("""CREATE TABLE IF NOT EXISTS cases(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, device TEXT, os_version TEXT,
            top_id TEXT, top_title TEXT, matched TEXT, confirmed_id TEXT, notes TEXT)""")

    def _run(self, sql, args=(), fetch=False):
        with closing(sqlite3.connect(self.path)) as c:
            c.row_factory = sqlite3.Row
            cur = c.execute(sql, args)
            rows = cur.fetchall() if fetch else None
            c.commit()
            return rows if fetch else cur.lastrowid

    def save(self, device, os_version, ranked) -> int:
        return self._run(
            "INSERT INTO cases(created,device,os_version,top_id,top_title,matched) VALUES(?,?,?,?,?,?)",
            (time.strftime("%Y-%m-%d %H:%M"), device, os_version, ranked[0]["id"], ranked[0]["title"],
             json.dumps([c["id"] for c in ranked])))

    def confirm(self, case_id: int, signature_id: str, notes: str = "") -> None:
        self._run("UPDATE cases SET confirmed_id=?, notes=? WHERE id=?", (signature_id, notes[:500], case_id))

    def history(self, limit=30) -> list:
        rows = self._run("SELECT id,created,device,top_title,confirmed_id FROM cases ORDER BY id DESC LIMIT ?",
                         (limit,), fetch=True)
        return [dict(r) for r in rows]

    def stats(self) -> dict:
        out = {}
        for r in self._run("SELECT matched, confirmed_id FROM cases WHERE confirmed_id IS NOT NULL", fetch=True):
            for sid in json.loads(r["matched"]):
                s = out.setdefault(sid, {"n": 0, "correct": 0})
                s["n"] += 1
                s["correct"] += sid == r["confirmed_id"]
        return out
