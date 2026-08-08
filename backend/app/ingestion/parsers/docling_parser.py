"""
DocIntel AI — Docling Parser.

Primary parser for PDF (native) and DOCX using IBM Docling.
Preserves document structure: headings, sections, tables, figures.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class ParsedElement:
    """Represents a parsed document element."""

    def __init__(
        self,
        content: str,
        element_type: str = "text",  # text, table, figure, heading
        page_number: int | None = None,
        section_path: str | None = None,
        bbox: dict[str, float] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.content = content
        self.element_type = element_type
        self.page_number = page_number
        self.section_path = section_path
        self.bbox = bbox
        self.metadata = metadata or {}

class DoclingParser:
    """Parser using IBM Docling for structured document extraction."""

    def __init__(self):
        self._converter = None

    @property
    def converter(self):
        """Lazy-initialize Docling converter."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
        return self._converter

    def parse(self, file_path: Path) -> list[ParsedElement]:
        """
        Parse a document using Docling.

        Returns list of ParsedElements with structure preserved.
        """
        logger.info(f"Parsing with Docling: {file_path.name}")

        try:
            result = self.converter.convert(str(file_path))
            doc = result.document

            elements: list[ParsedElement] = []
            current_section_path = ""

            # Iterate over document elements
            for item in doc.iterate_items():
                element, _level = item if isinstance(item, tuple) else (item, 0)

                # Determine element type and extract content
                element_type = "text"
                content = ""
                page_num = None
                bbox = None

                # Get element label/type
                label = getattr(element, "label", "text")
                if hasattr(label, "value"):
                    label = label.value

                if "heading" in str(label).lower() or "title" in str(label).lower():
                    element_type = "heading"
                    content = element.text if hasattr(element, "text") else str(element)
                    current_section_path = content
                elif "table" in str(label).lower():
                    element_type = "table"
                    # Export table as markdown for better structure preservation
                    if hasattr(element, "export_to_markdown"):
                        content = element.export_to_markdown()
                    else:
                        content = element.text if hasattr(element, "text") else str(element)
                elif "figure" in str(label).lower() or "picture" in str(label).lower():
                    element_type = "figure"
                    content = f"[Figure: {element.text if hasattr(element, 'text') else 'image'}]"
                else:
                    content = element.text if hasattr(element, "text") else str(element)

                # Get provenance (page number, bbox)
                if hasattr(element, "prov") and element.prov:
                    prov = element.prov[0] if isinstance(element.prov, list) else element.prov
                    page_num = getattr(prov, "page_no", None)
                    if hasattr(prov, "bbox"):
                        b = prov.bbox
                        bbox = {
                            "x0": getattr(b, "l", 0),
                            "y0": getattr(b, "t", 0),
                            "x1": getattr(b, "r", 0),
                            "y1": getattr(b, "b", 0),
                        }

                if content and content.strip():
                    elements.append(
                        ParsedElement(
                            content=content.strip(),
                            element_type=element_type,
                            page_number=page_num,
                            section_path=current_section_path,
                            bbox=bbox,
                        )
                    )

            logger.info(f"Docling parsed {len(elements)} elements from {file_path.name}")
            return elements

        except Exception as e:
            logger.error(f"Docling parsing failed for {file_path.name}: {e}")
            raise

    def get_metadata(self, file_path: Path) -> dict[str, Any]:
        """Extract document metadata."""
        try:
            result = self.converter.convert(str(file_path))
            doc = result.document

            metadata = {}
            if hasattr(doc, "name"):
                metadata["title"] = doc.name
            if hasattr(doc, "origin") and doc.origin:
                if hasattr(doc.origin, "filename"):
                    metadata["original_filename"] = doc.origin.filename

            return metadata

        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return {}

    def get_page_count(self, file_path: Path) -> int | None:
        """Get the number of pages in a document."""
        try:
            if file_path.suffix.lower() == ".pdf":
                import fitz
                doc = fitz.open(str(file_path))
                count = doc.page_count
                doc.close()
                return count
        except Exception:
            pass
        return None

# Singleton instance
docling_parser = DoclingParser()
