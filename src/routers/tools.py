from fastapi import APIRouter, Depends, Request

from common.auth import AuthContext
from common.logging import get_logger
from common.rbac import require_permission
from routers.auth import require_jwt
from schemas.tool import ToolCreate, ToolTestRequest
from services.tool_service import create_tool, execute_tool, list_tools

router = APIRouter(prefix="/tools")
logger = get_logger("routers.tools")


def _envelope(data: dict, request: Request) -> dict:
    return {"data": data, "meta": {"request_id": request.state.request_id}}


@router.post("")
def create_tool_endpoint(
    request: Request, payload: ToolCreate, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "tools:write")
    record = create_tool(auth.company_id, payload.model_dump(), auth)
    return _envelope({"tool_id": record.id}, request)


@router.get("")
def list_tools_endpoint(request: Request, auth: AuthContext = Depends(require_jwt)) -> dict:
    require_permission(auth, "tools:read")
    tools = list_tools(auth.company_id)
    data = [
        {
            "tool_id": tool.id,
            "name": tool.name,
            "type": tool.type,
            "description": tool.description,
            "status": tool.status,
        }
        for tool in tools
    ]
    return _envelope({"tools": data}, request)


@router.post("/{tool_id}/test")
def test_tool_endpoint(
    request: Request,
    tool_id: str,
    payload: ToolTestRequest,
    auth: AuthContext = Depends(require_jwt),
) -> dict:
    require_permission(auth, "tools:write")
    result = execute_tool(auth.company_id, tool_id, payload.input)
    logger.info("tool_tested %s", tool_id)
    return _envelope({"result": result}, request)
