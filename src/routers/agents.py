from typing import Optional

from fastapi import APIRouter, Depends, Request

from common.auth import AuthContext
from common.errors import SaturnError
from common.logging import get_logger, set_request_context
from common.rbac import has_scope, require_permission
from routers.auth import require_auth, require_jwt
from schemas.agent import AgentCreate, AgentUpdate
from schemas.chat import ChatRequest
from schemas.tool import ToolAttachRequest, ToolDetachRequest
from services.orchestrator_service import execute_turn
from services.tool_service import attach_tool, detach_tool
from services.agent_service import create_agent, disable_agent, get_agent, list_agents, update_agent

router = APIRouter(prefix="/agents")
logger = get_logger("routers.agents")


def _envelope(data: dict, request: Request) -> dict:
    return {"data": data, "meta": {"request_id": request.state.request_id}}


@router.post("")
def create_agent_endpoint(
    request: Request, payload: AgentCreate, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "agents:write")
    record = create_agent(auth.company_id, payload.model_dump(by_alias=True), auth)
    logger.info("agent_created %s", record.id)
    return _envelope({"agent_id": record.id, "version": record.version}, request)


@router.get("")
def list_agents_endpoint(
    request: Request,
    type: Optional[str] = None,
    status: Optional[str] = None,
    auth: AuthContext = Depends(require_jwt),
) -> dict:
    require_permission(auth, "agents:read")
    records = list_agents(auth.company_id, type, status)
    data = [
        {
            "agent_id": record.id,
            "company_id": record.company_id,
            "name": record.name,
            "type": record.type,
            "status": record.status,
            "model_config": record.model_config,
            "behavior_config": record.behavior_config,
            "memory_config": record.memory_config,
            "rag_config": record.rag_config,
            "tool_policy": record.tool_policy,
            "channel_config": record.channel_config,
            "version": record.version,
        }
        for record in records
    ]
    return _envelope({"agents": data}, request)


@router.get("/{agent_id}")
def get_agent_endpoint(
    request: Request, agent_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "agents:read")
    record = get_agent(auth.company_id, agent_id)
    data = {
        "agent_id": record.id,
        "company_id": record.company_id,
        "name": record.name,
        "type": record.type,
        "status": record.status,
        "model_config": record.model_config,
        "behavior_config": record.behavior_config,
        "memory_config": record.memory_config,
        "rag_config": record.rag_config,
        "tool_policy": record.tool_policy,
        "channel_config": record.channel_config,
        "version": record.version,
    }
    return _envelope(data, request)


@router.patch("/{agent_id}")
def update_agent_endpoint(
    request: Request, agent_id: str, payload: AgentUpdate, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "agents:write")
    record = update_agent(
        auth.company_id,
        agent_id,
        payload.model_dump(by_alias=True, exclude_unset=True),
        auth,
    )
    return _envelope({"agent_id": record.id, "version": record.version}, request)


@router.post("/{agent_id}/disable")
def disable_agent_endpoint(
    request: Request, agent_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "agents:write")
    record = disable_agent(auth.company_id, agent_id, auth)
    return _envelope({"agent_id": record.id, "version": record.version}, request)


@router.post("/{agent_id}/chat")
def chat_agent_endpoint(
    request: Request, agent_id: str, payload: ChatRequest, auth: AuthContext = Depends(require_auth)
) -> dict:
    if auth.auth_type == "jwt":
        require_permission(auth, "chat:write")
    else:
        if not has_scope(auth, ["chat:write"]):
            raise SaturnError("AUTH_FORBIDDEN")
    set_request_context(
        request_id=request.state.request_id,
        company_id=auth.company_id,
        agent_id=agent_id,
    )
    session_id, reply, usage, citations = execute_turn(
        auth.company_id, agent_id, payload.session_id, payload.message, payload.metadata, auth
    )
    data = {
        "session_id": session_id,
        "reply": reply,
        "citations": citations,
        "usage": usage,
    }
    return _envelope(data, request)


@router.post("/{agent_id}/tools/attach")
def attach_tool_endpoint(
    request: Request,
    agent_id: str,
    payload: ToolAttachRequest,
    auth: AuthContext = Depends(require_jwt),
) -> dict:
    require_permission(auth, "tools:write")
    attach_tool(auth.company_id, agent_id, payload.tool_id, payload.policy)
    return _envelope({"agent_id": agent_id, "tool_id": payload.tool_id}, request)


@router.post("/{agent_id}/tools/detach")
def detach_tool_endpoint(
    request: Request,
    agent_id: str,
    payload: ToolDetachRequest,
    auth: AuthContext = Depends(require_jwt),
) -> dict:
    require_permission(auth, "tools:write")
    detach_tool(auth.company_id, agent_id, payload.tool_id)
    return _envelope({"agent_id": agent_id, "tool_id": payload.tool_id}, request)
