from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import status


@dataclass(frozen=True)
class ErrorDefinition:
    code: str
    message: str
    http_status: int


ERRORS: Dict[str, ErrorDefinition] = {
    "AUTH_INVALID": ErrorDefinition("AUTH_INVALID", "Authentication failed", status.HTTP_401_UNAUTHORIZED),
    "AUTH_FORBIDDEN": ErrorDefinition("AUTH_FORBIDDEN", "Access forbidden", status.HTTP_403_FORBIDDEN),
    "TENANT_NOT_FOUND": ErrorDefinition("TENANT_NOT_FOUND", "Tenant not found", status.HTTP_404_NOT_FOUND),
    "AGENT_NOT_FOUND": ErrorDefinition("AGENT_NOT_FOUND", "Agent not found", status.HTTP_404_NOT_FOUND),
    "SESSION_NOT_FOUND": ErrorDefinition("SESSION_NOT_FOUND", "Session not found", status.HTTP_404_NOT_FOUND),
    "KB_INDEXING_FAILED": ErrorDefinition(
        "KB_INDEXING_FAILED", "Knowledge base indexing failed", status.HTTP_500_INTERNAL_SERVER_ERROR
    ),
    "TOOL_NOT_ALLOWED": ErrorDefinition("TOOL_NOT_ALLOWED", "Tool not allowed", status.HTTP_403_FORBIDDEN),
    "TOOL_SCHEMA_INVALID": ErrorDefinition("TOOL_SCHEMA_INVALID", "Tool schema invalid", status.HTTP_400_BAD_REQUEST),
    "TOOL_EXECUTION_FAILED": ErrorDefinition(
        "TOOL_EXECUTION_FAILED", "Tool execution failed", status.HTTP_500_INTERNAL_SERVER_ERROR
    ),
    "LLM_PROVIDER_ERROR": ErrorDefinition(
        "LLM_PROVIDER_ERROR", "LLM provider error", status.HTTP_502_BAD_GATEWAY
    ),
    "RATE_LIMITED": ErrorDefinition("RATE_LIMITED", "Rate limited", status.HTTP_429_TOO_MANY_REQUESTS),
    "BAD_REQUEST": ErrorDefinition("BAD_REQUEST", "Bad request", status.HTTP_400_BAD_REQUEST),
    "NOT_FOUND": ErrorDefinition("NOT_FOUND", "Resource not found", status.HTTP_404_NOT_FOUND),
    "INTERNAL_ERROR": ErrorDefinition("INTERNAL_ERROR", "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR),
}


class SaturnError(Exception):
    def __init__(self, code: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if code not in ERRORS:
            raise ValueError(f"Unknown error code: {code}")
        self.definition = ERRORS[code]
        self.code = code
        self.message = message or self.definition.message
        self.details = details or {}
        super().__init__(self.message)


def error_response(code: str, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    definition = ERRORS.get(code, ERRORS["INTERNAL_ERROR"])
    return {
        "error": {
            "code": definition.code,
            "message": message or definition.message,
            "details": details or {},
        },
    }
