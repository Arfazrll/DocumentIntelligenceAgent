"""
DocIntel AI — Document Storage (filesystem).

Handles file saving with hash-based naming and duplicate detection.
"""

import hashlib
import shutil
from pathlib import Path
from typing import BinaryIO

from app.config import settings

class FileStorage:
    """Manages document files on the local filesystem."""

    def __init__(self):
        self.base_path = settings.documents_path

    def compute_hash(self, file_content: bytes) -> str:
        """Compute SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def file_exists(self, file_hash: str) -> bool:
        """Check if a file with this hash already exists (duplicate detection)."""
        doc_dir = self.base_path / file_hash
        return doc_dir.exists()

    def save_file(self, file_content: bytes, file_hash: str, original_filename: str) -> Path:
        """
        Save file to disk with hash-based directory naming.

        Structure: ./data/documents/{file_hash}/original.{ext}

        Returns the full path to the saved file.
        """
        ext = Path(original_filename).suffix.lower()
        doc_dir = self.base_path / file_hash
        doc_dir.mkdir(parents=True, exist_ok=True)

        file_path = doc_dir / f"original{ext}"
        file_path.write_bytes(file_content)

        return file_path

    def get_file_path(self, file_hash: str, original_filename: str) -> Path | None:
        """Get the path to a stored file."""
        ext = Path(original_filename).suffix.lower()
        file_path = self.base_path / file_hash / f"original{ext}"
        return file_path if file_path.exists() else None

    def delete_file(self, file_hash: str) -> bool:
        """Delete a document directory and all its contents."""
        doc_dir = self.base_path / file_hash
        if doc_dir.exists():
            shutil.rmtree(doc_dir)
            return True
        return False

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size

# Singleton instance
file_storage = FileStorage()
