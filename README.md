# iPhone Panic Analyzer

Analyze iPhone `panic-full` logs and get a **ranked list of likely faults with evidence**. The tool combines a local signature engine, optional AI verification with live web search, and a feedback loop that calibrates scores from your own confirmed repairs.

> **Disclaimer:** a panic log narrows down a fault; it never proves it. Always verify on the bench. Built-in scores are starting estimates, not ground truth.

## Features

- Parses new `.ips` logs and old plain-text panic logs (upload or paste)
- Extracts signals: panic type, missing sensors, watchdog service/timeout, kernel extensions
- Ranked candidates with score, share %, matching log lines as **evidence**, and next-check steps
- Separates hardware vs software causes (e.g. `thermalmonitord` vs app watchdog timeouts)
- Optional **AI verification** (Claude API) with **web search** for external sources, listed in the UI
- Final verdict = rules ranking + AI agreement (agreement raises confidence, disagreement lowers it)
- **Learns from your cases**: confirm the real fault after a repair and future scores are calibrated
- History (SQLite), print/PDF report, English and Arabic UI
- Works fully offline in rules-only mode (no API key needed)

## Requirements

- Python 3.10+
- (Optional) an [Anthropic API key](https://console.anthropic.com/) for AI verification and web search

## Installation

```bash
git clone https://github.com/whoismostafa/panic-analyzer.git
cd panic-analyzer

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
```

Edit `.env` and set `ANTHROPIC_API_KEY` (optional).

### Run

```bash
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

### Docker

```bash
docker build -t panic-analyzer .
docker run -p 8000:8000 --env-file .env -v "$(pwd)/data:/srv/data" panic-analyzer
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | _(empty)_ | Enables AI verification. Empty = rules-only mode |
| `ANTHROPIC_MODEL` | `claude-sonnet-5-5` | Model used for verification |
| `ENABLE_WEB_SEARCH` | `true` | Let the AI search the web (falls back automatically if unavailable) |
| `PANIC_DB` | `data/cases.db` | SQLite history path |

## Usage

### 1. Get the panic log from the iPhone

1. Open **Settings → Privacy & Security → Analytics & Improvements → Analytics Data**.
2. Find entries starting with `panic-full` and open the latest one.
3. Tap the share button and send it to your computer (AirDrop, email, Files).

If the list is empty, make sure **Share iPhone Analytics** is enabled.

### 2. Analyze

1. Open the web UI, then upload the file or paste its text.
2. Click **Analyze**.
3. Read the result:
   - **Verdict**: top fault, confidence (Low / Medium / High) and whether the AI agrees.
   - **Ranked faults**: each with score, evidence lines from the log, and next steps.
   - **AI verification**: alternatives and the sources consulted.
   - **Quick search**: Google / iFixit links prefilled with the model and sensor.
4. After the repair, use **Confirm the actual fault** so the engine calibrates itself.

### 3. API

```bash
curl -F "file=@panic-full-2026-10-14.ips" http://127.0.0.1:8000/api/analyze
```

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/analyze` | Form field `file` or `text`; returns verdict, ranked faults, AI result, links |
| POST | `/api/cases/{id}/confirm` | JSON `{"signature_id": "...", "notes": "..."}` |
| GET | `/api/history` | Recent analyses |
| GET | `/api/signatures` | Known signature ids and titles |

## How it works

```
upload/paste → parser → classifier → engine (knowledge.py) → ranked candidates
                                              ↓
                        sanitized summary → AI (+ web search) → verdict
                                              ↓
                                SQLite history ← confirmed fault (calibration)
```

## Project structure

```
app/
  parser.py       .ips / text parsing, identifier sanitizing
  classifier.py   signal extraction
  knowledge.py    signature database (extend this)
  engine.py       scoring, ranking, verdict, external links
  ai.py           AI verification + web search
  store.py        SQLite history and calibration stats
  devices.py      model identifier → device name
  main.py         FastAPI app
static/index.html Web UI (EN / AR)
tests/            pytest suite
```

## Extending the knowledge base

Add an entry to `SIGNATURES` in `app/knowledge.py`:

```python
dict(id="my_rule", title="Description of the fault", area="hardware", component="Part",
     base=0.6, patterns=[r"regex matching the panic string"],
     steps=["What to check next"])
```

Then add a test in `tests/test_engine.py`.

## Testing

```bash
pytest
```

## Privacy

- Device identifiers (UDID, serial) are stripped before anything is sent to an external service.
- Only a short summary and excerpt are sent, never the full log. Raw logs are not stored.
- Keep your API key server-side and out of version control (`.env` is git-ignored).
- Web search results are treated as untrusted data.
- Never commit real customer logs.

## Contributing

Issues and pull requests are welcome, especially new signatures backed by real confirmed cases.

## License

MIT, see [LICENSE](LICENSE).
