# SCHOLARIS — Intelligent Academic Q&A Agent System

> A production-grade agentic AI application that routes academic queries to specialist agents using a LangGraph supervisor architecture.

---

## Project Overview

Scholaris accepts a natural-language academic question from the user, validates it through a security guardrail layer, and routes it via a supervisor agent to one of three specialist agents: **Math**, **Biology**, or **History**. Queries outside these three domains are explicitly rejected as out-of-scope.

---

## Project File Structure

```
scholaris/
├── app.py            # Streamlit frontend — user-facing UI
├── main.py           # FastAPI backend — REST API entry point
├── logic.py          # LangGraph agent pipeline — supervisor + 3 agents
├── guardrail.py      # Security layer — input validation and injection defence
├── .env              # Environment variables (OPENAI_API_KEY) — not committed to VCS
├── requirements.txt  # Python dependency list
└── README.md         # This document
```

---

## What Each File Does

### `app.py` — Streamlit Frontend
The user-facing interface. Renders a professional dark-academic UI with a text input for the query and a result card that displays the responding agent's label alongside the answer. It POSTs the query to the FastAPI backend and handles all response states (success, blocked, error, timeout).

### `main.py` — FastAPI Backend
Defines a single `POST /query` endpoint. It receives the query, passes it through `guardrail.py` for validation, then calls `logic.py` to invoke the agent pipeline. Returns a structured JSON response (`agent`, `answer`, `status`). Also exposes a `GET /health` liveness probe.

### `logic.py` — LangGraph Agent Logic
Contains three specialist agents built with `create_react_agent` (ReAct pattern), each equipped with a single domain-specific tool:
- **math_agent** — uses `solve_math` tool; shows full step-by-step workings
- **biology_agent** — uses `answer_biology` tool; provides scientific detail
- **history_agent** — uses `answer_history` tool; includes dates and context

A `create_supervisor` orchestrator reads the query and routes to the correct agent. Queries that do not match any of the three subjects are rejected with an `OUT_OF_SCOPE` response. All agents share a single `ChatOpenAI(gpt-4o-mini)` instance capped at 512 output tokens.

### `guardrail.py` — Security Layer
Validates every query *before* it reaches the LLM pipeline:
1. **Minimum length** — rejects inputs under 3 words
2. **Maximum length** — rejects inputs over 500 characters (~125 tokens)
3. **Prompt-injection scan** — checks for 15+ known injection phrases (jailbreak, system prompt leak, persona override, etc.) using compiled regex
4. **Character allowlist** — blocks raw control characters

### `.env` — Environment Variables
Stores the `OPENAI_API_KEY`. Never commit this file. Add `.env` to `.gitignore`.

### `requirements.txt` — Dependencies
Pins all required libraries with exact versions for reproducible installs.

---

## Workflow Architecture

```
User (Streamlit)
       │
       │  POST /query  {"query": "..."}
       ▼
FastAPI  main.py
       │
       ├─► guardrail.py  ── BLOCKED ──► 400 response to UI
       │         │
       │       SAFE
       │         │
       ▼
logic.py  run_query()
       │
       ▼
LangGraph Supervisor
       │
       ├─── Math subject?    ──► math_agent    ──► solve_math tool
       ├─── Biology subject? ──► biology_agent ──► answer_biology tool
       ├─── History subject? ──► history_agent ──► answer_history tool
       └─── Other subject?   ──► OUT_OF_SCOPE response
       │
       ▼
FastAPI returns QueryResponse  {"agent": "...", "answer": "...", "status": "success"}
       │
       ▼
Streamlit renders result card
```

---

## Setup & Running

### Configure environment variable (.env as a new file and write API key as works)
```bash
# Set OPENAI_API_KEY=sk-...
```

### Start the backend
```bash
uvicorn main:app --reload --port 8000
```

### Start the frontend 
```bash
streamlit run app.py
```

### Open in browser
Navigate to `http://localhost:8501`


---

## Supported Query Examples

| Subject | Example Query |
|---|---|
| Math | `Solve 3x² - 12 = 0 step by step` |
| Biology | `What is the role of mitochondria in a cell?` |
| History | `What were the main causes of World War I?` |
| Out of scope | `Explain Newton's second law` → ⛔ rejected |

---

## Security Considerations

- The guardrail runs **before** any LLM call — no tokens are spent on injected inputs.
- Pydantic field constraints in `main.py` provide a first-pass length guard before the guardrail even runs.
- The supervisor prompt explicitly instructs the model to respond with a sentinel string (`OUT_OF_SCOPE:`) for unsupported subjects — this is parsed and surfaced as a friendly UI message rather than exposing raw model output.
- The `.env` file must be excluded from version control (add to `.gitignore`).
