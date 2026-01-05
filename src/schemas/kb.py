from typing import Optional

from pydantic import BaseModel


class KbUploadRequest(BaseModel):
    filename: str
    content: str


class KbUploadResponse(BaseModel):
    doc_id: str
    status: str


class KbDeleteResponse(BaseModel):
    doc_id: str
    status: str


class KbReindexResponse(BaseModel):
    doc_id: str
    status: str


class KbDocumentResponse(BaseModel):
    doc_id: str
    filename: str
    status: str
    error_message: Optional[str] = None
