import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from common.errors import SaturnError
from common.logging import get_logger
from db.session import session_scope
from models.core import KbChunk as KbChunkModel
from models.core import KbDocument as KbDocumentModel

logger = get_logger("services.kb")


@dataclass
class KbDocument:
    id: str
    company_id: str
    agent_id: str
    filename: str
    status: str
    error_message: Optional[str]
    created_at: str


@dataclass
class KbChunk:
    doc_id: str
    chunk_id: str
    content: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_doc(model: KbDocumentModel) -> KbDocument:
    return KbDocument(
        id=model.id,
        company_id=model.company_id,
        agent_id=model.agent_id,
        filename=model.filename,
        status=model.status,
        error_message=model.error_message,
        created_at=model.created_at.isoformat(),
    )


def upload_document(company_id: str, agent_id: str, filename: str, content: str) -> KbDocument:
    doc_id = str(uuid.uuid4())
    with session_scope() as session:
        session.add(
            KbDocumentModel(
                id=doc_id,
                company_id=company_id,
                agent_id=agent_id,
                filename=filename,
                status="indexing",
                created_at=_now(),
            )
        )
    _index_document(company_id, agent_id, doc_id, content)
    logger.info("kb_uploaded %s", doc_id)
    return get_document(company_id, agent_id, doc_id)


def _index_document(company_id: str, agent_id: str, doc_id: str, content: str) -> None:
    chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]
    if not chunks:
        with session_scope() as session:
            session.query(KbDocumentModel).filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.id == doc_id,
            ).update({"status": "failed", "error_message": "Empty document"})
        raise SaturnError("KB_INDEXING_FAILED", "Empty document")
    with session_scope() as session:
        session.query(KbChunkModel).filter(KbChunkModel.doc_id == doc_id).delete()
        for chunk in chunks:
            session.add(
                KbChunkModel(
                    id=str(uuid.uuid4()),
                    doc_id=doc_id,
                    company_id=company_id,
                    agent_id=agent_id,
                    content=chunk,
                )
            )
        session.query(KbDocumentModel).filter(
            KbDocumentModel.company_id == company_id,
            KbDocumentModel.agent_id == agent_id,
            KbDocumentModel.id == doc_id,
        ).update({"status": "ready", "error_message": None})
    logger.info("kb_indexed %s", doc_id)


def list_documents(company_id: str, agent_id: str) -> List[KbDocument]:
    with session_scope() as session:
        rows = (
            session.query(KbDocumentModel)
            .filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.status != "deleted",
            )
            .all()
        )
    return [_to_doc(row) for row in rows]


def get_document(company_id: str, agent_id: str, doc_id: str) -> KbDocument:
    with session_scope() as session:
        row = (
            session.query(KbDocumentModel)
            .filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.id == doc_id,
            )
            .first()
        )
    if not row:
        raise SaturnError("KB_INDEXING_FAILED", "Document not found")
    return _to_doc(row)


def delete_document(company_id: str, agent_id: str, doc_id: str) -> KbDocument:
    with session_scope() as session:
        updated = (
            session.query(KbDocumentModel)
            .filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.id == doc_id,
            )
            .update({"status": "deleted"})
        )
    if not updated:
        raise SaturnError("KB_INDEXING_FAILED", "Document not found")
    logger.info("kb_deleted %s", doc_id)
    return get_document(company_id, agent_id, doc_id)


def reindex_document(company_id: str, agent_id: str, doc_id: str) -> KbDocument:
    with session_scope() as session:
        row = (
            session.query(KbDocumentModel)
            .filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.id == doc_id,
            )
            .first()
        )
        if not row:
            raise SaturnError("KB_INDEXING_FAILED", "Document not found")
        session.query(KbDocumentModel).filter(
            KbDocumentModel.company_id == company_id,
            KbDocumentModel.agent_id == agent_id,
            KbDocumentModel.id == doc_id,
        ).update({"status": "indexing"})
        chunks = (
            session.query(KbChunkModel)
            .filter(KbChunkModel.doc_id == doc_id)
            .all()
        )
        content = "\n\n".join(chunk.content for chunk in chunks) or "Reindexed content"
    _index_document(company_id, agent_id, doc_id, content)
    return get_document(company_id, agent_id, doc_id)


def retrieve(company_id: str, agent_id: str, query: str, top_k: int = 3) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    with session_scope() as session:
        docs = (
            session.query(KbDocumentModel)
            .filter(
                KbDocumentModel.company_id == company_id,
                KbDocumentModel.agent_id == agent_id,
                KbDocumentModel.status == "ready",
            )
            .all()
        )
        for doc in docs:
            chunks = (
                session.query(KbChunkModel)
                .filter(
                    KbChunkModel.doc_id == doc.id,
                    KbChunkModel.company_id == company_id,
                    KbChunkModel.agent_id == agent_id,
                )
                .all()
            )
            for chunk in chunks:
                if len(results) >= top_k:
                    break
                if query.lower() in chunk.content.lower():
                    results.append(
                        {"doc_id": doc.id, "title": doc.filename, "snippet": chunk.content[:200]}
                    )
            if len(results) >= top_k:
                break
    return results


def reset_kb() -> None:
    with session_scope() as session:
        session.query(KbChunkModel).delete()
        session.query(KbDocumentModel).delete()
