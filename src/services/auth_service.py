import hashlib
from datetime import datetime, timezone
from typing import Optional

import jwt

from common.auth import AuthContext
from common.config import ApiKeyRecord, get_settings
from common.errors import SaturnError
from common.logging import get_logger
from db.session import session_scope
from models.core import ApiKey as ApiKeyModel

logger = get_logger("services.auth")


def _hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _find_api_key_record(token: str) -> Optional[ApiKeyRecord]:
    settings = get_settings()
    token_hash = _hash_api_key(token)
    with session_scope() as session:
        row = (
            session.query(ApiKeyModel)
            .filter(ApiKeyModel.key_hash == token_hash, ApiKeyModel.status == "active")
            .first()
        )
        if row:
            row.last_used_at = datetime.now(timezone.utc)
            return ApiKeyRecord(
                key_hash=row.key_hash,
                company_id=row.company_id,
                scopes=row.scopes or [],
                status=row.status,
            )
    for record in settings.api_keys:
        if record.key_hash == token_hash:
            return record
    return None


def verify_api_key(token: str) -> AuthContext:
    record = _find_api_key_record(token)
    if not record or record.status != "active":
        raise SaturnError("AUTH_INVALID")
    logger.info("api_key_verified")
    return AuthContext(
        auth_type="api_key",
        company_id=record.company_id,
        user_id=None,
        role="admin",
        scopes=record.scopes,
    )


def verify_jwt(token: str) -> AuthContext:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        logger.error("jwt_invalid", exc_info=exc)
        raise SaturnError("AUTH_INVALID")
    company_id = payload.get("company_id")
    if not company_id:
        raise SaturnError("TENANT_NOT_FOUND")
    logger.info("jwt_verified")
    return AuthContext(
        auth_type="jwt",
        company_id=company_id,
        user_id=payload.get("user_id"),
        role=payload.get("role", "viewer"),
        scopes=payload.get("scopes", []),
    )


def parse_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip()


def authenticate(authorization: Optional[str]) -> Optional[AuthContext]:
    token = parse_bearer_token(authorization)
    if not token:
        return None
    if token.startswith("sk_"):
        return verify_api_key(token)
    return verify_jwt(token)
