# Agentic AI Platform – API Specification (Deep)

This document defines HTTP APIs for the platform. APIs are versioned and stable.
All endpoints are scoped to a tenant (company) using API keys (external) or JWT (UI users).

---

## 1. Conventions

### Base URL
- `/api/v1`

### Response Envelope
Success:
```json
{
  "data": {},
  "meta": {
    "request_id": "uuid"
  }
}
```

Error:
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  },
  "meta": {
    "request_id": "uuid"
  }
}
```

### Idempotency
For webhook adapters and critical operations, support:
- `Idempotency-Key` header (optional)
- store hash in DB for N hours (future)

### Pagination
Use:
- `?limit=50&cursor=...`
Return:
- `meta.next_cursor`

### Authentication Headers
- External API key: `Authorization: Bearer <API_KEY>`
- JWT: `Authorization: Bearer <JWT>`

### Tenant Resolution
- API key/JWT maps to `company_id`
- Never accept company_id directly from client except in super-admin operations.

---

## 2. Auth & Identity

### 2.1 Login (UI)
`POST /auth/login`

Request:
```json
{ "email": "a@b.com", "password": "..." }
```

Response:
```json
{ "data": { "access_token": "...", "token_type": "bearer" } }
```

### 2.2 Current User
`GET /auth/me`

Response:
```json
{ "data": { "user_id": "...", "email": "...", "role": "admin" } }
```

### 2.3 API Keys
Create API key (admin):
`POST /api-keys`

Request:
```json
{ "name": "prod-key", "scopes": ["chat:write", "agents:read"] }
```

Response (show plaintext ONCE):
```json
{ "data": { "api_key": "sk_live_....", "key_id": "uuid" } }
```

List keys:
`GET /api-keys`

Revoke key:
`POST /api-keys/{key_id}/revoke`

Rotate key:
`POST /api-keys/{key_id}/rotate`

---

## 3. Company & RBAC

Create company (bootstrap or super-admin only):
`POST /companies`

Request:
```json
{ "name": "Acme Inc", "plan_id": "starter" }
```

List roles:
`GET /roles`

Create custom role:
`POST /roles`

Assign role to user:
`POST /users/{user_id}/role`

---

## 4. Agent Management

### 4.1 Create Agent
`POST /agents`

Request:
```json
{
  "name": "Clinic Receptionist",
  "type": "chat",
  "status": "active",
  "model_config": {
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "temperature": 0.4,
    "max_output_tokens": 600
  },
  "behavior_config": {
    "system_prompt": "You are a receptionist...",
    "rules": [
      "Ask for name and phone",
      "Do not give medical diagnosis"
    ],
    "style": { "tone": "polite", "brevity": "medium" }
  },
  "rag_config": { "enabled": true, "top_k": 6, "min_score": 0.25 },
  "tool_policy": {
    "allowed_tools": ["calendar.create_event", "http.get"],
    "max_tool_calls_per_turn": 3
  },
  "channel_config": { "enabled_channels": ["web", "api"] }
}
```

Response:
```json
{ "data": { "agent_id": "uuid", "version": 1 } }
```

### 4.2 Get Agents
`GET /agents?type=chat&status=active`

### 4.3 Get Agent
`GET /agents/{agent_id}`

### 4.4 Update Agent
`PATCH /agents/{agent_id}`

Rules:
- Updates increment `agents.version`
- Maintain audit log of config changes

### 4.5 Disable Agent
`POST /agents/{agent_id}/disable`

---

## 5. Chat Runtime

### 5.1 Send Message (REST)
`POST /agents/{agent_id}/chat`

Request:
```json
{
  "session_id": "optional",
  "message": "I need to book an appointment",
  "metadata": {
    "user_external_id": "patient_123",
    "locale": "en-IN"
  }
}
```

Response:
```json
{
  "data": {
    "session_id": "uuid",
    "reply": "Sure. Can I have your full name and phone number?",
    "citations": [
      { "doc_id": "uuid", "title": "clinic_faq.pdf", "snippet": "..." }
    ],
    "usage": {
      "tokens_in": 210,
      "tokens_out": 55,
      "tool_calls": 0,
      "kb_queries": 1
    }
  }
}
```

### 5.2 Streaming Chat (WebSocket) (optional v1)
`WS /agents/{agent_id}/chat/stream?session_id=...`

Events:
- `token` (partial)
- `final` (complete response)
- `usage` (summary)
- `error`

---

## 6. Sessions & Messages

List sessions:
`GET /sessions?agent_id=...&state=open&limit=50`

Get a session:
`GET /sessions/{session_id}`

Get messages:
`GET /sessions/{session_id}/messages`

Close session:
`POST /sessions/{session_id}/close`

---

## 7. Knowledge Base (RAG)

Upload document:
`POST /agents/{agent_id}/kb/upload` (multipart)

Response:
```json
{ "data": { "doc_id": "uuid", "status": "indexing" } }
```

List documents:
`GET /agents/{agent_id}/kb`

Delete document:
`DELETE /agents/{agent_id}/kb/{doc_id}`

Reindex document:
`POST /agents/{agent_id}/kb/{doc_id}/reindex`

---

## 8. Tools

### 8.1 Create Tool
`POST /tools`

Request (HTTP tool example):
```json
{
  "name": "crm.create_lead",
  "type": "http",
  "description": "Create a lead in CRM",
  "input_schema": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "phone": { "type": "string" }
    },
    "required": ["name", "phone"]
  },
  "config": {
    "method": "POST",
    "url": "https://example-crm/api/leads",
    "headers": { "Authorization": "Bearer {{secret.crm_token}}" },
    "timeout_seconds": 10
  }
}
```

List tools:
`GET /tools`

Attach tool to agent:
`POST /agents/{agent_id}/tools/attach`
```json
{ "tool_id": "uuid", "policy": { "daily_limit": 500 } }
```

Detach tool:
`POST /agents/{agent_id}/tools/detach`
```json
{ "tool_id": "uuid" }
```

Test tool (admin only):
`POST /tools/{tool_id}/test`
```json
{ "input": { "name": "A", "phone": "..." } }
```

---

## 9. Usage and Billing

Usage summary:
`GET /usage/summary?period=2025-12`

Response:
```json
{
  "data": {
    "period": "2025-12",
    "tokens_in": 123456,
    "tokens_out": 654321,
    "tool_calls": 980,
    "kb_queries": 1200,
    "estimated_cost": 342.10
  }
}
```

List invoices:
`GET /invoices?status=draft&period=2025-12`

Get invoice:
`GET /invoices/{invoice_id}`

Generate invoice draft (admin):
`POST /invoices/generate`
```json
{ "period": "2025-12" }
```

Mark invoice paid (admin):
`POST /invoices/{invoice_id}/mark-paid`

---

## 10. Voice (v1)

Voice session connect (WebSocket):
`WS /agents/{agent_id}/voice/connect?session_id=...`

Events:
- client sends audio chunks
- server sends transcript + assistant audio chunks

Telephony adapters:
- provider webhook endpoints map call_id → session_id and stream audio.

---

## 11. Health and Meta

Health:
`GET /health`

Readiness:
`GET /ready`

Metrics:
`GET /metrics` (optional Prometheus format)

---

## 12. Standard Error Codes

- `AUTH_INVALID`
- `AUTH_FORBIDDEN`
- `TENANT_NOT_FOUND`
- `AGENT_NOT_FOUND`
- `SESSION_NOT_FOUND`
- `KB_INDEXING_FAILED`
- `TOOL_NOT_ALLOWED`
- `TOOL_SCHEMA_INVALID`
- `TOOL_EXECUTION_FAILED`
- `LLM_PROVIDER_ERROR`
- `RATE_LIMITED`
