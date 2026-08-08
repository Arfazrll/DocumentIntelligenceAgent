"""
DocIntel AI — Layout-Aware Chunker.

Section-based chunking that preserves document structure.
NOT character-based — chunks are created at logical boundaries.
"""

import logging
from typing import Any

from app.config import settings
from app.ingestion.parsers.docling_parser import ParsedElement

logger = logging.getLogger(__name__)

class ChunkResult:
    """Result of chunking a document."""

    def __init__(
        self,
        content: str,
        chunk_index: int,
        chunk_type: str = "text",
        page_number: int | None = None,
        section_path: str | None = None,
        bbox: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.chunk_type = chunk_type
        self.page_number = page_number
        self.section_path = section_path
        self.bbox = bbox
        self.metadata = metadata or {}

class LayoutAwareChunker:
    """
    Chunks documents based on logical structure (sections, tables, headings).
    Not character-based splitting.
    """

    def __init__(self):
        self.max_tokens = settings.CHUNK_SIZE_TOKENS
        self.overlap_tokens = settings.CHUNK_OVERLAP_TOKENS

    def chunk(self, elements: list[ParsedElement]) -> list[ChunkResult]:
        """
        Create chunks from parsed elements.

        Strategy:
        - Tables are always their own chunk (never split)
        - Headings are prepended to the following content
        - Text is merged until max_tokens, then split at sentence boundaries
        """
        chunks: list[ChunkResult] = []
        current_text: list[str] = []
        current_section = ""
        current_page = None
        current_bbox = None
        chunk_index = 0

        for element in elements:
            # Update section path
            if element.element_type == "heading":
                # If we have accumulated text, flush it
                if current_text:
                    chunks.append(self._create_chunk(
                        content="\n\n".join(current_text),
                        chunk_index=chunk_index,
                        chunk_type="text",
                        page_number=current_page,
                        section_path=current_section,
                        bbox=current_bbox,
                    ))
                    chunk_index += 1
                    current_text = []
                    current_bbox = None

                current_section = element.content
                current_page = element.page_number
                # Prepend heading to next chunk
                current_text.append(f"## {element.content}")
                continue

            # Tables are always their own chunk
            if element.element_type == "table":
                # Flush accumulated text first
                if current_text:
                    chunks.append(self._create_chunk(
                        content="\n\n".join(current_text),
                        chunk_index=chunk_index,
                        chunk_type="text",
                        page_number=current_page,
                        section_path=current_section,
                        bbox=current_bbox,
                    ))
                    chunk_index += 1
                    current_text = []
                    current_bbox = None

                # Table as its own chunk
                table_content = element.content
                if current_section:
                    table_content = f"## {current_section}\n\n{table_content}"

                chunks.append(self._create_chunk(
                    content=table_content,
                    chunk_index=chunk_index,
                    chunk_type="table",
                    page_number=element.page_number or current_page,
                    section_path=current_section,
                    bbox=element.bbox,
                ))
                chunk_index += 1
                continue

            # Regular text — accumulate
            estimated_tokens = self._estimate_tokens(
                "\n\n".join(current_text + [element.content])
            )

            if estimated_tokens > self.max_tokens and current_text:
                # Flush current chunk
                chunks.append(self._create_chunk(
                    content="\n\n".join(current_text),
                    chunk_index=chunk_index,
                    chunk_type="text",
                    page_number=current_page,
                    section_path=current_section,
                    bbox=current_bbox,
                ))
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_text)
                current_text = overlap_text + [element.content]
                current_bbox = element.bbox
            else:
                current_text.append(element.content)
                if element.page_number:
                    current_page = element.page_number
                if element.bbox and current_bbox is None:
                    current_bbox = element.bbox

        # Flush remaining text
        if current_text:
            chunks.append(self._create_chunk(
                content="\n\n".join(current_text),
                chunk_index=chunk_index,
                chunk_type="text",
                page_number=current_page,
                section_path=current_section,
                bbox=current_bbox,
            ))

        logger.info(f"Created {len(chunks)} chunks from {len(elements)} elements")
        return chunks

    def _create_chunk(self, **kwargs) -> ChunkResult:
        """Create a ChunkResult."""
        return ChunkResult(**kwargs)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars for English/Indonesian)."""
        return len(text) // 4

    def _get_overlap(self, texts: list[str]) -> list[str]:
        """Get overlap text from the end of current chunks."""
        if not texts:
            return []

        # Take last element as overlap if it fits
        last = texts[-1]
        if self._estimate_tokens(last) <= self.overlap_tokens:
            return [last]

        # Otherwise take last N chars
        overlap_chars = self.overlap_tokens * 4
        return [last[-overlap_chars:]]

# Singleton instance
chunker = LayoutAwareChunker()
