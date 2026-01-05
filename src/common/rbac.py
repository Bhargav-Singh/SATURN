from typing import Iterable

from common.auth import AuthContext
from common.config import get_settings
from common.errors import SaturnError


def require_permission(auth: AuthContext, permission: str) -> None:
    settings = get_settings()
    role = auth.role or "viewer"
    allowed = settings.role_permissions.get(role, [])
    if "*" in allowed:
        return
    if permission not in allowed:
        raise SaturnError("AUTH_FORBIDDEN")


def has_scope(auth: AuthContext, scopes: Iterable[str]) -> bool:
    if not scopes:
        return True
    if "*" in auth.scopes:
        return True
    return any(scope in auth.scopes for scope in scopes)
