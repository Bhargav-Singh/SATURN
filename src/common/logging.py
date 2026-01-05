import json
import logging
import sys
import time
from contextvars import ContextVar
from typing import Any, Dict, Optional

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_company_id_ctx: ContextVar[Optional[str]] = ContextVar("company_id", default=None)
_agent_id_ctx: ContextVar[Optional[str]] = ContextVar("agent_id", default=None)


def set_request_context(
    request_id: Optional[str],
    company_id: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> None:
    _request_id_ctx.set(request_id)
    _company_id_ctx.set(company_id)
    _agent_id_ctx.set(agent_id)


def clear_request_context() -> None:
    _request_id_ctx.set(None)
    _company_id_ctx.set(None)
    _agent_id_ctx.set(None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = _request_id_ctx.get()
        if request_id:
            payload["request_id"] = request_id
        company_id = _company_id_ctx.get()
        if company_id:
            payload["company_id"] = company_id
        agent_id = _agent_id_ctx.get()
        if agent_id:
            payload["agent_id"] = agent_id
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
