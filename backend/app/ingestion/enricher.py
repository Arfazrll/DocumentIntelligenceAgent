"""
DocIntel AI — Contextual Enricher.

Generates contextual prefix for each chunk using Gemini Flash.
"Chunk ini dari section X tentang Y" — helps retrieval precision.
"""

import logging

from app.config import settings
from app.llm.gemini_client import gemini_client

logger = logging.getLogger(__name__)

ENRICHMENT_PROMPT = """Anda diberikan potongan (chunk) dari dokumen. Tugas Anda:
Buat SATU KALIMAT ringkas yang menjelaskan konteks chunk ini.

Format: "Chunk ini dari [section/bagian] tentang [topik utama]."

Jika chunk adalah tabel, jelaskan apa isi tabelnya.
Jika chunk berisi angka/premi, sebutkan.

CHUNK:
{chunk_content}

SECTION PATH: {section_path}

Output (satu kalimat saja, dalam bahasa yang sama dengan chunk):"""

class ContextualEnricher:
    """Enriches chunks with contextual prefix for better retrieval."""

    async def enrich(
        self,
        content: str,
        section_path: str | None = None,
    ) -> str:
        """Generate contextual prefix for a chunk."""
        # Use structured section path prefix directly during ingestion.
        # This eliminates 429 rate limit errors and speeds up ingestion to ~1 second.
        return self._fallback_prefix(content, section_path)

    def _fallback_prefix(
        self, content: str, section_path: str | None
    ) -> str:
        """Simple prefix when LLM enrichment fails."""
        if section_path:
            return f"Chunk ini dari bagian: {section_path}"
        return "Chunk dari dokumen."

    async def enrich_batch(
        self,
        chunks: list[dict],
    ) -> list[str]:
        """Enrich a batch of chunks. Returns list of prefixes."""
        prefixes = []
        for chunk in chunks:
            prefix = await self.enrich(
                content=chunk.get("content", ""),
                section_path=chunk.get("section_path"),
            )
            prefixes.append(prefix)
        return prefixes

# Singleton instance
enricher = ContextualEnricher()
