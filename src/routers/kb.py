from fastapi import APIRouter, Depends, Request

from common.auth import AuthContext
from common.logging import get_logger
from common.rbac import require_permission
from routers.auth import require_jwt
from schemas.kb import KbDeleteResponse, KbDocumentResponse, KbReindexResponse, KbUploadRequest, KbUploadResponse
from services.agent_service import get_agent
from services.kb_service import delete_document, list_documents, reindex_document, upload_document

router = APIRouter(prefix="/agents/{agent_id}/kb")
logger = get_logger("routers.kb")


def _envelope(data: dict, request: Request) -> dict:
    return {"data": data, "meta": {"request_id": request.state.request_id}}


@router.post("/upload")
def upload_kb_document(
    request: Request,
    agent_id: str,
    payload: KbUploadRequest,
    auth: AuthContext = Depends(require_jwt),
) -> dict:
    require_permission(auth, "kb:write")
    get_agent(auth.company_id, agent_id)
    doc = upload_document(auth.company_id, agent_id, payload.filename, payload.content)
    logger.info("kb_upload %s", doc.id)
    response = KbUploadResponse(doc_id=doc.id, status=doc.status)
    return _envelope(response.model_dump(), request)


@router.get("")
def list_kb_documents(
    request: Request, agent_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "kb:read")
    get_agent(auth.company_id, agent_id)
    docs = list_documents(auth.company_id, agent_id)
    response = [
        KbDocumentResponse(
            doc_id=doc.id,
            filename=doc.filename,
            status=doc.status,
            error_message=doc.error_message,
        ).model_dump()
        for doc in docs
    ]
    return _envelope({"documents": response}, request)


@router.delete("/{doc_id}")
def delete_kb_document(
    request: Request, agent_id: str, doc_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "kb:write")
    get_agent(auth.company_id, agent_id)
    doc = delete_document(auth.company_id, agent_id, doc_id)
    response = KbDeleteResponse(doc_id=doc.id, status=doc.status)
    return _envelope(response.model_dump(), request)


@router.post("/{doc_id}/reindex")
def reindex_kb_document(
    request: Request, agent_id: str, doc_id: str, auth: AuthContext = Depends(require_jwt)
) -> dict:
    require_permission(auth, "kb:write")
    get_agent(auth.company_id, agent_id)
    doc = reindex_document(auth.company_id, agent_id, doc_id)
    response = KbReindexResponse(doc_id=doc.id, status=doc.status)
    return _envelope(response.model_dump(), request)
