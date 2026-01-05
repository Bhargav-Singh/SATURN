import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from common.errors import SaturnError
from common.logging import get_logger
from db.session import session_scope
from models.core import ChatSession as ChatSessionModel
from models.core import Message as MessageModel

logger = get_logger("services.sessions")


@dataclass
class ChatSession:
    id: str
    company_id: str
    agent_id: str
    user_external_id: Optional[str]
    channel: str
    state: str
    started_at: str
    ended_at: Optional[str]


@dataclass
class Message:
    id: str
    company_id: str
    session_id: str
    role: str
    content: str
    created_at: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(
    company_id: str,
    agent_id: str,
    user_external_id: Optional[str],
    channel: str,
) -> ChatSession:
    session_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            ChatSessionModel(
                id=session_id,
                company_id=company_id,
                agent_id=agent_id,
                user_external_id=user_external_id,
                channel=channel,
                state="open",
                started_at=_now(),
            )
        )
    logger.info("session_created %s", session_id)
    return get_session(company_id, session_id)


def get_session(company_id: str, session_id: str, agent_id: Optional[str] = None) -> ChatSession:
    with session_scope() as session:
        query = session.query(ChatSessionModel).filter(
            ChatSessionModel.company_id == company_id,
            ChatSessionModel.id == session_id,
        )
        if agent_id:
            query = query.filter(ChatSessionModel.agent_id == agent_id)
        row = query.first()
        if not row:
            raise SaturnError("SESSION_NOT_FOUND")
        return ChatSession(
            id=row.id,
            company_id=row.company_id,
            agent_id=row.agent_id,
            user_external_id=row.user_external_id,
            channel=row.channel,
            state=row.state,
            started_at=row.started_at.isoformat(),
            ended_at=row.ended_at.isoformat() if row.ended_at else None,
        )


def add_message(company_id: str, session_id: str, role: str, content: str) -> Message:
    message_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            MessageModel(
                id=message_id,
                company_id=company_id,
                session_id=session_id,
                role=role,
                content=content,
                created_at=_now(),
            )
        )
    logger.info("message_added %s %s", session_id, role)
    return Message(
        id=message_id,
        company_id=company_id,
        session_id=session_id,
        role=role,
        content=content,
        created_at=_now().isoformat(),
    )


def list_messages(company_id: str, session_id: str, limit: int = 20) -> List[Message]:
    with session_scope() as session:
        rows = (
            session.query(MessageModel)
            .filter(
                MessageModel.company_id == company_id,
                MessageModel.session_id == session_id,
            )
            .order_by(MessageModel.created_at.desc())
            .limit(limit)
            .all()
        )
    rows.reverse()
    return [
        Message(
            id=row.id,
            company_id=row.company_id,
            session_id=row.session_id,
            role=row.role,
            content=row.content or "",
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


def reset_sessions() -> None:
    with session_scope() as session:
        session.query(MessageModel).delete()
        session.query(ChatSessionModel).delete()
