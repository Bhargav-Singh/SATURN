# SATURN Error Code Registry

This registry defines canonical error codes used across the SATURN API.
Codes are stable and referenced by `src/common/errors.py`.

## Auth
- AUTH_INVALID
- AUTH_FORBIDDEN

## Tenant and Identity
- TENANT_NOT_FOUND

## Agents and Sessions
- AGENT_NOT_FOUND
- SESSION_NOT_FOUND

## Knowledge Base
- KB_INDEXING_FAILED

## Tools
- TOOL_NOT_ALLOWED
- TOOL_SCHEMA_INVALID
- TOOL_EXECUTION_FAILED

## LLM/Provider
- LLM_PROVIDER_ERROR

## Platform
- RATE_LIMITED
- BAD_REQUEST
- NOT_FOUND
- INTERNAL_ERROR
