from typing import Any, Dict, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    metadata: Optional[Dict[str, Any]] = None


class ChatUsage(BaseModel):
    tokens_in: int
    tokens_out: int
    tool_calls: int
    kb_queries: int


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    usage: ChatUsage
