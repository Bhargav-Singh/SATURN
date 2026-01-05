# SATURN – Agentic Sessions Plan

This plan converts the architecture spec into staged, agent-friendly sessions.
Each session is a self-contained prompt for a "moon" (AI agent) and prioritizes
simple, debuggable code, structured logging, and consistent error handling.
It expands every component in Section 3 into detailed implementation sessions.

## Naming
- Project: SATURN
- "Moon": an AI agent working on a session

## Global Engineering Constraints
- Keep code simple and explicit; avoid over-abstraction.
- All logs are structured JSON and include `request_id`, `company_id`, and `agent_id` when available.
- Centralize error codes and map them to API responses.
- Never log secrets; redact tool args/results as needed.
- All DB access is tenant-scoped (`company_id` required).

## Shared Artifacts (created in Session 0)
- `docs/error_codes.md`: canonical error code registry.
- `src/common/errors.py`: error classes + code mapping + helper to build API error responses.
- `src/common/logging.py`: logger config with request context.

---

## Session 0 – Foundations (Moon: Core)
Goal: lay down the repo skeleton and common utilities.

Tasks:
- Create repo layout per architecture spec (`routers/`, `services/`, `adapters/`, `models/`, `schemas/`, `workers/`).
- Add structured logging utilities with request context injection.
- Create error handling module and `docs/error_codes.md` registry.
- Add base FastAPI app with health/readiness endpoints.

Outputs:
- Skeleton project with shared logging/error handling.
- Error code registry initialized with baseline codes from `docs/api.md`.

Acceptance:
- `GET /health` returns OK with request_id.
- Example error response uses registry codes.

---

## Session 1 – Auth, Tenancy, and RBAC (Moon: Identity)
Goal: implement tenant resolution and access control.

Tasks:
- API key auth (hash storage, lookup, status checks).
- JWT auth for UI (minimal).
- Tenant middleware that injects `company_id` into request context.
- RBAC roles and permission checks for admin endpoints.

Outputs:
- Auth middleware and tenant context on every request.
- Role/permission checks in routers.

Acceptance:
- Unauthorized requests return `AUTH_INVALID`.
- Tenant mismatch is blocked with `TENANT_NOT_FOUND` or `AUTH_FORBIDDEN`.

---

## Session 2 – Agent Management (Moon: Agents)
Goal: CRUD for agents with versioning and audit logs.

Tasks:
- Implement `POST /agents`, `GET /agents`, `GET /agents/{id}`, `PATCH /agents/{id}`, `POST /agents/{id}/disable`.
- Store configs in JSONB, increment version on update.
- Write audit logs for config changes.

Outputs:
- Agent CRUD service + schemas + router.
- Audit logs on create/update/disable.

Acceptance:
- Version increments on every update.
- Tenant isolation enforced on all agent queries.

---

## Session 3 – Sessions & Chat Runtime (Moon: Orchestrator)
Goal: core runtime: sessions, messages, and one-turn orchestration.

Tasks:
- Session create/load, message persistence, windowing.
- Orchestrator loop with tool-call handling stubbed.
- LLM provider abstraction with usage capture.

Outputs:
- `POST /agents/{id}/chat` endpoint.
- Messages persisted with usage metadata.

Acceptance:
- New chat creates session if missing.
- Usage events created per LLM call.

---

## Session 4 – Tools Service (Moon: Tools)
Goal: tool registry and execution with policy enforcement.

Tasks:
- CRUD for tools and attach/detach to agents.
- HTTP tool execution with schema validation.
- Tool allowlist, per-turn max calls, and error handling.

Outputs:
- Tool service + router.
- Tool execution audited with redaction.

Acceptance:
- Disallowed tool calls return `TOOL_NOT_ALLOWED`.
- Schema errors return `TOOL_SCHEMA_INVALID`.

---

## Session 5 – Knowledge Base (Moon: RAG)
Goal: document upload, indexing pipeline, retrieval.

Tasks:
- Upload endpoint and `kb_documents` tracking.
- Async indexing worker stub (enqueue + status update).
- Retrieval integration into orchestrator.

Outputs:
- `POST /agents/{id}/kb/upload`, list/delete, reindex endpoints.
- RAG retrieval returns citations.

Acceptance:
- Retrieval filters by `company_id` and `agent_id`.
- KB failures return `KB_INDEXING_FAILED`.

---

## Session 6 – Usage Metering & Billing (Moon: Billing)
Goal: usage events and invoice draft generation.

Tasks:
- Append-only usage event creation.
- Monthly aggregation job (worker).
- `POST /invoices/generate` draft creation.

Outputs:
- Usage endpoints and invoice endpoints.

Acceptance:
- Drafts are recomputable from usage events.
- Billing data is tenant-scoped.

---

## Session 7 – Observability (Moon: Ops)
Goal: metrics, tracing hooks, and logging completeness.

Tasks:
- `/metrics` endpoint (basic counts/latencies).
- Add correlation IDs and propagate to logs.
- Add error logging with code + request_id.

Outputs:
- Metrics endpoint and consistent logs.

