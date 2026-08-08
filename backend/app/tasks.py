"""
DocIntel AI — Celery Tasks.

Async ingestion pipeline tasks running in Celery workers.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from celery import Celery

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "docintel",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

def run_async(coro):
    """Helper to run async code in Celery (sync) context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@celery_app.task(bind=True, name="ingestion.process_document")
def process_document_task(self, document_id: str, file_path: str, file_type: str):
    """
    Full ingestion pipeline for a single document.

    Steps:
    1. Route to parser (detect type)
    2. Parse document (Docling / PaddleOCR / openpyxl)
    3. Chunk (layout-aware)
    4. Enrich (contextual prefix via Gemini)
    5. Generate embeddings (bge-m3 via Ollama)
    6. Index to Qdrant
    7. Update database status
    """
    logger.info(f"Starting ingestion for document {document_id[:8]}...")

    try:
        run_async(_process_document_async(
            task=self,
            document_id=document_id,
            file_path=file_path,
            file_type=file_type,
        ))
    except Exception as e:
        logger.error(f"Ingestion failed for {document_id[:8]}: {e}")
        run_async(_update_document_status(
            document_id=document_id,
            status="FAILED",
            error_message=str(e),
        ))
        raise

async def _process_document_async(
    task, document_id: str, file_path: str, file_type: str
):
    """Async implementation of the ingestion pipeline."""
    from app.ingestion.router import detect_file_type, is_scanned_pdf
    from app.ingestion.parsers.docling_parser import docling_parser
    from app.ingestion.parsers.ocr_parser import ocr_parser
    from app.ingestion.parsers.xlsx_parser import xlsx_parser
    from app.ingestion.chunker import chunker
    from app.ingestion.enricher import enricher
    from app.ingestion.indexer import indexer

    fp = Path(file_path)

    # ── Step 1: Parsing ──
    await _update_document_status(document_id, "PARSING", progress_step="parsing", progress_percent=10)

    if file_type == "pdf":
        if is_scanned_pdf(fp):
            logger.info(f"Scanned PDF detected, using OCR: {fp.name}")
            elements = ocr_parser.parse(fp)
        else:
            logger.info(f"Native PDF detected, using Docling: {fp.name}")
            elements = docling_parser.parse(fp)
    elif file_type == "docx":
        elements = docling_parser.parse(fp)
    elif file_type == "xlsx":
        elements = xlsx_parser.parse(fp)
    elif file_type == "image":
        elements = ocr_parser.parse(fp)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Get page count
    page_count = docling_parser.get_page_count(fp)

    # ── Step 2: Chunking ──
    await _update_document_status(document_id, "CHUNKING", progress_step="chunking", progress_percent=30)
    chunks = chunker.chunk(elements)

    # ── Step 3: Enrichment ──
    await _update_document_status(document_id, "ENRICHING", progress_step="enriching", progress_percent=45)
    enrichment_prefixes = await enricher.enrich_batch([
        {"content": c.content, "section_path": c.section_path}
        for c in chunks
    ])

    # ── Step 4: Embedding + Indexing ──
    await _update_document_status(document_id, "EMBEDDING", progress_step="embedding", progress_percent=60)

    # ── Step 5: Index to Qdrant ──
    await _update_document_status(document_id, "INDEXING", progress_step="indexing", progress_percent=75)
    chunk_records = await indexer.index_chunks(
        chunks=chunks,
        document_id=document_id,
        enrichment_prefixes=enrichment_prefixes,
    )

    # ── Step 6: Save chunks to database ──
    await _save_chunks_to_db(document_id, chunk_records)

    # ── Step 7: Mark as indexed ──
    await _update_document_status(
        document_id,
        "INDEXED",
        progress_step="completed",
        progress_percent=100,
        page_count=page_count,
    )

    logger.info(
        f"Ingestion complete for {document_id[:8]}: "
        f"{len(chunks)} chunks indexed"
    )

async def _update_document_status(
    document_id: str,
    status: str,
    error_message: str | None = None,
    progress_step: str | None = None,
    progress_percent: int | None = None,
    page_count: int | None = None,
):
    """Update document status in database."""
    from app.models.database import async_session_factory
    from app.models.document import Document
    from sqlalchemy import update

    async with async_session_factory() as session:
        values: dict = {"status": status}
        if error_message:
            values["error_message"] = error_message
        if progress_step:
            values["progress_step"] = progress_step
        if progress_percent is not None:
            values["progress_percent"] = progress_percent
        if page_count is not None:
            values["page_count"] = page_count
        if status == "INDEXED":
            values["indexed_at"] = datetime.now(timezone.utc)

        await session.execute(
            update(Document).where(Document.id == document_id).values(**values)
        )
        await session.commit()

async def _save_chunks_to_db(document_id: str, chunk_records: list[dict]):
    """Save chunk records to PostgreSQL/SQLite."""
    from app.models.database import async_session_factory
    from app.models.chunk import Chunk

    async with async_session_factory() as session:
        for record in chunk_records:
            chunk = Chunk(
                id=record["id"],
                document_id=record["document_id"],
                chunk_index=record["chunk_index"],
                page_number=record.get("page_number"),
                section_path=record.get("section_path"),
                chunk_type=record.get("chunk_type"),
                content=record["content"],
                contextual_prefix=record.get("contextual_prefix"),
                bbox_json=record.get("bbox_json"),
                qdrant_point_id=record.get("qdrant_point_id"),
                metadata_json=record.get("metadata_json"),
            )
            session.add(chunk)
        await session.commit()
