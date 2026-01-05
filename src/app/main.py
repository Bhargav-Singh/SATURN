import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from common.errors import ERRORS, SaturnError, error_response
from common.logging import configure_logging, get_logger, set_request_context, clear_request_context
from common.metrics import record_request
from db.session import init_db
from routers import agents, auth, billing, health, kb, metrics, tools
from services.auth_service import authenticate


configure_logging()
logger = get_logger("app")

app = FastAPI(title="SATURN Agentic Platform", version="0.1.0")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(tools.router)
app.include_router(kb.router)
app.include_router(billing.router)
app.include_router(metrics.router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.state.request_id = request_id
    set_request_context(request_id=request_id)
    auth = authenticate(request.headers.get("Authorization"))
    request.state.auth = auth
    if auth:
        set_request_context(request_id=request_id, company_id=auth.company_id)
    logger.info("request_start %s %s", request.method, request.url.path)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        record_request(elapsed_ms)
        clear_request_context()
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(SaturnError)
async def saturn_error_handler(request: Request, exc: SaturnError) -> JSONResponse:
    payload = error_response(exc.code, exc.message, exc.details)
    payload["meta"] = {"request_id": request.state.request_id}
    logger.error("saturn_error %s", exc.code)
    return JSONResponse(status_code=exc.definition.http_status, content=payload)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_code = exc.status_code
    if status_code == 400:
        code = "BAD_REQUEST"
    elif status_code == 401:
        code = "AUTH_INVALID"
    elif status_code == 403:
        code = "AUTH_FORBIDDEN"
    elif status_code == 404:
        code = "NOT_FOUND"
    elif status_code == 429:
        code = "RATE_LIMITED"
    else:
        code = "INTERNAL_ERROR"
    payload = error_response(code, str(exc.detail))
    payload["meta"] = {"request_id": request.state.request_id}
    logger.error("http_error %s", code)
    return JSONResponse(status_code=status_code, content=payload)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    payload = error_response("INTERNAL_ERROR")
    payload["meta"] = {"request_id": request.state.request_id}
    logger.error("unhandled_error", exc_info=exc)
    return JSONResponse(status_code=ERRORS["INTERNAL_ERROR"].http_status, content=payload)
