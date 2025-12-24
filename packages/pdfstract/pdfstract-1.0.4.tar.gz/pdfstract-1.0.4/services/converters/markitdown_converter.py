from typing import Dict, Any
import re
from services.base import PDFConverter

try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False
    MarkItDown = None

class MarkItDownConverter(PDFConverter):
    """Converter implementation for markitdown library"""
    
    def __init__(self):
        self._converter = None
        if MARKITDOWN_AVAILABLE:
            self._converter = MarkItDown()
    
    @property
    def name(self) -> str:
        return "markitdown"
    
    @property
    def available(self) -> bool:
        return MARKITDOWN_AVAILABLE
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("markitdown is not available")
        result = self._converter.convert(file_path)
        return result.text_content
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("markitdown is not available")
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

