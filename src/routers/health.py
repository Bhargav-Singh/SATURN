from fastapi import APIRouter, Request

from common.logging import get_logger

router = APIRouter()
logger = get_logger("routers.health")


def _envelope(data: dict, request: Request) -> dict:
    return {"data": data, "meta": {"request_id": request.state.request_id}}


@router.get("/health")
def health(request: Request) -> dict:
    logger.info("health_check")
    return _envelope({"status": "ok"}, request)


@router.get("/ready")
def readiness(request: Request) -> dict:
    logger.info("readiness_check")
    return _envelope({"status": "ready"}, request)
