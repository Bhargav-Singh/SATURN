# SATURN

SATURN is a platform for orchestrating multiple AI agents at scale. Like Saturn
with its many moons, this project coordinates and controls the "revolutions" of
agents (the moons) across chat, tools, knowledge retrieval, and usage tracking.

## What SATURN Provides
- Multi-tenant agent orchestration for chat, voice, and task agents.
- Config-first agents with policies, tools, and knowledge bases.
- Usage metering and billing foundations for scalable SaaS operations.
- Observability with structured logs, request IDs, and metrics.
- Pluggable providers for LLMs and vector search.

## Quick Start (SQLite)
Use SQLite for local development with a single file database.

```bash
export SATURN_DB_URL=sqlite+pysqlite:///saturn.db
conda activate saturn
PYTHONPATH=src uvicorn app.main:app --reload
```

Health endpoints:
- `GET /health`
- `GET /ready`
- `GET /metrics`

Run tests:
```bash
PYTHONPATH=src pytest
```

## MySQL (Production-Oriented)
Set a MySQL connection URL via:
```bash
export SATURN_DB_URL=mysql+pymysql://user:pass@localhost:3306/saturn
```

## Project Structure (High Level)
- `src/routers/` HTTP endpoints
- `src/services/` business logic
- `src/models/` SQLAlchemy models
- `src/db/` database session and setup
- `agent-platform-docs/docs/` architecture and planning docs

## Moon Philosophy
SATURN is the orchestrator; AI agents are its moons. Each moon can be configured
and guided by policies, tools, and knowledge, while SATURN keeps the system safe,
observable, and scalable.
