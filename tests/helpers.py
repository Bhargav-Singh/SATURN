from datetime import datetime

from db.session import session_scope
from models.core import Company


def ensure_company(company_id: str, name: str = "Test Co") -> None:
    with session_scope() as session:
        existing = session.query(Company).filter(Company.id == company_id).first()
        if existing:
            return
        session.add(
            Company(
                id=company_id,
                name=name,
                plan_id="starter",
                status="active",
                created_at=datetime.utcnow(),
            )
        )
