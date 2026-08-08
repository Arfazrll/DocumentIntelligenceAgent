"""
DocIntel AI — Session & Message Models.

Tracks chat sessions and message history with citations.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

class Session(Base):
    """Represents a chat session scoped to specific documents."""

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # placeholder for MVP
    document_ids_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of doc IDs
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Session {self.id[:8]}... msgs={len(self.messages) if self.messages else '?'}>"

class Message(Base):
    """Represents a single message in a chat session."""

    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI response metadata
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of citations
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    agent_trace_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON agent steps
    llm_metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: model, tokens, cost

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    session = relationship("Session", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.id[:8]}... role={self.role}>"
