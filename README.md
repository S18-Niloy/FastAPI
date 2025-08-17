# Softvence Omega — AI Task (FastAPI + MCP + Backtest)

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

> ⚠️ You need an **OpenAI API key** to use the AI features. Put it in `.env`.

---

## Quick Start (macOS + VS Code)

### 1) Clone / unzip
- Download the ZIP from ChatGPT, unzip it, then in Terminal:
```bash
cd softvence-ai-task
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set OPENAI_API_KEY=...
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

## MCP Integration (minimal demo)

This repo includes a tiny MCP server and client using the official Python SDK.

- **Server:** `app/mcp_server.py` exposes a single tool `upper(text:str)`.
- **Client:** `app/mcp_client.py` connects over stdio and calls `upper`.
- The FastAPI **Q&A** path will *attempt* to call the MCP tool and prepend a hint.

Run the server manually (optional):
```bash
python -m app.mcp_server
```
Then, in another terminal:
```bash
python -m app.mcp_client
```

> Docs you may find helpful:
> - Official Python SDK: https://github.com/modelcontextprotocol/python-sdk
> - Client quickstart: https://modelcontextprotocol.io/quickstart/client

---

## Backtest (bonus deliverable)

A simple SMA crossover example that outputs CSV, a PNG chart, and metrics.
```bash
python backtest/sma_backtest.py AAPL
# outputs to backtest/results/
```

---

## Deploy (free tier hints)

- **Render:** Use `render.yaml` as a starting point (Free Web Service). Set `OPENAI_API_KEY` and `JWT_SECRET` in the dashboard.
- **Docker:** `docker build -t softvence-ai-task . && docker run -p 8000:8000 softvence-ai-task`

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

## Notes / Assumptions
- JWT has **no expiration** to match the spec wording; rotate secrets if needed.
- Image endpoint returns **Base64** for portability. You may host URLs if you prefer.
- MCP is included as a **minimal, working demo** (stdio transport). Swap in your own tools as needed.
- If you prefer not to use OpenAI, you can replace the client calls with other providers.
