"""
DocIntel AI — Extraction Job Model.

Tracks async structured extraction jobs.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

class ExtractionJob(Base):
    """Represents an async structured extraction job."""

    __tablename__ = "extraction_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    schema_definition_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON schema

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, RUNNING, COMPLETED, FAILED

    # Results (JSON as text for SQLite)
    result_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="extraction_jobs")

    def __repr__(self) -> str:
        return f"<ExtractionJob {self.id[:8]}... [{self.status}]>"