Acceptance:
- Every request logs `request_id`.
- Failures emit structured error logs with code.

---

## Session 8 – Tests and Hardening (Moon: QA)
Goal: essential tests and guardrails.

Tasks:
- Tenant isolation tests (db + qdrant filter stubs).
- Agent CRUD tests.
- Chat runtime tests (no tool, tool error paths).
- Usage events and invoice draft tests.

Outputs:
- Pytest suite for MVP acceptance criteria.

Acceptance:
- Tests cover tenant isolation and critical flows.

---

## Session 9 – Data Layer (Moon: Storage)
Goal: replace in-memory stores with MySQL-backed persistence.

Tasks:
- Add SQLAlchemy models matching `docs/db_schema.md`.
- Add database session factory and tenant-scoped query helper.
- Implement CRUD services for companies, users, roles, api_keys, agents, tools, sessions, messages, kb_documents, usage_events, invoices.
- Migrations: Alembic setup with initial schema.

Outputs:
- DB models and repositories.
- MySQL configured with env vars and connection pooling.

Acceptance:
- CRUD routes persist to MySQL.
- All queries require `company_id`.

---

## Session 10 – LLM Provider (Moon: LLM)
Goal: real provider adapters and usage extraction.

Tasks:
- Implement OpenAI adapter (configurable via env).
- Implement Ollama adapter (optional).
- Standardize request/response and usage extraction.
- Add timeouts and retry with backoff (idempotent only).

Outputs:
- `adapters/llm/` with provider implementations.
- Usage emitted for each model call.

Acceptance:
- LLM calls succeed with real provider.
- Usage events recorded with tokens in/out.

---

## Session 11 – RAG Pipeline (Moon: Indexing)
Goal: production-grade ingestion + retrieval with Qdrant.

Tasks:
- Integrate LlamaIndex for chunking and embedding.
- Store vectors in Qdrant with `company_id` + `agent_id` payload filters.
- Implement async indexing worker stub (enqueue + status update).
- Implement retrieval interface returning chunks + citations.

Outputs:
- RAG service with ingestion and retrieval.
- Worker task for indexing.

Acceptance:
- Retrieval filtered by `company_id` and `agent_id`.
- KB doc status transitions: uploaded → indexing → ready/failed.

---

## Session 12 – Orchestrator Tool Loop (Moon: Runtime)
Goal: multi-step tool execution with policy enforcement.

Tasks:
- Register tool schemas with model calls.
- Enforce per-agent allowlist and per-turn max tool calls.
- Execute tool calls and loop back to LLM with tool results.
- Add redaction of sensitive args/results.

Outputs:
- Orchestrator tool loop.
- Audit logs for tool executions.

Acceptance:
- Disallowed tools blocked.
- Loop caps respected and logged.

---

## Session 13 – Channels and Adapters (Moon: Channels)
Goal: channel adapters and normalization.

Tasks:
- Web chat (REST + optional WS).
- API chat (server-to-server).
- Idempotency keys for incoming events (store hash).

Outputs:
- Adapter layer for channel normalization.

Acceptance:
- Duplicate webhook events are idempotent.

---

## Session 14 – Billing Aggregation Worker (Moon: Billing Ops)
Goal: monthly aggregation job.

Tasks:
- Worker to aggregate usage events into invoice drafts.
- Pricing config per plan (stub).
- Recompute invoices from usage events.

Outputs:
- Scheduled job for billing aggregation.

Acceptance:
- Aggregation produces deterministic drafts.

---

## Session 15 – Security Hardening (Moon: Security)
Goal: secrets handling, redaction, and logging hygiene.

Tasks:
- Central redaction rules for tool args/results.
- API key hashing + rotation endpoints.
- Ensure secrets never logged.

Outputs:
- Redaction utilities and policy enforcement.

Acceptance:
- Redaction applied to tool logs.

---

## Session 16 – Observability v1 (Moon: Tracing)
Goal: tracing hooks for API, orchestrator, tool, RAG.

Tasks:
- OpenTelemetry spans for request, LLM, tool, RAG.
- Correlation IDs across services and workers.

Outputs:
- Trace spans with consistent IDs.

Acceptance:
- Traces include request_id, company_id, agent_id.

---

## Session 17 – QA and Acceptance (Moon: QA+)
Goal: MVP acceptance coverage.

Tasks:
- Tests for tenant isolation across DB + Qdrant filters.
- Tests for tool allowlist, schema validation, and failure paths.
- End-to-end tests for chat + RAG + tools + usage + billing.

Outputs:
- Full test suite for MVP acceptance.

Acceptance:
- All MVP acceptance criteria pass.

## Prompt Template (per Moon)
Use this when prompting a moon to implement a session:

```
You are Moon: <name>. Implement Session <N> from docs/agentic_sessions_plan.md.
Before coding, review docs/architecture.md for detailed requirements relevant to this session.
Constraints: keep code simple, add structured logging, use error codes registry.
Deliverables: code + tests (if applicable) + update docs if needed.
Do not refactor unrelated areas.
```
