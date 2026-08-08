"""
DocIntel AI — Table Agent.

Handles queries requiring tabular reasoning (e.g. premium lookups).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class TableAgent:
    """Handles tabular data reasoning for premium/benefit lookups."""

    async def process_table_query(
        self,
        query: str,
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Process table-specific queries.

        For MVP: filters chunks to table-type chunks and returns them
        with enhanced metadata for the synthesizer.
        """
        # Filter to table chunks
        table_chunks = [
            c for c in chunks
            if c.get("payload", {}).get("chunk_type") == "table"
        ]

        if table_chunks:
            logger.info(f"Found {len(table_chunks)} table chunks for query")
            return table_chunks

        # If no explicit table chunks, return all chunks
        # (tables might be embedded in text chunks)
        logger.info("No explicit table chunks found, using all chunks")
        return chunks

# Singleton instance
table_agent = TableAgent()
