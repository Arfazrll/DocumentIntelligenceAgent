"""
DocIntel AI — Document Schemas.

Pydantic models for document upload, status tracking, and metadata.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

class DocumentUploadResponse(BaseModel):
    """Response for a single uploaded document."""
    id: str
    filename: str
    status: str
    task_id: Optional[str] = None

class DocumentsUploadResponse(BaseModel):
    """Response for batch document upload."""
    documents: list[DocumentUploadResponse]

class ProgressInfo(BaseModel):
    """Ingestion progress tracking."""
    current_step: str
    steps_completed: int
    total_steps: int = 7
    percentage: int

class DocumentStatusResponse(BaseModel):
    """Document status with progress."""
    id: str
    status: str
    progress: Optional[ProgressInfo] = None
    error_message: Optional[str] = None

class DocumentDetail(BaseModel):
    """Full document detail."""
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: Optional[int] = None
    doc_type: Optional[str] = None
    status: str
    chunk_count: int = 0
    metadata: Optional[dict[str, Any]] = None
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None

class DocumentListItem(BaseModel):
    """Document list item (summary)."""
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    page_count: Optional[int] = None
    doc_type: Optional[str] = None
    status: str
    uploaded_at: datetime
