import uuid
from dataclasses import dataclass
from typing import Dict, List

from common.logging import get_logger
from db.session import session_scope
from models.core import AuditLog as AuditLogModel

logger = get_logger("services.audit")


@dataclass
class AuditLog:
    company_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    metadata: Dict[str, str]


def record_audit_log(
    company_id: str,
    actor_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: Dict[str, str],
) -> None:
    with session_scope() as session:
        session.add(
            AuditLogModel(
                id=str(uuid.uuid4()),
                company_id=company_id,
                actor_type="system",
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                metadata_json=metadata,
            )
        )
    logger.info("audit_log_recorded %s %s", action, resource_id)


def list_audit_logs(company_id: str) -> List[AuditLog]:
    with session_scope() as session:
        rows = (
            session.query(AuditLogModel)
            .filter(AuditLogModel.company_id == company_id)
            .all()
        )
    return [
        AuditLog(
            company_id=row.company_id,
            actor_id=row.actor_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            metadata=row.metadata_json or {},
        )
        for row in rows
    ]


def reset_audit_logs() -> None:
    with session_scope() as session:
        session.query(AuditLogModel).delete()
