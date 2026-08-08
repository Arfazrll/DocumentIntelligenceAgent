"""
DocIntel AI — Chunk Model.

Each chunk is a segment of a parsed document, stored for citation resolution.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

class Chunk(Base):
    """Represents a chunk of document content for retrieval and citation."""

    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Structure
    section_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # e.g. "Section 5.2 > Table 3"
    chunk_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # text, table, figure, heading

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    contextual_prefix: Mapped[str | None] = mapped_column(Text, nullable=True)  # enrichment prefix

    # Location in PDF
    bbox_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {x0, y0, x1, y1}

    # Qdrant reference
    qdrant_point_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Extra metadata (JSON as text for SQLite)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk {self.id[:8]}... doc={self.document_id[:8]}... idx={self.chunk_index}>"
