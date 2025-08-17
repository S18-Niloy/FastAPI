# Softvence Omega — AI Task 

A single-route FastAPI app that handles multiple AI tasks, includes optional JWT auth, integrates a minimal MCP server/client for tool calling, and ships with a basic trading backtest utility. Tested locally on macOS.

## Features
- **One route:** `POST /ai-task` with `task` in body: `qa`, `latest`, `image`, `platform_content`
- **Agent Q&A:** Calls OpenAI chat model (`DEFAULT_MODEL`)
- **Latest answer:** Stores Q&A/image/platform outputs to SQLite and fetches the latest
- **Image generation:** Returns base64-encoded PNG using OpenAI Images (`IMAGE_MODEL`)
- **Platform content:** Facebook, LinkedIn, Twitter/X, Instagram, TikTok, Reddit, Medium styles
- **JWT auth (optional but implemented):** Indefinite token (no exp); use `/login` to obtain
- **MCP integration:** Minimal local MCP server with an `upper(text)` demo tool + client
- **Backtest kit:** Simple SMA crossover script that outputs CSV, chart, and metrics

---

## (macOS + VS Code)

### 1) Clone 
```bash
cd softvence-ai-task
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# At .env set OPENAI_API_KEY=...
```

### 2) Run the API
```bash
./run.sh
# or:
uvicorn app.main:app --reload --port 8000
```
Open http://127.0.0.1:8000/docs

### 3) Auth
1. Hit `POST /login` with any username/password (demo). Copy `access_token`.
2. For `POST /ai-task` add header: `Authorization: Bearer <token>`.

### 4) Example requests
**Q&A**
```bash
curl -X POST http://127.0.0.1:8000/ai-task   -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json"   -d '{"task":"qa","prompt":"What is MCP in one sentence?"}'
```

**Latest**
```bash
curl -X POST http://127.0.0.1:8000/ai-task   -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json"   -d '{"task":"latest"}'
```

**Image**
```bash
curl -X POST http://127.0.0.1:8000/ai-task   -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json"   -d '{"task":"image","prompt":"A minimalist robot mascot, vector style"}'
```
Response includes `image_b64` — render in a browser or save to file.

**Platform content**
```bash
curl -X POST http://127.0.0.1:8000/ai-task   -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json"   -d '{"task":"platform_content","platform":"linkedin","prompt":"Announce our new AI trading API beta"}'
```

---

## MCP Integration 

This repo includes a tiny MCP server and client using the official Python SDK.

- **Server:** `app/mcp_server.py` exposes a single tool `upper(text:str)`.
- **Client:** `app/mcp_client.py` connects over stdio and calls `upper`.
- The FastAPI **Q&A** path will *attempt* to call the MCP tool and prepend a hint.

---



## Folder structure
```
app/
  auth.py          # JWT helpers
  db.py            # SQLite models + init
  main.py          # FastAPI entry — single /ai-task route
  mcp_client.py    # Minimal MCP client
  mcp_server.py    # Minimal MCP server with 'upper' tool
  schemas.py       # Pydantic models
backtest/
  sma_backtest.py  # SMA strategy CSV, chart, metrics
tests/
  test_api.py
Dockerfile
render.yaml
requirements.txt
run.sh
.env.example
```

# Short Write-Up: Approach, Risk Controls, and Assumptions

## Approach
- **Single-route API design:** One endpoint `POST /ai-task` with a typed `task` field (`qa`, `latest`, `image`, `platform_content`). This keeps the client contract simple and extensible.
- **Framework & structure:** FastAPI with Pydantic v2 models for I/O validation, SQLAlchemy (async) for persistence, and a small, readable module layout (`app/`).
- **Auth:** Optional JWT via `/login`. Tokens include `sub` and `iat` (no expiry by default to match the spec); middleware enforces `Authorization: Bearer <token>`.
- **Q&A & content generation:** OpenAI Chat models for `qa` and `platform_content`. Platform output uses a style map (LinkedIn, Facebook, X/Twitter, Instagram, TikTok, Reddit, Medium) to tailor tone/length.
- **Image generation:** OpenAI Images; returns **Base64** (portable by default). Trivially swappable to URL output by persisting images to `/static`.
- **State & “latest”:** All successful `qa`, `image`, and `platform_content` results are saved to SQLite; `latest` returns the most recent row.
- **MCP integration (extensibility):** Minimal MCP server with a demo `upper(text)` tool and a client; `qa` path attempts a tool call first to show how external tools can be composed.
- **Ops:** Uvicorn for local dev, Dockerfile for container runs, `render.yaml` for a free Render deployment. Tests and a backtest utility are included.

## Backtest Method (SMA Crossover)
- **Data & transforms:** Daily OHLCV (via `yfinance` locally). Compute `SMA50` and `SMA200`; drop initial warm-up rows.
- **Signal:** Long when `SMA50 > SMA200`, flat otherwise. Apply **next-bar execution** (`signal.shift(1)`) to avoid look-ahead.
- **Returns & equity:** Daily returns = `pct_change`; strategy returns = `ret * shifted_signal`; cumulative equity = product of `(1 + strategy)`.
- **Metrics:** CAGR (252 trading days), annualized volatility, and Sharpe (no risk-free rate, simple mean/std formulation). CSV + PNG equity curve + JSON metrics are produced for reproducibility.

## Risk Controls
- **Look-ahead prevention:** Signals lag by one bar (`shift(1)`).
- **Warm-up handling:** Drop rows until both SMAs are defined to avoid biased early signals.
- **Deterministic artifacts:** Persist CSV, chart, and metrics to allow audit and re-calculation.
- **Separation of concerns:** Strategy logic is pure; no trading-engine side effects beyond artifact writes (easy to unit-test).
- **Graceful failure paths:** Data gaps handled by `dropna`; runtime errors surface clearly.

## Assumptions & Limitations
- **Frictionless markets:** No commissions, fees, or slippage; fills at close. (Can be added by subtracting a cost whenever `position` changes.)
- **Availability & liquidity:** Assumes you can trade desired size without impact or partial fills.
- **Data quality:** Yahoo data is sufficient for demo purposes; production should use a vetted vendor and corporate-action checks.
- **Risk-free rate:** Sharpe uses 0% RF for simplicity; can be adjusted.
- **JWT expiry:** Tokens are indefinite per spec preference; production should add `exp`, rotation, and revocation lists if needed.
- **Model outputs:** LLM content may vary run-to-run; system prompts and temperatures are chosen for consistency but not determinism.

## Reproducibility Notes
- **API:** `uvicorn app.main:app --reload --port 8000`; use `/docs` for interactive testing.
- **Backtest:** `python backtest/sma_backtest.py AAPL` (writes CSV/PNG/JSON under `backtest/results/`).
- **Environment:** Pin versions in `requirements.txt`; `.env` holds `OPENAI_API_KEY`, `JWT_SECRET`.

## Potential Improvements
- Add **transaction costs** and **position sizing** (vol targeting).
- Enforce **JWT expiration** and refresh flow.
- Serve images from `/static` and return **URLs** by default.
- CI pipeline (lint, type-check, tests) + container scan.
- Extend MCP tools for data retrieval, compliance checks, or custom retrieval-augmented generation.

## Link
https://softvence-ai-task-gbsh.onrender.com/docs
