"""
DocIntel AI — Extraction API.

Endpoint for structured data extraction from documents.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.extractor import extraction_agent
from app.models.database import get_session
from app.models.document import Document
from app.models.extraction import ExtractionJob
from app.schemas.extraction import ExtractionRequest, ExtractionResponse, PREBUILT_SCHEMAS

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/extract", response_model=ExtractionResponse)
async def extract_from_document(
    request: ExtractionRequest,
    db: AsyncSession = Depends(get_session),
):
    """
    Run structured extraction on a document using a schema.

    Supports pre-built schemas (insurance_product) and custom schemas.
    """
    # Validate document
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id, Document.status == "INDEXED"
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=400,
            detail="Document not found or not yet indexed.",
        )

    # Get schema
    schema = request.custom_schema
    if not schema and request.schema_type in PREBUILT_SCHEMAS:
        # Convert Pydantic model to JSON schema
        model_class = PREBUILT_SCHEMAS[request.schema_type]
        schema = model_class.model_json_schema()

    if not schema:
        raise HTTPException(
            status_code=400,
            detail=f"Schema '{request.schema_type}' not found. "
            f"Available: {list(PREBUILT_SCHEMAS.keys())}",
        )

    # Create extraction job
    job = ExtractionJob(
        document_id=request.document_id,
        schema_definition_json=json.dumps(schema),
        status="RUNNING",
    )
    db.add(job)
    await db.flush()

    try:
        # Run extraction
        result_data = await extraction_agent.extract(
            document_id=request.document_id,
            schema=schema,
        )

        # Update job
        job.status = "COMPLETED"
        job.result_json = json.dumps(result_data, ensure_ascii=False)
        job.completed_at = datetime.now(timezone.utc)

        return ExtractionResponse(
            extraction_id=job.id,
            document_id=request.document_id,
            status="COMPLETED",
            result=result_data,
        )

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        job.status = "FAILED"
        job.error_message = str(e)

        return ExtractionResponse(
            extraction_id=job.id,
            document_id=request.document_id,
            status="FAILED",
            error_message=str(e),
        )

@router.get("/extract/{job_id}")
async def get_extraction_result(
    job_id: str,
    db: AsyncSession = Depends(get_session),
):
    """Get extraction job result."""
    result = await db.execute(
        select(ExtractionJob).where(ExtractionJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Extraction job not found")

    return ExtractionResponse(
        extraction_id=job.id,
        document_id=job.document_id,
        status=job.status,
        result=json.loads(job.result_json) if job.result_json else None,
        error_message=job.error_message,
    )
