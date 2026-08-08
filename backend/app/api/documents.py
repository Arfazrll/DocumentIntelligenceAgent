"""
DocIntel AI — Documents API.

Endpoints: upload, status, detail, list, delete.
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chunk import Chunk
from app.models.database import get_session
from app.models.document import Document
from app.schemas.document import (
    DocumentDetail,
    DocumentListItem,
    DocumentStatusResponse,
    DocumentsUploadResponse,
    DocumentUploadResponse,
    ProgressInfo,
)
from app.storage import file_storage
from app.ingestion.router import detect_file_type
from app.tasks import process_document_task

logger = logging.getLogger(__name__)
router = APIRouter()

PROGRESS_STEPS = {
    "parsing": (1, 14),
    "chunking": (2, 28),
    "enriching": (3, 42),
    "embedding": (4, 57),
    "indexing": (5, 71),
    "saving": (6, 85),
    "completed": (7, 100),
}

@router.post("/upload", response_model=DocumentsUploadResponse, status_code=202)
async def upload_documents(
    files: list[UploadFile] = File(...),
    doc_type: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_session),
):
    """Upload one or more documents for async processing."""
    if len(files) > settings.MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_FILES_PER_UPLOAD} files per upload.",
        )

    results: list[DocumentUploadResponse] = []

    for upload_file in files:
        try:
            content = await upload_file.read()

            if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                results.append(DocumentUploadResponse(
                    id="", filename=upload_file.filename or "unknown",
                    status="REJECTED", task_id=None,
                ))
                continue

            file_type = detect_file_type(
                upload_file.filename or "unknown", upload_file.content_type,
            )

            file_hash = file_storage.compute_hash(content)

            # Duplicate check
            existing = await session.execute(
                select(Document).where(Document.file_hash == file_hash)
            )
            if existing.scalar_one_or_none():
                results.append(DocumentUploadResponse(
                    id="", filename=upload_file.filename or "unknown",
                    status="DUPLICATE", task_id=None,
                ))
                continue

            file_path = file_storage.save_file(
                content, file_hash, upload_file.filename or "file"
            )

            doc = Document(
                file_hash=file_hash,
                original_filename=upload_file.filename or "unknown",
                file_type=file_type,
                file_size_bytes=len(content),
                file_path=str(file_path),
                doc_type=doc_type,
                status="PENDING",
            )
            session.add(doc)
            await session.commit()

            try:
                import asyncio
                from app.tasks import process_document_task

                loop = asyncio.get_running_loop()
                loop.run_in_executor(
                    None,
                    process_document_task,
                    doc.id,
                    str(file_path),
                    file_type,
                )
                task_id = f"bg-{doc.id[:8]}"
            except Exception as task_err:
                logger.warning(f"Could not dispatch bg task for document {doc.id}: {task_err}")
                task_id = None

            results.append(DocumentUploadResponse(
                id=doc.id, filename=upload_file.filename or "unknown",
                status="PENDING", task_id=task_id,
            ))

        except Exception as e:
            logger.error(f"Error processing upload for {upload_file.filename}: {e}", exc_info=True)
            results.append(DocumentUploadResponse(
                id="", filename=upload_file.filename or "unknown",
                status=f"ERROR: {str(e)}", task_id=None,
            ))

    return DocumentsUploadResponse(documents=results)

@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str, session: AsyncSession = Depends(get_session),
):
    """Get document processing status with progress."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    progress = None
    if doc.progress_step and doc.progress_step in PROGRESS_STEPS:
        steps_completed, percentage = PROGRESS_STEPS[doc.progress_step]
        progress = ProgressInfo(
            current_step=doc.progress_step, steps_completed=steps_completed,
            total_steps=7, percentage=doc.progress_percent or percentage,
        )

    return DocumentStatusResponse(
        id=doc.id, status=doc.status, progress=progress, error_message=doc.error_message,
    )

