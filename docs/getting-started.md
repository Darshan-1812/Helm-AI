# Getting Started with Agent Control Room

## Prerequisites

- Docker & Docker Compose
- Python 3.10+ (for SDK and demo agent)
- Node.js 18+ (only if running frontend outside Docker)

## Quick Start

### 1. Clone & Configure

```bash
git clone <your-repo-url>
cd ai
cp .env.example .env
```

### 2. Start All Services

```bash
docker-compose up --build
```

This starts:
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Queue broker |
| FastAPI | 8000 | Backend API |
| Dramatiq Worker | — | Async processing |
| Next.js | 3000 | Dashboard |

### 3. Get Your API Key

Check the **backend** container logs for:
```
🔑 Default org API key: acr-dev-xxxxx
```

### 4. Seed Demo Data

```bash
# Set the API key
set ACR_API_KEY=acr-dev-xxxxx    # Windows
export ACR_API_KEY=acr-dev-xxxxx # Mac/Linux

# Run the demo agent (10 runs)
python demo/demo_agent.py

# Or seed more data (30 runs)
python demo/seed_data.py
```

### 5. Open the Dashboard

Visit **http://localhost:3000**, paste your API key, and explore!

---

## Using the Python SDK

### Install

```bash
pip install -e ./sdk
```

### Instrument Your Agent

```python
from agentcontrolroom import trace, ACRClient

client = ACRClient(api_key="your-key", endpoint="http://localhost:8000")
trace.configure(client=client)

@trace.agent("my-agent")
def my_agent(query: str):
    result = analyze(query)
    return summarize(result)

@trace.llm_call("gpt-4o")
def analyze(query):
    # Your LLM call
    return response

@trace.tool("summarizer")
def summarize(data):
    # Your tool logic
    return summary
```

### Client-Side Guardrails

```python
from agentcontrolroom import Guardrails

guardrails = Guardrails(max_cost=5.0, max_latency_ms=30000, max_loop_count=10)
guardrails.check_cost(current_cost)
```

---

## API Reference

All endpoints require `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ingest/traces` | Send traces |
| GET | `/api/v1/runs` | List runs |
| GET | `/api/v1/runs/{id}` | Run detail |
| GET | `/api/v1/costs/summary` | Cost summary |
| GET | `/api/v1/costs/by-agent` | Cost by agent |
| GET | `/api/v1/costs/by-model` | Cost by model |
| GET | `/api/v1/evaluations` | List evaluations |
| POST | `/api/v1/evaluations/trigger` | Trigger eval |
| GET/POST | `/api/v1/guardrails/configs` | Guardrail CRUD |
| GET | `/api/v1/guardrails/alerts` | List alerts |

---

## Database Migrations

```bash
cd backend

# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Project Structure

```
ai/
├── backend/     # FastAPI + SQLAlchemy + Dramatiq
├── sdk/         # Python SDK (pip-installable)
├── frontend/    # Next.js 14 dashboard
├── demo/        # Demo agents + seed data
└── docs/        # This documentation
```
