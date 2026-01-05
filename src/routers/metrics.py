from fastapi import APIRouter, Request

from common.logging import get_logger
from common.metrics import as_dict

router = APIRouter()
logger = get_logger("routers.metrics")


@router.get("/metrics")
def metrics(request: Request) -> dict:
    logger.info("metrics")
    return {"data": as_dict(), "meta": {"request_id": request.state.request_id}}
