from fastapi import APIRouter, Depends, Request

from common.auth import AuthContext
from common.logging import get_logger
from common.rbac import require_permission
from routers.auth import require_jwt
from services.billing_service import generate_invoice, get_invoice, list_invoices
from services.usage_service import summarize_usage

router = APIRouter()
logger = get_logger("routers.billing")


def _envelope(data: dict, request: Request) -> dict:
    return {"data": data, "meta": {"request_id": request.state.request_id}}


@router.get("/usage/summary")
def usage_summary(
    request: Request, period: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "billing:read")
    invoice = generate_invoice(auth.company_id, period)
    usage = summarize_usage(auth.company_id)
    data = {
        "period": period,
        "tokens_in": usage["tokens_in"],
        "tokens_out": usage["tokens_out"],
        "tool_calls": usage["tool_calls"],
        "kb_queries": usage["kb_queries"],
        "estimated_cost": invoice.total,
    }
    return _envelope(data, request)


@router.get("/invoices")
def list_invoice_endpoint(request: Request, auth: AuthContext = Depends(require_jwt)) -> dict:
    require_permission(auth, "billing:read")
    invoices = list_invoices(auth.company_id)
    data = [
        {
            "invoice_id": invoice.id,
            "period_start": invoice.period_start.isoformat(),
            "period_end": invoice.period_end.isoformat(),
            "status": invoice.status,
            "total": invoice.total,
        }
        for invoice in invoices
    ]
    return _envelope({"invoices": data}, request)


@router.get("/invoices/{invoice_id}")
def get_invoice_endpoint(
    request: Request, invoice_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "billing:read")
    invoice = get_invoice(auth.company_id, invoice_id)
    data = {
        "invoice_id": invoice.id,
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "status": invoice.status,
        "currency": invoice.currency,
        "total": invoice.total,
        "line_items": invoice.line_items,
    }
    return _envelope(data, request)


@router.post("/invoices/generate")
def generate_invoice_endpoint(
    request: Request, period: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "billing:write")
    invoice = generate_invoice(auth.company_id, period)
    data = {
        "invoice_id": invoice.id,
        "period_start": invoice.period_start.isoformat(),
        "period_end": invoice.period_end.isoformat(),
        "status": invoice.status,
        "total": invoice.total,
    }
    logger.info("invoice_draft_created %s", invoice.id)
    return _envelope(data, request)
