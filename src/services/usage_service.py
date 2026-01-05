import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from common.logging import get_logger
from db.session import session_scope
from models.core import UsageEvent as UsageEventModel

logger = get_logger("services.usage")


@dataclass
class UsageEvent:
    id: str
    company_id: str
    agent_id: str
    session_id: Optional[str]
    event_type: str
    quantity: int
    unit: str
    created_at: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def record_usage_event(
    company_id: str,
    agent_id: str,
    session_id: Optional[str],
    event_type: str,
    quantity: int,
    unit: str,
) -> UsageEvent:
    event_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            UsageEventModel(
                id=event_id,
                company_id=company_id,
                agent_id=agent_id,
                session_id=session_id,
                event_type=event_type,
                quantity=quantity,
                unit=unit,
                created_at=_now(),
            )
        )
    logger.info("usage_event %s %s", event_type, quantity)
    return UsageEvent(
        id=event_id,
        company_id=company_id,
        agent_id=agent_id,
        session_id=session_id,
        event_type=event_type,
        quantity=quantity,
        unit=unit,
        created_at=_now().isoformat(),
    )


def list_usage_events(company_id: str) -> List[UsageEvent]:
    with session_scope() as session:
        rows = (
            session.query(UsageEventModel)
            .filter(UsageEventModel.company_id == company_id)
            .all()
        )
    return [
        UsageEvent(
            id=row.id,
            company_id=row.company_id,
            agent_id=row.agent_id,
            session_id=row.session_id,
            event_type=row.event_type,
            quantity=int(row.quantity),
            unit=row.unit,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


def summarize_usage(company_id: str) -> Dict[str, int]:
    totals = {"tokens_in": 0, "tokens_out": 0, "tool_calls": 0, "kb_queries": 0, "audio_seconds": 0}
    for event in list_usage_events(company_id):
        if event.event_type == "llm_tokens_in":
            totals["tokens_in"] += event.quantity
        elif event.event_type == "llm_tokens_out":
            totals["tokens_out"] += event.quantity
        elif event.event_type == "tool_call":
            totals["tool_calls"] += event.quantity
        elif event.event_type == "kb_query":
            totals["kb_queries"] += event.quantity
        elif event.event_type == "audio_seconds":
            totals["audio_seconds"] += event.quantity
    return totals


def reset_usage_events() -> None:
    with session_scope() as session:
        session.query(UsageEventModel).delete()
