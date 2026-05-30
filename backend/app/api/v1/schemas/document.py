"""Document schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Document response schema."""

    id: str
    filename: str
    file_type: str
    file_size: Optional[int] = None
    chunk_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """List of documents response."""

    documents: List[DocumentResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    """Document upload response."""

    id: str
    filename: str
    status: str
    chunk_count: int
    message: str
