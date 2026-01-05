import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List

from common.errors import SaturnError
from db.session import session_scope
from models.core import Company as CompanyModel


@dataclass
class CompanyRecord:
    id: str
    name: str
    plan_id: str
    status: str


def create_company(name: str, plan_id: str, status: str = "active") -> CompanyRecord:
    company_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            CompanyModel(
                id=company_id,
                name=name,
                plan_id=plan_id,
                status=status,
                created_at=datetime.utcnow(),
            )
        )
    return get_company(company_id)


def get_company(company_id: str) -> CompanyRecord:
    with session_scope() as session:
        row = session.query(CompanyModel).filter(CompanyModel.id == company_id).first()
    if not row:
        raise SaturnError("TENANT_NOT_FOUND")
    return CompanyRecord(id=row.id, name=row.name, plan_id=row.plan_id or "", status=row.status)


def list_companies() -> List[CompanyRecord]:
    with session_scope() as session:
        rows = session.query(CompanyModel).all()
    return [
        CompanyRecord(id=row.id, name=row.name, plan_id=row.plan_id or "", status=row.status)
        for row in rows
    ]
