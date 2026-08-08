"""
DocIntel AI — OCR Parser.

Fallback parser using PaddleOCR for scanned PDFs and images.
"""

import logging
from pathlib import Path
from typing import Any

from app.ingestion.parsers.docling_parser import ParsedElement

logger = logging.getLogger(__name__)

class OCRParser:
    """OCR-based parser using PaddleOCR for scanned documents."""

    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        """Lazy-initialize PaddleOCR."""
        if self._ocr is None:
            from paddleocr import PaddleOCR

            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="en",  # Will also handle Indonesian text
                use_gpu=True,
                show_log=False,
            )
        return self._ocr

    def parse(self, file_path: Path) -> list[ParsedElement]:
        """
        Parse a scanned PDF or image using PaddleOCR.

        Returns list of ParsedElements with bounding boxes.
        """
        logger.info(f"Parsing with PaddleOCR: {file_path.name}")

        elements: list[ParsedElement] = []

        try:
            if file_path.suffix.lower() == ".pdf":
                elements = self._parse_pdf(file_path)
            else:
                elements = self._parse_image(file_path)

            logger.info(f"OCR parsed {len(elements)} elements from {file_path.name}")
            return elements

        except Exception as e:
            logger.error(f"OCR parsing failed for {file_path.name}: {e}")
            raise

    def _parse_pdf(self, file_path: Path) -> list[ParsedElement]:
        """Parse a scanned PDF page by page."""
        import fitz  # PyMuPDF

        elements: list[ParsedElement] = []
        doc = fitz.open(str(file_path))

        for page_num in range(doc.page_count):
            page = doc[page_num]
            # Render page to image for OCR
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")

            # Save temp image
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            # Run OCR on rendered page
            page_elements = self._ocr_image(
                tmp_path, page_number=page_num + 1
            )
            elements.extend(page_elements)

            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)

        doc.close()
        return elements

    def _parse_image(self, file_path: Path) -> list[ParsedElement]:
        """Parse a single image."""
        return self._ocr_image(str(file_path), page_number=1)

    def _ocr_image(
        self, image_path: str, page_number: int = 1
    ) -> list[ParsedElement]:
        """Run OCR on a single image and return parsed elements."""
        result = self.ocr.ocr(image_path, cls=True)

        elements: list[ParsedElement] = []

        if not result or not result[0]:
            return elements

        # Group OCR results into logical blocks
        current_block: list[str] = []
        current_bbox: dict[str, float] | None = None

        for line in result[0]:
            bbox_points = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = line[1][0]
            confidence = line[1][1]

            if confidence < 0.5:
                continue

            # Convert bbox to {x0, y0, x1, y1}
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = {
                "x0": min(x_coords),
                "y0": min(y_coords),
                "x1": max(x_coords),
                "y1": max(y_coords),
            }

            current_block.append(text)

            if current_bbox is None:
                current_bbox = bbox.copy()
            else:
                # Expand bounding box
                current_bbox["x0"] = min(current_bbox["x0"], bbox["x0"])
                current_bbox["y0"] = min(current_bbox["y0"], bbox["y0"])
                current_bbox["x1"] = max(current_bbox["x1"], bbox["x1"])
                current_bbox["y1"] = max(current_bbox["y1"], bbox["y1"])

        # Flush remaining block
        if current_block:
            elements.append(
                ParsedElement(
                    content="\n".join(current_block),
                    element_type="text",
                    page_number=page_number,
                    bbox=current_bbox,
                    metadata={"parser": "paddleocr"},
                )
            )

        return elements

# Singleton instance
ocr_parser = OCRParser()
