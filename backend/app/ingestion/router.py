"""
DocIntel AI — Ingestion File Router.

Auto-detects file type and routes to the appropriate parser.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

FileType = Literal["pdf", "docx", "xlsx", "image"]

# MIME type to file type mapping
MIME_MAP: dict[str, FileType] = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xlsx",
    "image/jpeg": "image",
    "image/png": "image",
    "image/tiff": "image",
    "image/bmp": "image",
    "image/webp": "image",
}

# Extension fallback
EXT_MAP: dict[str, FileType] = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".tiff": "image",
    ".tif": "image",
    ".bmp": "image",
    ".webp": "image",
}

def detect_file_type(filename: str, content_type: str | None = None) -> FileType:
    """
    Auto-detect file type from filename and optional MIME content type.

    Returns: 'pdf', 'docx', 'xlsx', or 'image'.
    Raises ValueError if type is unsupported.
    """
    # Try MIME type first
    if content_type and content_type in MIME_MAP:
        return MIME_MAP[content_type]

    # Fallback to extension
    ext = Path(filename).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]

    # Try mimetypes library
    guessed_type, _ = mimetypes.guess_type(filename)
    if guessed_type and guessed_type in MIME_MAP:
        return MIME_MAP[guessed_type]

    raise ValueError(f"Unsupported file type: {filename} (content_type={content_type})")

def is_scanned_pdf(file_path: Path) -> bool:
    """
    Heuristic to detect if a PDF is scanned (image-based) vs native text.
    If extractable text is very short relative to page count, likely scanned.
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(file_path))
        total_text_length = 0
        for page in doc:
            total_text_length += len(page.get_text())
        doc.close()

        # Heuristic: if less than 50 chars per page on average, likely scanned
        avg_chars = total_text_length / max(doc.page_count, 1)
        is_scan = avg_chars < 50

        logger.info(
            f"PDF scan detection: avg_chars={avg_chars:.0f}/page, "
            f"is_scanned={is_scan}"
        )
        return is_scan

    except Exception as e:
        logger.warning(f"Error detecting PDF type: {e}. Assuming native.")
        return False
