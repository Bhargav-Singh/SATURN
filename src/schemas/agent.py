from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    type: str = Field(..., pattern="^(chat|voice|task)$")
    status: str = Field("active", pattern="^(active|disabled)$")
    model_config_payload: Dict[str, Any] = Field(..., alias="model_config")
    behavior_config: Dict[str, Any]
    memory_config: Optional[Dict[str, Any]] = None
    rag_config: Optional[Dict[str, Any]] = None
    tool_policy: Optional[Dict[str, Any]] = None
    channel_config: Optional[Dict[str, Any]] = None


class AgentUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|disabled)$")
    model_config_payload: Optional[Dict[str, Any]] = Field(None, alias="model_config")
    behavior_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    rag_config: Optional[Dict[str, Any]] = None
    tool_policy: Optional[Dict[str, Any]] = None
    channel_config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    agent_id: str
    company_id: str
    name: str
    type: str
    status: str
    model_config_payload: Dict[str, Any] = Field(..., alias="model_config")
    behavior_config: Dict[str, Any]
    memory_config: Optional[Dict[str, Any]] = None
    rag_config: Optional[Dict[str, Any]] = None
    tool_policy: Optional[Dict[str, Any]] = None
    channel_config: Optional[Dict[str, Any]] = None
    version: int


class AgentListResponse(BaseModel):
    data: List[AgentResponse]
