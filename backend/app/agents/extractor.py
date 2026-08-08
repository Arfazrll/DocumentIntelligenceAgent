"""
DocIntel AI — Extraction Agent.

Schema-driven structured extraction using Gemini Flash + Instructor.
"""

import json
import logging
from typing import Any

from app.llm.gemini_client import gemini_client
from app.agents.retriever import retrieval_agent

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """Anda adalah extraction agent untuk dokumen asuransi.
Tugas: Extract SEMUA field yang diminta dari dokumen berdasarkan CONTEXT.

ATURAN:
1. Extract persis seperti tertulis di dokumen.
2. Jika field TIDAK DITEMUKAN, set value ke null.
3. Setiap field HARUS punya citation (chunk_id, page_number).
4. Untuk angka, extract persis (jangan bulatkan).
5. Untuk list/array, extract semua item.
6. Confidence: 1.0 jika verbatim dari doc, 0.8 jika perlu sedikit inference, 0.5 jika uncertain.

SCHEMA FIELDS YANG DIMINTA:
{schema_fields}

CONTEXT (chunks dari dokumen):
{context}

Output HARUS valid JSON sesuai schema yang diminta.
Setiap field harus berformat:
{{
    "field_name": {{
        "value": <extracted_value_or_null>,
        "citation": {{"chunk_id": "...", "page_number": N, "text_snippet": "..."}},
        "confidence": 0.0-1.0,
        "reasoning": "alasan jika null"
    }}
}}"""

class ExtractionAgent:
    """Performs schema-driven structured extraction."""

    async def extract(
        self,
        document_id: str,
        schema: dict[str, Any],
        document_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Extract structured data from document based on schema.

        Args:
            document_id: Target document ID.
            schema: JSON schema defining fields to extract.
            document_ids: List of document IDs to search (defaults to [document_id]).

        Returns:
            Dict of field names to extraction results.
        """
        doc_ids = document_ids or [document_id]

        # Generate queries per field for targeted retrieval
        all_chunks = []
        field_names = list(schema.keys()) if isinstance(schema, dict) else []

        # Retrieve relevant chunks for the overall document
        general_chunks = await retrieval_agent.retrieve(
            query="Extract semua informasi penting dari dokumen ini",
            document_ids=doc_ids,
            top_k_initial=30,
            top_k_final=15,
        )
        all_chunks.extend(general_chunks)

        # Format context
        context_parts = []
        seen_ids = set()
        for chunk in all_chunks:
            chunk_id = chunk.get("id", chunk.get("payload", {}).get("chunk_id", ""))
            if chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)

            content = chunk.get("payload", {}).get("content", "")
            page = chunk.get("payload", {}).get("page_number", "?")
            section = chunk.get("payload", {}).get("section_path", "")

            context_parts.append(
                f"[chunk_id: {chunk_id}] (Page {page}, Section: {section})\n{content}"
            )

        context_str = "\n\n---\n\n".join(context_parts)

        # Format schema fields
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

        prompt = EXTRACTION_SYSTEM_PROMPT.format(
            schema_fields=schema_str,
            context=context_str,
        )

        try:
            response = await gemini_client.generate_json(
                prompt=prompt,
                temperature=0.1,
            )

            result = json.loads(response)
            return result

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"error": str(e)}

# Singleton instance
extraction_agent = ExtractionAgent()
