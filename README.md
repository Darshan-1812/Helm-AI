# 🛡️ Agent Control Room

**The Reliability Layer for Autonomous AI Agents**

Full agent tracing, session recording & replay, cost intelligence, quality evaluation, and guardrails — in one open-source platform.

---

## ✨ Core Features

| Feature | Description |
|---------|------------|
| **🔄 Full Agent Trace** | Every LLM call, tool use, and agent step recorded with OTel-aligned semconv |
| **📼 Session Recording** | Visual trace timeline — like a "flight recorder" for AI agents |
| **💰 Cost Intelligence** | Per-agent, per-model cost tracking with spike detection |
| **✅ Quality Evaluation** | Hallucination, faithfulness, correctness scoring (Ragas/DeepEval ready) |
| **🛡️ Guardrails** | Cost limits, loop detection, latency budgets, quality gates |
| **🏢 Multi-Tenancy** | Built-in org isolation with API key authentication |

---

## 🏗️ Architecture

```
Your Agent    ──▶  SDK (@trace decorators)  ──▶  FastAPI Backend  ──▶  PostgreSQL
                                                       │
                                                  Redis + Dramatiq
                                                   (async workers)
                                                       │
                                              Next.js Dashboard  ◀── You
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2 |
| Database | PostgreSQL |
| Queue | Redis + Dramatiq |
| Frontend | Next.js 14 (App Router), Recharts |
| SDK | Python — `pip install agentcontrolroom` |
| Containers | Docker + docker-compose |

---

## 🚀 Quick Start

### 1. Clone & Configure

```bash
git clone <your-repo>
cd ai
cp .env.example .env
```

### 2. Start All Services

```bash
docker-compose up --build
```

This starts 5 services:
- **PostgreSQL** (port 5432)
- **Redis** (port 6379)
- **FastAPI Backend** (port 8000)
- **Dramatiq Worker**
- **Next.js Frontend** (port 3000)

### 3. Get Your API Key

Check the backend console output for:
```
🔑 Default org API key: acr-dev-xxxxx
```

### 4. Open the Dashboard

Visit **http://localhost:3000** and paste your API key.

### 5. Run the Demo Agent

```bash
# Set the API key from step 3
set ACR_API_KEY=acr-dev-xxxxx

# Run the demo
python demo/demo_agent.py
```

This generates 10 realistic agent runs with varying models, costs, and outcomes.

---

## 🐍 SDK Usage

### Basic Instrumentation

```python
from agentcontrolroom import trace, ACRClient

# Initialize
client = ACRClient(
    api_key="your-api-key",
    endpoint="http://localhost:8000"
)
trace.configure(client=client)

# Decorate your functions
@trace.agent("research-agent")
def my_agent(query: str):
    result = my_llm_call(query)
    data = my_tool(result)
    return synthesize(result, data)

@trace.llm_call("gpt-4o")
def my_llm_call(query: str):
    # your LLM call here
    return response

@trace.tool("web-search")
def my_tool(query: str):
    # your tool call here
    return results
```

### Context Manager Style

```python
with trace.span("custom-operation", kind="tool") as span:
    span.set_input("processing data...")
    result = do_work()
    span.set_output(result)
```

### Client-Side Guardrails

```python
from agentcontrolroom import Guardrails

guardrails = Guardrails(
    max_cost=5.0,         # Kill if >$5
    max_latency_ms=30000, # Alert if >30s
    max_loop_count=10,    # Block if >10 iterations
)

# Check during execution
guardrails.check_cost(current_cost)
guardrails.check_latency(elapsed_ms)
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/trace` | Send agent run traces |
| `GET` | `/api/v1/runs` | List runs (paginated, filterable) |
| `GET` | `/api/v1/runs/{id}` | Get run detail with spans |
| `GET` | `/api/v1/costs/summary` | Cost summary |
| `GET` | `/api/v1/costs/by-agent` | Cost breakdown by agent |
| `GET` | `/api/v1/costs/by-model` | Cost breakdown by model |
| `GET` | `/api/v1/evaluations` | List evaluations |
| `POST` | `/api/v1/evaluations/trigger` | Trigger evaluation |
| `GET/POST` | `/api/v1/guardrails/configs` | CRUD guardrail rules |
| `GET` | `/api/v1/guardrails/alerts` | List alerts |
| `GET` | `/health` | Health check |

All endpoints require `X-API-Key` header for authentication.

---

## 📁 Project Structure

```
ai/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes (ingest, runs, costs, evals, guardrails)
│   │   ├── models/       # SQLAlchemy ORM models (7 tables)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── workers/      # Dramatiq async workers (trace, eval)
│   │   ├── config.py     # Pydantic settings
│   │   ├── database.py   # Async SQLAlchemy setup
│   │   └── main.py       # FastAPI app entrypoint
│   ├── Dockerfile
│   └── pyproject.toml
├── sdk/
│   └── src/agentcontrolroom/
│       ├── tracer.py     # @trace.agent / @trace.tool / @trace.llm_call
│       ├── spans.py      # SpanData / RunData (OTel-aligned)
│       ├── client.py     # HTTP client with batching
│       ├── cost.py       # Cost calculator (25+ models)
│       ├── guardrails.py # Client-side guardrails
│       └── instruments/  # Auto-instrumentation stubs
├── frontend/
│   └── src/app/
│       ├── page.tsx          # Dashboard home
│       ├── runs/page.tsx     # Runs list
│       ├── runs/[id]/page.tsx # Trace detail / session recording
│       ├── costs/page.tsx    # Cost intelligence
│       ├── evaluations/      # Quality evaluation
│       └── guardrails/       # Guardrail rules & alerts
├── demo/
│   └── demo_agent.py    # Demo agent for seeding data
├── docker-compose.yml
└── .env.example
```

---

## 📄 License

MIT — Built for the AI agent ecosystem.
