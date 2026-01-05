import json
import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ApiKeyRecord:
    key_hash: str
    company_id: str
    scopes: List[str]
    status: str


@dataclass(frozen=True)
class RolePermissions:
    role: str
    permissions: List[str]


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_algorithm: str
    api_keys: List[ApiKeyRecord]
    role_permissions: Dict[str, List[str]]
    billing_currency: str
    db_url: str


def _load_api_keys(value: str) -> List[ApiKeyRecord]:
    if not value:
        return []
    parsed = json.loads(value)
    records: List[ApiKeyRecord] = []
    for item in parsed:
        records.append(
            ApiKeyRecord(
                key_hash=item["key_hash"],
                company_id=item["company_id"],
                scopes=item.get("scopes", []),
                status=item.get("status", "active"),
            )
        )
    return records


def _load_role_permissions(value: str) -> Dict[str, List[str]]:
    if not value:
        return {
            "admin": ["*"],
            "operator": [
                "agents:read",
                "agents:write",
                "sessions:read",
                "kb:read",
                "kb:write",
                "chat:write",
                "tools:read",
                "billing:read",
            ],
            "viewer": ["agents:read", "sessions:read", "kb:read", "tools:read", "billing:read"],
        }
    parsed = json.loads(value)
    return {role: perms for role, perms in parsed.items()}


def get_settings() -> Settings:
    return Settings(
        jwt_secret=os.getenv("SATURN_JWT_SECRET", "change-me"),
        jwt_algorithm=os.getenv("SATURN_JWT_ALG", "HS256"),
        api_keys=_load_api_keys(os.getenv("SATURN_API_KEYS_JSON", "")),
        role_permissions=_load_role_permissions(os.getenv("SATURN_ROLE_PERMISSIONS_JSON", "")),
        billing_currency=os.getenv("SATURN_BILLING_CURRENCY", "USD"),
        db_url=os.getenv("SATURN_DB_URL", "mysql+pymysql://saturn:saturn@localhost:3306/saturn"),
    )


def get_database_url() -> str:
    return get_settings().db_url
