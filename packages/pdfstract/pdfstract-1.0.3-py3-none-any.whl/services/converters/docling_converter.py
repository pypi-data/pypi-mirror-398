from typing import Dict, Any
import re
from services.base import PDFConverter

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None

class DoclingConverter(PDFConverter):
    """Converter implementation for docling library"""
    
    def __init__(self):
        self._converter = None
        if DOCLING_AVAILABLE:
            self._converter = DocumentConverter()
    
    @property
    def name(self) -> str:
        return "docling"
    
    @property
    def available(self) -> bool:
        return DOCLING_AVAILABLE
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("docling is not available")
        result = self._converter.convert(file_path)
        return result.document.export_to_markdown()
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("docling is not available")
        md_content = await self.convert_to_md(file_path)
        return {
            "content": md_content,
            "format": "markdown",
            "library": self.name
        }
    
    async def convert_to_text(self, file_path: str) -> str:
        md_content = await self.convert_to_md(file_path)
        text = re.sub(r'#+\s+', '', md_content)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        return text

