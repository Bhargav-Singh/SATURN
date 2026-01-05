import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from common.auth import AuthContext
from common.errors import SaturnError
from common.logging import get_logger
from common.metrics import record_tool_call
from db.session import session_scope
from models.core import AgentTool as AgentToolModel
from models.core import Tool as ToolModel
from services.audit_service import record_audit_log

logger = get_logger("services.tools")


@dataclass
class ToolRecord:
    id: str
    company_id: str
    name: str
    type: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    config: Dict[str, Any]
    status: str


@dataclass
class ToolAttachment:
    company_id: str
    agent_id: str
    tool_id: str
    policy: Optional[Dict[str, Any]]


def _to_record(model: ToolModel) -> ToolRecord:
    return ToolRecord(
        id=model.id,
        company_id=model.company_id,
        name=model.name,
        type=model.type,
        description=model.description,
        input_schema=model.input_schema_json,
        output_schema=model.output_schema_json,
        config=model.config_json,
        status=model.status,
    )


def _validate_type(schema_type: str, value: Any) -> bool:
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "number":
        return isinstance(value, (int, float))
    if schema_type == "integer":
        return isinstance(value, int)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    return False


def validate_input_schema(schema: Dict[str, Any], payload: Dict[str, Any]) -> None:
    if schema.get("type") != "object":
        raise SaturnError("TOOL_SCHEMA_INVALID", "Only object schema supported")
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    for field in required:
        if field not in payload:
            raise SaturnError("TOOL_SCHEMA_INVALID", f"Missing required field: {field}")
    for key, value in payload.items():
        prop_schema = properties.get(key)
        if not prop_schema:
            continue
        prop_type = prop_schema.get("type")
        if prop_type and not _validate_type(prop_type, value):
            raise SaturnError("TOOL_SCHEMA_INVALID", f"Invalid type for field: {key}")


def create_tool(company_id: str, payload: Dict[str, Any], actor: AuthContext) -> ToolRecord:
    tool_id = str(uuid.uuid4())
    with session_scope() as session:
        model = ToolModel(
            id=tool_id,
            company_id=company_id,
            name=payload["name"],
            type=payload["type"],
            description=payload["description"],
            input_schema_json=payload["input_schema"],
            output_schema_json=payload.get("output_schema"),
            config_json=payload.get("config", {}),
            status=payload.get("status", "active"),
        )
        session.add(model)
    record_audit_log(
        company_id=company_id,
        actor_id=actor.user_id or actor.auth_type,
        action="tool_created",
        resource_type="tool",
        resource_id=tool_id,
        metadata={"name": payload["name"]},
    )
    logger.info("tool_created %s", tool_id)
    return get_tool(company_id, tool_id)


def list_tools(company_id: str) -> List[ToolRecord]:
    with session_scope() as session:
        rows = session.query(ToolModel).filter(ToolModel.company_id == company_id).all()
    return [_to_record(row) for row in rows]


def get_tool(company_id: str, tool_id: str) -> ToolRecord:
    with session_scope() as session:
        model = (
            session.query(ToolModel)
            .filter(ToolModel.company_id == company_id, ToolModel.id == tool_id)
            .first()
        )
        if not model:
            raise SaturnError("TOOL_NOT_ALLOWED")
        return _to_record(model)


def attach_tool(company_id: str, agent_id: str, tool_id: str, policy: Optional[Dict[str, Any]]) -> None:
    get_tool(company_id, tool_id)
    with session_scope() as session:
        existing = (
            session.query(AgentToolModel)
            .filter(
                AgentToolModel.company_id == company_id,
                AgentToolModel.agent_id == agent_id,
                AgentToolModel.tool_id == tool_id,
            )
            .first()
        )
        if existing:
            return
        session.add(
            AgentToolModel(
                company_id=company_id,
                agent_id=agent_id,
                tool_id=tool_id,
                policy_json=policy,
            )
        )
    logger.info("tool_attached %s %s", agent_id, tool_id)


def detach_tool(company_id: str, agent_id: str, tool_id: str) -> None:
    with session_scope() as session:
        session.query(AgentToolModel).filter(
            AgentToolModel.company_id == company_id,
            AgentToolModel.agent_id == agent_id,
            AgentToolModel.tool_id == tool_id,
        ).delete()
    logger.info("tool_detached %s %s", agent_id, tool_id)


def list_agent_tool_ids(company_id: str, agent_id: str) -> List[str]:
    with session_scope() as session:
        rows = (
            session.query(AgentToolModel)
            .filter(
                AgentToolModel.company_id == company_id,
                AgentToolModel.agent_id == agent_id,
            )
            .all()
        )
    return [row.tool_id for row in rows]


def execute_tool(company_id: str, tool_id: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    try:
        tool = get_tool(company_id, tool_id)
        validate_input_schema(tool.input_schema, tool_input)
        if tool.status != "active":
            raise SaturnError("TOOL_NOT_ALLOWED")
        if tool.type == "http":
            result = {"status": "ok", "echo": tool_input}
        elif tool.type == "builtin":
            result = {"status": "ok", "echo": tool_input}
        elif tool.type == "workflow":
            result = {"status": "queued", "job_id": str(uuid.uuid4())}
        else:
            raise SaturnError("TOOL_EXECUTION_FAILED", "Unknown tool type")
        record_tool_call(True)
        logger.info("tool_executed %s", tool_id)
        return result
    except SaturnError:
        record_tool_call(False)
        raise


def reset_tools() -> None:
    with session_scope() as session:
        session.query(AgentToolModel).delete()
        session.query(ToolModel).delete()
