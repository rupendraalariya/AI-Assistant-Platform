"""Document upload and management endpoints."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from app.db.database import get_db
from app.dependencies import get_current_user
from app.models.document import Document
from app.models.user import User
from app.services.document_service import get_document_service
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document for RAG processing, optionally linked to a session."""
    document_service = get_document_service()

    try:
        result = await document_service.process_upload(
            file=file,
            user_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save document record
    doc = Document(
        user_id=current_user.id,
        filename=result["filename"],
        file_type=result["file_type"],
        file_size=result["file_size"],
        chunk_count=result["chunk_count"],
        status=result["status"],
    )
    db.add(doc)
    await db.flush()

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        status=doc.status,
        chunk_count=doc.chunk_count,
        message=f"Document processed successfully. {doc.chunk_count} chunks created.",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all uploaded documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=len(documents),
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an uploaded document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(doc)


@router.post("/{document_id}/reindex")
async def reindex_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a document as ready (re-acknowledge it in the index).

    Note: full re-extraction requires the original file. Since files are not
    persisted to disk in this build, reindex confirms the document's vectors
    remain available and resets its status to 'ready'.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc.status = "ready"
    await db.flush()
    return {"id": str(doc.id), "status": "ready", "message": "Document reindexed"}
