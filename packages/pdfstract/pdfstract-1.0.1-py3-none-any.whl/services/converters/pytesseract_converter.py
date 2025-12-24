from typing import Dict, Any
import re
from pathlib import Path

from services.base import PDFConverter

try:
    import pytesseract
    import pdf2image
    from PIL import Image
    from pytesseract import Output
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pytesseract = None
    pdf2image = None
    Image = None
    Output = None
    PYTESSERACT_AVAILABLE = False


class PyTesseractConverter(PDFConverter):
    """Simple Tesseract-based OCR converter (CPU only)."""

    def __init__(self):
        self._init_error = None
        if PYTESSERACT_AVAILABLE:
            try:
                pytesseract.get_tesseract_version()
            except Exception as exc:
                self._init_error = str(exc)

    @property
    def name(self) -> str:
        return "pytesseract"

    @property
    def available(self) -> bool:
        return PYTESSERACT_AVAILABLE and self._init_error is None

    @property
    def error_message(self) -> str:
        if not PYTESSERACT_AVAILABLE:
            return "pytesseract/pillow/pdf2image not installed"
        if self._init_error:
            return f"Tesseract executable missing: {self._init_error}"
        return "Available"

    def _images_from_pdf(self, file_path: str, dpi: int = 200):
        if not pdf2image:
            raise RuntimeError("pdf2image is required")
        images = pdf2image.convert_from_path(file_path, dpi=dpi)
        return images

    def _ocr_image(self, image):
        if image.mode != "RGB":
            image = image.convert("RGB")
        return pytesseract.image_to_string(image, lang="eng")

    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("pytesseract is not available")
        images = self._images_from_pdf(file_path, dpi=200)
        parts = []
        for idx, image in enumerate(images):
            text = self._ocr_image(image)
            if text.strip():
                if len(images) > 1:
                    parts.append(f"## Page {idx + 1}\n\n{text.strip()}")
                else:
                    parts.append(text.strip())
        return "\n\n".join(parts)

    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        markdown = await self.convert_to_md(file_path)
        pages = markdown.split("\n\n## Page ")
        content = []
        for page in pages:
            if page.strip():
                if page.startswith("Page"):
                    header, body = page.split("\n\n", 1)
                    page_num = header.replace("Page ", "").strip()
                    content.append({"page": int(page_num), "content": body, "format": "markdown"})
                else:
                    content.append({"page": 1, "content": page, "format": "markdown"})
        return {"content": content, "format": "json", "library": self.name, "total_pages": len(content)}

    async def convert_to_text(self, file_path: str) -> str:
        markdown = await self.convert_to_md(file_path)
        text = re.sub(r"#+\s+", "", markdown)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"`(.*?)`", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"<[^>]+>", "", text)
        return text



