"""
DocIntel AI — Indexer.

Generates embeddings and indexes chunks into Qdrant + PostgreSQL.
"""

import json
import logging
import uuid
from typing import Any

from app.config import settings
from app.ingestion.chunker import ChunkResult
from app.llm.ollama_client import ollama_client
from app.storage.qdrant_store import qdrant_store

logger = logging.getLogger(__name__)

class Indexer:
    """Handles embedding generation and vector indexing."""

    async def index_chunks(
        self,
        chunks: list[ChunkResult],
        document_id: str,
        doc_type: str | None = None,
        enrichment_prefixes: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Generate embeddings and index chunks into Qdrant.

        Returns list of indexed chunk records (for PostgreSQL storage).
        """
        logger.info(f"Indexing {len(chunks)} chunks for document {document_id[:8]}...")

        # Ensure collection exists
        await qdrant_store.ensure_collection()

        # Prepare texts for embedding (with contextual prefix)
        texts_to_embed = []
        for i, chunk in enumerate(chunks):
            prefix = ""
            if enrichment_prefixes and i < len(enrichment_prefixes):
                prefix = enrichment_prefixes[i] + "\n\n"
            texts_to_embed.append(prefix + chunk.content)

        # Generate embeddings in batches
        batch_size = 8
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts_to_embed), batch_size):
            batch = texts_to_embed[i:i + batch_size]
            embeddings = await ollama_client.generate_embeddings_batch(batch)
            all_embeddings.extend(embeddings)

        # Prepare Qdrant points and chunk records
        qdrant_points = []
        chunk_records = []

        for i, (chunk, embedding) in enumerate(zip(chunks, all_embeddings)):
            point_id = str(uuid.uuid4())

            prefix = ""
            if enrichment_prefixes and i < len(enrichment_prefixes):
                prefix = enrichment_prefixes[i]

            # Qdrant point
            payload = {
                "chunk_id": point_id,
                "document_id": document_id,
                "page_number": chunk.page_number,
                "section_path": chunk.section_path,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content,
                "contextual_prefix": prefix,
                "doc_type": doc_type,
                "metadata": chunk.metadata,
            }

            if chunk.bbox:
                payload["bbox"] = chunk.bbox

            qdrant_points.append({
                "id": point_id,
                "dense_vector": embedding,
                "payload": payload,
            })

            # Chunk record for PostgreSQL
            chunk_records.append({
                "id": point_id,
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "section_path": chunk.section_path,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content,
                "contextual_prefix": prefix,
                "bbox_json": json.dumps(chunk.bbox) if chunk.bbox else None,
                "qdrant_point_id": point_id,
                "metadata_json": json.dumps(chunk.metadata) if chunk.metadata else None,
            })

        # Upsert to Qdrant in batches
        for i in range(0, len(qdrant_points), 100):
            batch = qdrant_points[i:i + 100]
            qdrant_store.upsert_points(batch)

        logger.info(
            f"Indexed {len(qdrant_points)} points to Qdrant "
            f"for document {document_id[:8]}"
        )

        return chunk_records

# Singleton instance
indexer = Indexer()
