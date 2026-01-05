import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List

from common.errors import SaturnError
from db.session import session_scope
from models.core import ApiKey as ApiKeyModel


@dataclass
class ApiKeyRecord:
    id: str
    company_id: str
    name: str
    scopes: List[str]
    status: str


def _hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_api_key(company_id: str, name: str, scopes: List[str]) -> str:
    plaintext = f"sk_{uuid.uuid4().hex}"
    key_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            ApiKeyModel(
                id=key_id,
                company_id=company_id,
                name=name,
                key_hash=_hash_api_key(plaintext),
                scopes=scopes,
                status="active",
                created_at=datetime.utcnow(),
            )
        )
    return plaintext


def list_api_keys(company_id: str) -> List[ApiKeyRecord]:
    with session_scope() as session:
        rows = session.query(ApiKeyModel).filter(ApiKeyModel.company_id == company_id).all()
    return [
        ApiKeyRecord(
            id=row.id,
            company_id=row.company_id,
            name=row.name,
            scopes=row.scopes or [],
            status=row.status,
        )
        for row in rows
    ]


def revoke_api_key(company_id: str, key_id: str) -> None:
    with session_scope() as session:
        updated = (
            session.query(ApiKeyModel)
            .filter(ApiKeyModel.company_id == company_id, ApiKeyModel.id == key_id)
            .update({"status": "revoked"})
        )
    if not updated:
        raise SaturnError("NOT_FOUND", "API key not found")
