from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(builtin|http|workflow)$")
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    config: Dict[str, Any]
    status: str = Field("active", pattern="^(active|disabled)$")


class ToolTestRequest(BaseModel):
    input: Dict[str, Any]


class ToolAttachRequest(BaseModel):
    tool_id: str
    policy: Optional[Dict[str, Any]] = None


class ToolDetachRequest(BaseModel):
    tool_id: str