@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str, session: AsyncSession = Depends(get_session),
):
    """Get full document details."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_count_result = await session.execute(
        select(func.count(Chunk.id)).where(Chunk.document_id == document_id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    metadata = json.loads(doc.metadata_json) if doc.metadata_json else None

    return DocumentDetail(
        id=doc.id, filename=doc.original_filename, file_type=doc.file_type,
        file_size_bytes=doc.file_size_bytes, page_count=doc.page_count,
        doc_type=doc.doc_type, status=doc.status, chunk_count=chunk_count,
        metadata=metadata, uploaded_at=doc.uploaded_at, indexed_at=doc.indexed_at,
    )

def clean_chunk_text(text: str) -> str:
    """Clean raw Docling comments, rich cell tags, and empty markdown lines."""
    if not text:
        return ""
    import re
    cleaned = re.sub(r"<!--.*?-->", "", text)
    lines = []
    for line in cleaned.splitlines():
        line_s = line.strip()
        if re.match(r"^[\s\|\-\:\+\=]+$", line_s):
            continue
        if line_s:
            lines.append(line_s)
    result = "\n".join(lines).strip()
    return result

@router.get("/{document_id}/highlights")
async def get_document_highlights(
    document_id: str, session: AsyncSession = Depends(get_session)
):
    """Extract key structural highlights, essential clauses, and tables from the document."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_res = await session.execute(
        select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.chunk_index.asc()).limit(200)
    )
    chunks = chunks_res.scalars().all()

    highlights = []
    tables = []

    for c in chunks:
        raw_text = clean_chunk_text(c.content)
        if not raw_text or len(raw_text) < 15:
            continue

        content_lower = raw_text.lower()
        sec = c.section_path or "Utama"
        page = c.page_number or 1

        title_text = sec if sec.lower().startswith("ketentuan") else f"Ketentuan {sec}"

        if any(w in content_lower for w in ["luas jaminan", "manfaat", "pertanggungan", "coverage", "benefit", "paket"]):
            if len(highlights) < 12:
                highlights.append({
                    "id": f"hl-{c.id[:8]}",
                    "category": "Cakupan & Pertanggungan",
                    "title": title_text,
                    "summary": raw_text[:280] + ("..." if len(raw_text) > 280 else ""),
                    "full_text": raw_text,
                    "page_number": page,
                    "chunk_id": c.id,
                    "confidence": 0.96,
                    "tags": ["Pertanggungan", "Manfaat", f"Hal {page}"]
                })

        elif any(w in content_lower for w in ["pengecualian", "tidak dijamin", "exclusion", "di luar"]):
            if len(highlights) < 12:
                highlights.append({
                    "id": f"hl-{c.id[:8]}",
                    "category": "Pengecualian & Pembatasan",
                    "title": f"Pembatasan {sec}",
                    "summary": raw_text[:280] + ("..." if len(raw_text) > 280 else ""),
                    "full_text": raw_text,
                    "page_number": page,
                    "chunk_id": c.id,
                    "confidence": 0.93,
                    "tags": ["Pengecualian", "Pembatasan", f"Hal {page}"]
                })

        elif any(w in content_lower for w in ["klaim", "prosedur", "syarat", "hari kalender", "dokumen klaim"]):
            if len(highlights) < 12:
                highlights.append({
                    "id": f"hl-{c.id[:8]}",
                    "category": "Prosedur & Batas Waktu",
                    "title": f"Prosedur Klaim - {sec}",
                    "summary": raw_text[:280] + ("..." if len(raw_text) > 280 else ""),
                    "full_text": raw_text,
                    "page_number": page,
                    "chunk_id": c.id,
                    "confidence": 0.95,
                    "tags": ["Prosedur", "Klaim", f"Hal {page}"]
                })

        if (c.chunk_type == "table" or "|" in raw_text or "\t" in raw_text) and len(raw_text) > 30:
            if len(tables) < 6:
                tables.append({
                    "id": f"tbl-{c.id[:8]}",
                    "title": f"Tabel Struktur {sec}",
                    "page_number": page,
                    "content_snippet": raw_text[:400],
                    "full_text": raw_text,
                })

    if not highlights and chunks:
        for c in chunks:
            raw_text = clean_chunk_text(c.content)
            if not raw_text or len(raw_text) < 20:
                continue
            if len(highlights) >= 8:
                break
            highlights.append({
                "id": f"hl-{c.id[:8]}",
                "category": "Bagian Utama Dokumen",
                "title": c.section_path or f"Bagian Hal {c.page_number or 1}",
                "summary": raw_text[:280] + ("..." if len(raw_text) > 280 else ""),
                "full_text": raw_text,
                "page_number": c.page_number or 1,
                "chunk_id": c.id,
                "confidence": 0.90,
                "tags": ["Inti Dokumen", f"Hal {c.page_number or 1}"]
            })

    return {
        "document_id": doc.id,
        "filename": doc.original_filename,
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "doc_type": doc.doc_type or "Dokumen Utama",
        "total_chunks": len(chunks),
        "highlights": highlights,
        "tables": tables,
    }

@router.get("", response_model=list[DocumentListItem])
async def list_documents(session: AsyncSession = Depends(get_session)):
    """List all documents."""
    result = await session.execute(select(Document).order_by(Document.uploaded_at.desc()))
    docs = result.scalars().all()
    return [
        DocumentListItem(
            id=d.id, filename=d.original_filename, file_type=d.file_type,
            file_size_bytes=d.file_size_bytes, page_count=d.page_count,
            doc_type=d.doc_type, status=d.status, uploaded_at=d.uploaded_at,
        )
        for d in docs
    ]

@router.delete("/{document_id}")
async def delete_document(
    document_id: str, session: AsyncSession = Depends(get_session),
):
    """Delete a document and all associated data."""
    result = await session.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.storage.qdrant_store import qdrant_store
    try:
        qdrant_store.delete_by_document(document_id)
    except Exception as e:
        logger.warning(f"Failed to delete from Qdrant: {e}")

    file_storage.delete_file(doc.file_hash)
    await session.delete(doc)

    return {"status": "deleted", "document_id": document_id}
