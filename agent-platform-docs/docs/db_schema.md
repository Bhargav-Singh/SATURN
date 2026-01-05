# Agentic AI Platform – Database Schema (Deep)

This document defines the authoritative relational schema for the platform.
All core tables are tenant-scoped using `company_id`.

---

## 1. Design Rules

1. Every tenant-owned entity must include `company_id`.
2. UUID primary keys for all tables.
3. Append-only logs for usage and auditing.
4. No hard deletes for messages; prefer soft delete where needed.
5. Indexing: favor `(company_id, foreign_key)` patterns.
6. Store large configs as JSONB (validated at application layer).

---

## 2. Core Entities

### 2.1 companies
- `id` uuid pk
- `name` text
- `plan_id` text
- `status` text (active|suspended)
- `created_at` timestamptz

Indexes:
- (name) optional unique if global uniqueness desired

---

### 2.2 users
- `id` uuid pk
- `company_id` uuid fk companies(id)
- `email` text (unique within company)
- `password_hash` text (nullable if SSO)
- `status` text (active|disabled)
- `created_at` timestamptz

Indexes:
- unique(company_id, email)

---

### 2.3 roles
- `id` uuid pk
- `company_id` uuid fk
- `name` text
- `permissions` jsonb
- `created_at` timestamptz

Indexes:
- unique(company_id, name)

---

### 2.4 user_roles
- `company_id` uuid
- `user_id` uuid fk
- `role_id` uuid fk
Primary key:
- (company_id, user_id, role_id)

---

### 2.5 api_keys
- `id` uuid pk
- `company_id` uuid fk
- `name` text
- `key_hash` text (never store plaintext)
- `scopes` jsonb
- `status` text (active|revoked)
- `last_used_at` timestamptz nullable
- `rotated_from` uuid nullable
- `created_at` timestamptz

Indexes:
- (company_id, status)
- unique(company_id, name)

---

## 3. Agent and Runtime

### 3.1 agents
- `id` uuid pk
- `company_id` uuid fk
- `name` text
- `type` text (chat|voice|task)
- `status` text (active|disabled)
- `model_config` jsonb
- `behavior_config` jsonb
- `memory_config` jsonb nullable
- `rag_config` jsonb nullable
- `tool_policy` jsonb nullable
- `channel_config` jsonb nullable
- `version` int
- `created_at` timestamptz
- `updated_at` timestamptz

Indexes:
- (company_id, type)
- (company_id, status)
- unique(company_id, name)

Notes:
- Every update increments `version`
- Consider separate `agent_versions` table in v1.5 for immutable versions

---

### 3.2 chat_sessions
- `id` uuid pk
- `company_id` uuid fk
- `agent_id` uuid fk agents(id)
- `user_external_id` text nullable
- `channel` text (web|api|whatsapp|slack|voice)
- `state` text (open|closed|archived)
- `started_at` timestamptz
- `ended_at` timestamptz nullable

Indexes:
- (company_id, agent_id, state)
- (company_id, user_external_id)

---

### 3.3 messages
- `id` uuid pk
- `company_id` uuid fk
- `session_id` uuid fk chat_sessions(id)
- `role` text (system|user|assistant|tool)
- `content` text nullable
- `content_json` jsonb nullable (structured outputs)
- `tool_name` text nullable
- `tool_args_json` jsonb nullable
- `tool_result_json` jsonb nullable
- `tokens_in` int nullable
- `tokens_out` int nullable
- `latency_ms` int nullable
- `created_at` timestamptz

Indexes:
- (company_id, session_id, created_at)
- (company_id, role)

Invariants:
- Messages are immutable once written.
- Tool messages must include tool_name + tool_result_json.

---

## 4. Knowledge Base

### 4.1 kb_documents
- `id` uuid pk
- `company_id` uuid fk
- `agent_id` uuid fk
- `filename` text
- `file_type` text
- `storage_path` text (local path or object key)
- `status` text (uploaded|indexing|ready|failed|deleted)
- `error_message` text nullable
- `created_at` timestamptz

Indexes:
- (company_id, agent_id, status)

Notes:
- Vectors live in Qdrant with payload including company_id, agent_id, doc_id, chunk_id

---

## 5. Tools

### 5.1 tools
- `id` uuid pk
- `company_id` uuid fk
- `name` text
- `type` text (builtin|http|workflow)
- `description` text
- `input_schema_json` jsonb
- `output_schema_json` jsonb nullable
- `config_json` jsonb (url/method/headers/timeouts/etc.)
- `status` text (active|disabled)
- `created_at` timestamptz

Indexes:
- unique(company_id, name)
- (company_id, status)

---

### 5.2 agent_tools
- `company_id` uuid
- `agent_id` uuid
- `tool_id` uuid
- `policy_json` jsonb nullable
Primary key:
- (company_id, agent_id, tool_id)

---

## 6. Usage and Billing

### 6.1 usage_events (append-only)
- `id` uuid pk
- `company_id` uuid fk
- `agent_id` uuid fk
- `session_id` uuid fk nullable
- `event_type` text (llm_tokens|tool_call|kb_query|audio_seconds)
- `quantity` numeric
- `unit` text (tokens|calls|seconds)
- `cost` numeric nullable (computed at write or aggregation time)
- `metadata_json` jsonb
- `created_at` timestamptz

Indexes:
- (company_id, created_at)
- (company_id, agent_id, created_at)

---

### 6.2 invoices
- `id` uuid pk
- `company_id` uuid fk
- `period_start` date
- `period_end` date
- `currency` text
- `subtotal` numeric
- `tax` numeric
- `total` numeric
- `status` text (draft|issued|paid|void)
- `line_items_json` jsonb
- `created_at` timestamptz

Indexes:
- (company_id, period_start, period_end)
- (company_id, status)

---

### 6.3 plans (optional early, recommended)
- `id` text pk (starter/pro/enterprise)
- `pricing_json` jsonb
- `created_at` timestamptz

---

## 7. Audit and Compliance

### 7.1 audit_logs (append-only)
- `id` uuid pk
- `company_id` uuid fk
- `actor_type` text (user|api_key|system)
- `actor_id` uuid/text
- `action` text
- `resource_type` text
- `resource_id` uuid/text
- `metadata_json` jsonb
- `created_at` timestamptz

Indexes:
- (company_id, created_at)
- (company_id, action)

---

## 8. Constraints & Enforcement

- All SELECT/UPDATE/DELETE queries MUST include `company_id`.
- Enforce at application layer using a tenant-scoped session wrapper.
- For Qdrant:
  - every point payload includes company_id and agent_id
  - every search includes payload filters for both

---

## 9. Future Extensions

- agent_versions: immutable snapshots per agent config change
- tool_credentials: encrypted secrets table
- retention_policies: per-tenant retention for sessions/messages
- conversation_summaries: session-level summary text/json
- human_handoff: ticket entity + transcript export
