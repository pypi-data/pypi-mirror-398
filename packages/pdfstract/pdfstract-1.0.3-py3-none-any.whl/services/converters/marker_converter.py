from typing import Dict, Any
from services.base import PDFConverter

try:
    from marker.converters.pdf import PdfConverter  # type: ignore
    from marker.models import create_model_dict  # type: ignore
    from marker.output import text_from_rendered  # type: ignore
    MARKER_AVAILABLE = True
except ImportError:
    MARKER_AVAILABLE = False
    PdfConverter = None
    create_model_dict = None
    text_from_rendered = None

class MarkerConverter(PDFConverter):
    """Converter implementation for marker library"""
    
    def __init__(self):
        self._converter = None
        if MARKER_AVAILABLE:
            self._converter = PdfConverter(artifact_dict=create_model_dict())  # type: ignore
    
    @property
    def name(self) -> str:
        return "marker"
    
    @property
    def available(self) -> bool:
        return MARKER_AVAILABLE
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("marker is not available")
        rendered = self._converter(file_path)
        text, _, images = text_from_rendered(rendered)  # type: ignore
        return text
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("marker is not available")
        md_content = await self.convert_to_md(file_path)
        return {
            "content": md_content,
            "format": "markdown",
            "library": self.name
        }
    
    async def convert_to_text(self, file_path: str) -> str:
        return await self.convert_to_md(file_path)

