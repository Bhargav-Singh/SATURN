import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from common.errors import SaturnError
from db.session import session_scope
from models.core import User as UserModel


@dataclass
class UserRecord:
    id: str
    company_id: str
    email: str
    status: str


def create_user(company_id: str, email: str, password_hash: Optional[str] = None) -> UserRecord:
    user_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            UserModel(
                id=user_id,
                company_id=company_id,
                email=email,
                password_hash=password_hash,
                status="active",
                created_at=datetime.utcnow(),
            )
        )
    return get_user(company_id, user_id)


def get_user(company_id: str, user_id: str) -> UserRecord:
    with session_scope() as session:
        row = (
            session.query(UserModel)
            .filter(UserModel.company_id == company_id, UserModel.id == user_id)
            .first()
        )
    if not row:
        raise SaturnError("NOT_FOUND", "User not found")
    return UserRecord(id=row.id, company_id=row.company_id, email=row.email, status=row.status)


def list_users(company_id: str) -> List[UserRecord]:
    with session_scope() as session:
        rows = session.query(UserModel).filter(UserModel.company_id == company_id).all()
    return [UserRecord(id=row.id, company_id=row.company_id, email=row.email, status=row.status) for row in rows]
