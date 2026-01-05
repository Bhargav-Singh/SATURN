import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Tuple

from common.config import get_settings
from common.errors import SaturnError
from common.logging import get_logger
from db.session import session_scope
from models.core import Invoice as InvoiceModel
from services.usage_service import list_usage_events

logger = get_logger("services.billing")


@dataclass
class InvoiceDraft:
    id: str
    company_id: str
    period_start: date
    period_end: date
    currency: str
    subtotal: float
    total: float
    status: str
    line_items: List[Dict[str, str]]
    created_at: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_period(period: str) -> Tuple[date, date]:
    try:
        year, month = period.split("-")
        start = date(int(year), int(month), 1)
    except ValueError as exc:
        raise SaturnError("BAD_REQUEST", "Invalid period format, expected YYYY-MM") from exc
    if start.month == 12:
        end = date(start.year + 1, 1, 1)
    else:
        end = date(start.year, start.month + 1, 1)
    return start, end


def _aggregate_usage(company_id: str, start: date, end: date) -> Dict[str, float]:
    totals = {"tokens": 0.0, "calls": 0.0, "seconds": 0.0}
    for event in list_usage_events(company_id):
        created = datetime.fromisoformat(event.created_at).date()
        if not (start <= created < end):
            continue
        if event.unit == "tokens":
            totals["tokens"] += event.quantity
        elif event.unit == "calls":
            totals["calls"] += event.quantity
        elif event.unit == "seconds":
            totals["seconds"] += event.quantity
    return totals


def _pricing() -> Dict[str, float]:
    return {"tokens": 0.000002, "calls": 0.01, "seconds": 0.02}


def _to_draft(model: InvoiceModel) -> InvoiceDraft:
    return InvoiceDraft(
        id=model.id,
        company_id=model.company_id,
        period_start=model.period_start,
        period_end=model.period_end,
        currency=model.currency,
        subtotal=model.subtotal,
        total=model.total,
        status=model.status,
        line_items=model.line_items_json or [],
        created_at=model.created_at.isoformat(),
    )


def generate_invoice(company_id: str, period: str) -> InvoiceDraft:
    start, end = _parse_period(period)
    totals = _aggregate_usage(company_id, start, end)
    pricing = _pricing()
    subtotal = (
        totals["tokens"] * pricing["tokens"]
        + totals["calls"] * pricing["calls"]
        + totals["seconds"] * pricing["seconds"]
    )
    line_items = [
        {"item": "tokens", "quantity": str(int(totals["tokens"])), "unit_price": str(pricing["tokens"])},
        {"item": "calls", "quantity": str(int(totals["calls"])), "unit_price": str(pricing["calls"])},
        {"item": "seconds", "quantity": str(int(totals["seconds"])), "unit_price": str(pricing["seconds"])},
    ]
    invoice_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            InvoiceModel(
                id=invoice_id,
                company_id=company_id,
                period_start=start,
                period_end=end,
                currency=get_settings().billing_currency,
                subtotal=round(subtotal, 2),
                total=round(subtotal, 2),
                status="draft",
                line_items_json=line_items,
                created_at=_now(),
            )
        )
    logger.info("invoice_generated %s", invoice_id)
    return get_invoice(company_id, invoice_id)


def list_invoices(company_id: str) -> List[InvoiceDraft]:
    with session_scope() as session:
        rows = session.query(InvoiceModel).filter(InvoiceModel.company_id == company_id).all()
    return [_to_draft(row) for row in rows]


def get_invoice(company_id: str, invoice_id: str) -> InvoiceDraft:
    with session_scope() as session:
        row = (
            session.query(InvoiceModel)
            .filter(InvoiceModel.company_id == company_id, InvoiceModel.id == invoice_id)
            .first()
        )
    if not row:
        raise SaturnError("NOT_FOUND", "Invoice not found")
    return _to_draft(row)


def reset_invoices() -> None:
    with session_scope() as session:
        session.query(InvoiceModel).delete()
