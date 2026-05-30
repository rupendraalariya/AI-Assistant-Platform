"""Document Service - File processing for RAG pipeline."""

import os
import tempfile
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import UploadFile

from app.config import get_settings
from app.services.rag_service import get_rag_service
from app.utils.helpers import sanitize_filename
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Supported file types
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/csv": "csv",
    "application/csv": "csv",
    "application/vnd.ms-excel": "csv",
}

# Extension fallback (browsers send inconsistent content types)
EXTENSION_TYPES = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".csv": "csv",
    ".md": "txt",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class DocumentService:
    """Service for processing uploaded documents."""

    def __init__(self):
        self.rag_service = get_rag_service()

    async def process_upload(
        self,
        file: UploadFile,
        user_id: UUID,
        session_id: Optional[str] = None,
    ) -> Dict:
        """Process an uploaded file and ingest into vector store.

        Args:
            file: Uploaded file
            user_id: ID of the uploading user
            session_id: Optional session to associate the document with

        Returns:
            Dict with processing results
        """
        # Validate file
        self._validate_file(file)

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Extract text based on file type
        filename = sanitize_filename(file.filename or "unnamed")
        file_type = self._get_file_type(file.content_type, filename)
        logger.info(f"[DOC] File uploaded: {filename} ({file_type}, {file_size} bytes)")

        text = await self._extract_text(content, file_type)
        logger.info(f"[DOC] Text extracted: {len(text)} chars from {filename}")

        if not text.strip():
            raise ValueError("No text content could be extracted from the file")

        # Ingest into RAG pipeline with user/session metadata for filtering
        metadata = {
            "source": filename,
            "user_id": str(user_id),
            "session_id": str(session_id) if session_id else "",
            "file_type": file_type,
        }

        chunk_count = await self.rag_service.ingest_documents(
            texts=[text],
            metadatas=[metadata],
        )

        logger.info(
            "[DOC] Document processed",
            filename=filename,
            file_type=file_type,
            chunks=chunk_count,
        )

        return {
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "chunk_count": chunk_count,
            "status": "ready",
        }

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file by content type or extension."""
        import os
        ext = os.path.splitext(file.filename or "")[1].lower()
        if (file.content_type not in SUPPORTED_TYPES) and (ext not in EXTENSION_TYPES):
            raise ValueError(
                f"Unsupported file type: {file.content_type or ext}. "
                f"Supported: PDF, DOCX, TXT, CSV"
            )

    def _get_file_type(self, content_type: Optional[str], filename: str = "") -> str:
        """Get file type from content type, falling back to extension."""
        if content_type and content_type in SUPPORTED_TYPES:
            return SUPPORTED_TYPES[content_type]
        import os
        ext = os.path.splitext(filename)[1].lower()
        return EXTENSION_TYPES.get(ext, "txt")

    async def _extract_text(self, content: bytes, file_type: str) -> str:
        """Extract text from file content."""
        if file_type == "pdf":
            return self._extract_pdf(content)
        elif file_type == "docx":
            return self._extract_docx(content)
        elif file_type in ("txt", "csv"):
            return content.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF."""
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(content))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n\n".join(text_parts)

    def _extract_docx(self, content: bytes) -> str:
        """Extract text from DOCX."""
        from docx import Document
        import io

        doc = Document(io.BytesIO(content))
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return "\n\n".join(text_parts)


def get_document_service() -> DocumentService:
    """Factory function for document service."""
    return DocumentService()
