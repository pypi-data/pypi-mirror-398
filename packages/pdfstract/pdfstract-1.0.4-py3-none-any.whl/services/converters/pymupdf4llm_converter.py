from typing import Dict, Any
import re
from services.base import PDFConverter, OutputFormat

try:
    import pymupdf4llm
    PYUPDF4LLM_AVAILABLE = True
except ImportError:
    PYUPDF4LLM_AVAILABLE = False
    pymupdf4llm = None

class PyMuPDF4LLMConverter(PDFConverter):
    """Converter implementation for pymupdf4llm library"""
    
    @property
    def name(self) -> str:
        return "pymupdf4llm"
    
    @property
    def available(self) -> bool:
        return PYUPDF4LLM_AVAILABLE
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("pymupdf4llm is not available")
        return pymupdf4llm.to_markdown(file_path)
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("pymupdf4llm is not available")
        # Convert to markdown first, then structure as JSON
        md_content = await self.convert_to_md(file_path)
        return {
            "content": md_content,
            "format": "markdown",
            "library": self.name
        }
    
    async def convert_to_text(self, file_path: str) -> str:
        # For pymupdf4llm, we can extract text from markdown
        md_content = await self.convert_to_md(file_path)
        # Simple markdown to text conversion (remove markdown syntax)
        text = re.sub(r'#+\s+', '', md_content)  # Remove headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic
        return text

