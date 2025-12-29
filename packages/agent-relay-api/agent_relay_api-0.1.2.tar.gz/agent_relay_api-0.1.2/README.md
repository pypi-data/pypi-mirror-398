# AgentRelay Website

Enterprise and paid version of the **agentRelay** library: a full-stack platform for tracing, replaying, and debugging AI agent workflows.

AgentRelay combines:
- A Python SDK for deterministic tracing and replay
- A FastAPI backend for ingestion, auth, billing, and realtime streaming
- A React UI for dashboards, runs, and team workflows

---

## ✨ Highlights

### 1) Observability for Agent Runs
Capture run metadata, tool calls, and timing details to understand what your agents did and why.

**Capabilities**
- Run ingestion API for tools and agent events
- Structured storage of runs + tool calls
- Real-time streaming for live dashboards

### 2) Deterministic Replay
Re-execute agent workflows deterministically using recorded tool calls.

**Capabilities**
- SDK-based tracing and replay
- Deterministic replay using stored tool-call history
- Useful for debugging, regression testing, and CI

### 3) Resume Mode + Budget Caps
Resume partially completed runs and stop execution once a budget ceiling is reached.

**Capabilities**
- Resume a prior `run_id` and skip completed tool calls
- Budget caps enforced per session with optional compensations

### 4) LLM Cost Accounting
Wrap LLM provider calls to record token usage and cost per step.

**Capabilities**
- OpenAI, Anthropic, and Ollama wrappers
- Step-level and run-level cost totals

### 5) Secure, Multi-Project Access
Built for teams and production deployments.

**Capabilities**
- Project-based access control
- Role-based API keys (viewer/writer/admin)
- OAuth providers + email/password auth

### 6) Production Billing Foundation
Stripe-powered billing endpoints with checkout and portal sessions.

---

## 🧭 Architecture

```
agent_relay/        # Python SDK (trace + replay)
backend/            # FastAPI backend (auth, billing, ingest)
ui/                 # React dashboard
```

---

## 🚀 Quick Start

### 1) Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MONGO_URI="mongodb://localhost:27017/agentrelay"
export JWT_SECRET_KEY="<secure-value>"
export SESSION_SECRET_KEY="<secure-value>"
export FRONTEND_URL="http://localhost:5173"

uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 2) Frontend (React)

```bash
cd ui
npm install
npm run dev
```

### 3) SDK usage

```python
from agent_relay.runtime import AgentRuntime
from agent_relay.llm import wrap_openai_call

runtime = AgentRuntime.from_conection_string("sqlite:///agent_relay.db")

def my_tool(x: int) -> int:
    return x + 1

runtime.register_tool("my_tool", my_tool)

with runtime.agent_session("example") as session:
    result = my_tool(2)
    session.set_output({"result": result})

# Resume a run and enforce a budget cap
with runtime.resume_session("example", run_id="<existing-run-id>", budget_limit=1.50) as session:
    result = my_tool(5)
    session.set_output({"result": result})

# Export a run to a file and replay locally
runtime.export_run_to_file("<run-id>", "./run.json")
runtime.replay_run_from_file("example", "./run.json", lambda: my_tool(3))

# Wrap an OpenAI call to capture usage and spend
response = wrap_openai_call(
    model="gpt-4o",
    call=lambda: client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "hi"}],
    ),
    input_cost_per_1k=0.005,
    output_cost_per_1k=0.015,
)
```

---

## 🔑 Environment Variables

### Backend
- `MONGO_URI` – MongoDB connection string
- `JWT_SECRET_KEY` – JWT signing key
- `SESSION_SECRET_KEY` – Cookie session key
- `FRONTEND_URL` – Allowed CORS origin


---

## 📜 License

See `LICENSE.txt`.
