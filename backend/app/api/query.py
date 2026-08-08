"""
DocIntel AI — Query API.

Endpoint for Q&A queries with orchestrator integration.
"""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import run_orchestrator
from app.models.database import get_session
from app.models.document import Document
from app.models.session import Message, Session
from app.schemas.query import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Submit a Q&A query against indexed documents.

    Runs the full multi-agent orchestrator pipeline:
    Planner → Retriever → Synthesizer → Verifier → Answer.
    """
    # Validate document IDs
    if request.document_ids:
        for doc_id in request.document_ids:
            result = await db.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.status.in_(["INDEXED", "COMPLETED"])
                )
            )
            if not result.scalar_one_or_none():
                raise HTTPException(
                    status_code=400,
                    detail=f"Document {doc_id} not found or not yet indexed.",
                )

    # Get or create session
    session_id = request.session_id
    if session_id:
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = Session(
            document_ids_json=json.dumps(request.document_ids),
        )
        db.add(session)
        await db.flush()
        session_id = session.id

    # Get conversation history
    history = []
    if session_id:
        msgs_result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(10)
        )
        msgs = msgs_result.scalars().all()
        history = [
            {"role": m.role, "content": m.content}
            for m in reversed(msgs)
        ]

    # Get document summaries
    doc_summaries = []
    for doc_id in request.document_ids:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc_summaries.append({
                "filename": doc.original_filename,
                "doc_type": doc.doc_type,
                "page_count": doc.page_count,
            })

    # Save user message
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=request.query,
    )
    db.add(user_msg)
    await db.flush()

    # Run orchestrator
    response = await run_orchestrator(
        query=request.query,
        document_ids=request.document_ids,
        session_id=session_id,
        history=history,
        document_summaries=doc_summaries,
    )

    # Set message ID
    msg_id = str(uuid.uuid4())
    response.message_id = msg_id

    # Save assistant message
    assistant_msg = Message(
        id=msg_id,
        session_id=session_id,
        role="assistant",
        content=response.answer,
        citations_json=json.dumps([c.model_dump() for c in response.citations]),
        confidence=response.confidence.score if response.confidence else None,
        agent_trace_json=json.dumps(response.trace.model_dump()) if response.trace else None,
    )
    db.add(assistant_msg)

    return response

@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get chat messages for a session."""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "citations": json.loads(m.citations_json) if m.citations_json else None,
                "confidence": m.confidence,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    }
