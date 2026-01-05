import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from common.errors import SaturnError
from db.session import session_scope
from models.core import Role as RoleModel
from models.core import UserRole as UserRoleModel


@dataclass
class RoleRecord:
    id: str
    company_id: str
    name: str
    permissions: Dict


def create_role(company_id: str, name: str, permissions: Dict) -> RoleRecord:
    role_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            RoleModel(
                id=role_id,
                company_id=company_id,
                name=name,
                permissions=permissions,
                created_at=datetime.utcnow(),
            )
        )
    return get_role(company_id, role_id)


def get_role(company_id: str, role_id: str) -> RoleRecord:
    with session_scope() as session:
        row = (
            session.query(RoleModel)
            .filter(RoleModel.company_id == company_id, RoleModel.id == role_id)
            .first()
        )
    if not row:
        raise SaturnError("NOT_FOUND", "Role not found")
    return RoleRecord(id=row.id, company_id=row.company_id, name=row.name, permissions=row.permissions)


def list_roles(company_id: str) -> List[RoleRecord]:
    with session_scope() as session:
        rows = session.query(RoleModel).filter(RoleModel.company_id == company_id).all()
    return [RoleRecord(id=row.id, company_id=row.company_id, name=row.name, permissions=row.permissions) for row in rows]


def assign_role(company_id: str, user_id: str, role_id: str) -> None:
    with session_scope() as session:
        session.add(
            UserRoleModel(company_id=company_id, user_id=user_id, role_id=role_id)
        )
