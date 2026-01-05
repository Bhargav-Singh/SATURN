from fastapi import APIRouter, Depends, Request

from common.auth import AuthContext
from common.errors import SaturnError
from common.logging import get_logger
from common.rbac import require_permission
from services.auth_service import authenticate

router = APIRouter()
logger = get_logger("routers.auth")


def _require_auth(request: Request) -> AuthContext:
    auth = request.state.auth
    if not auth:
        raise SaturnError("AUTH_INVALID")
    return auth


def require_jwt(request: Request) -> AuthContext:
    auth = _require_auth(request)
    if auth.auth_type != "jwt":
        raise SaturnError("AUTH_INVALID")
    return auth


def require_api_key(request: Request) -> AuthContext:
    auth = _require_auth(request)
    if auth.auth_type != "api_key":
        raise SaturnError("AUTH_INVALID")
    return auth


def require_auth(request: Request) -> AuthContext:
    return _require_auth(request)


@router.get("/auth/me")
def me(request: Request, auth: AuthContext = Depends(require_jwt)) -> dict:
    logger.info("auth_me")
    require_permission(auth, "users:read")
    return {
        "data": {
            "user_id": auth.user_id,
            "role": auth.role,
            "company_id": auth.company_id,
        },
        "meta": {"request_id": request.state.request_id},
    }


@router.get("/auth/api-key")
def api_key_info(request: Request, auth: AuthContext = Depends(require_api_key)) -> dict:
    logger.info("auth_api_key")
    return {
        "data": {
            "company_id": auth.company_id,
            "scopes": auth.scopes,
        },
        "meta": {"request_id": request.state.request_id},
    }
