"""
DocIntel AI — Document Model.

Tracks uploaded documents through their lifecycle:
PENDING → PARSING → CHUNKING → EMBEDDING → INDEXING → INDEXED | FAILED
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

class Document(Base):
    """Represents an uploaded document and its processing status."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf, docx, xlsx, image
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", index=True
    )  # PENDING, PARSING, CHUNKING, EMBEDDING, INDEXING, INDEXED, FAILED
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Progress tracking
    progress_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata (JSON stored as text for SQLite)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    doc_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # product_proposal, policy_wording, claim_form

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    extraction_jobs = relationship(
        "ExtractionJob", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.id[:8]}... {self.original_filename} [{self.status}]>"
