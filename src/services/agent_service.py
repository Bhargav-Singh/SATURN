import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from common.auth import AuthContext
from common.errors import SaturnError
from common.logging import get_logger
from db.session import session_scope
from models.core import Agent as AgentModel
from services.audit_service import record_audit_log

logger = get_logger("services.agents")


@dataclass
class AgentRecord:
    id: str
    company_id: str
    name: str
    type: str
    status: str
    model_config: Dict
    behavior_config: Dict
    memory_config: Optional[Dict]
    rag_config: Optional[Dict]
    tool_policy: Optional[Dict]
    channel_config: Optional[Dict]
    version: int


def _to_record(model: AgentModel) -> AgentRecord:
    return AgentRecord(
        id=model.id,
        company_id=model.company_id,
        name=model.name,
        type=model.type,
        status=model.status,
        model_config=model.model_config,
        behavior_config=model.behavior_config,
        memory_config=model.memory_config,
        rag_config=model.rag_config,
        tool_policy=model.tool_policy,
        channel_config=model.channel_config,
        version=model.version,
    )


def create_agent(company_id: str, payload: Dict, actor: AuthContext) -> AgentRecord:
    agent_id = str(uuid.uuid4())
    with session_scope() as session:
        model = AgentModel(
            id=agent_id,
            company_id=company_id,
            name=payload["name"],
            type=payload["type"],
            status=payload.get("status", "active"),
            model_config=payload["model_config"],
            behavior_config=payload["behavior_config"],
            memory_config=payload.get("memory_config"),
            rag_config=payload.get("rag_config"),
            tool_policy=payload.get("tool_policy"),
            channel_config=payload.get("channel_config"),
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(model)
    record_audit_log(
        company_id=company_id,
        actor_id=actor.user_id or actor.auth_type,
        action="agent_created",
        resource_type="agent",
        resource_id=agent_id,
        metadata={"name": payload["name"]},
    )
    logger.info("agent_created %s", agent_id)
    return get_agent(company_id, agent_id)


def list_agents(company_id: str, agent_type: Optional[str], status: Optional[str]) -> List[AgentRecord]:
    with session_scope() as session:
        query = session.query(AgentModel).filter(AgentModel.company_id == company_id)
        if agent_type:
            query = query.filter(AgentModel.type == agent_type)
        if status:
            query = query.filter(AgentModel.status == status)
        return [_to_record(row) for row in query.all()]


def get_agent(company_id: str, agent_id: str) -> AgentRecord:
    with session_scope() as session:
        model = (
            session.query(AgentModel)
            .filter(AgentModel.company_id == company_id, AgentModel.id == agent_id)
            .first()
        )
        if not model:
            raise SaturnError("AGENT_NOT_FOUND")
        return _to_record(model)


def update_agent(company_id: str, agent_id: str, payload: Dict, actor: AuthContext) -> AgentRecord:
    new_version = None
    with session_scope() as session:
        model = (
            session.query(AgentModel)
            .filter(AgentModel.company_id == company_id, AgentModel.id == agent_id)
            .first()
        )
        if not model:
            raise SaturnError("AGENT_NOT_FOUND")
        for key, value in payload.items():
            if value is not None and hasattr(model, key):
                setattr(model, key, value)
        model.version += 1
        model.updated_at = datetime.utcnow()
        new_version = model.version
    record_audit_log(
        company_id=company_id,
        actor_id=actor.user_id or actor.auth_type,
        action="agent_updated",
        resource_type="agent",
        resource_id=agent_id,
        metadata={"version": str(new_version)},
    )
    logger.info("agent_updated %s", agent_id)
    return get_agent(company_id, agent_id)


def disable_agent(company_id: str, agent_id: str, actor: AuthContext) -> AgentRecord:
    new_version = None
    with session_scope() as session:
        model = (
            session.query(AgentModel)
            .filter(AgentModel.company_id == company_id, AgentModel.id == agent_id)
            .first()
        )
        if not model:
            raise SaturnError("AGENT_NOT_FOUND")
        if model.status == "disabled":
            return _to_record(model)
        model.status = "disabled"
        model.version += 1
        model.updated_at = datetime.utcnow()
        new_version = model.version
    record_audit_log(
        company_id=company_id,
        actor_id=actor.user_id or actor.auth_type,
        action="agent_disabled",
        resource_type="agent",
        resource_id=agent_id,
        metadata={"version": str(new_version)},
    )
    logger.info("agent_disabled %s", agent_id)
    return get_agent(company_id, agent_id)


def reset_agents() -> None:
    with session_scope() as session:
        session.query(AgentModel).delete()
