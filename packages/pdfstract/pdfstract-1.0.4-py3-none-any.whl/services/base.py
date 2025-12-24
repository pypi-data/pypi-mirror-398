from abc import ABC, abstractmethod
from typing import Dict, Any
from enum import Enum

class OutputFormat(Enum):
    """Supported output formats"""
    MARKDOWN = "markdown"
    JSON = "json"
    TEXT = "text"
    HTML = "html"

class PDFConverter(ABC):
    """
    Abstract base class for PDF converters (Go-style interface).
    All converters must implement these methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the converter library"""
        pass
    
    @property
    @abstractmethod
    def available(self) -> bool:
        """Check if the converter library is available/installed"""
        pass
    
    @abstractmethod
    async def convert_to_md(self, file_path: str) -> str:
        """Convert PDF to Markdown"""
        pass
    
    @abstractmethod
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        """Convert PDF to JSON"""
        pass
    
    @abstractmethod
    async def convert_to_text(self, file_path: str) -> str:
        """Convert PDF to plain text"""
        pass
    
    def supports_format(self, format_type: OutputFormat) -> bool:
        """Check if converter supports a specific output format"""
        # Default implementation - can be overridden
        return format_type in [
            OutputFormat.MARKDOWN,
            OutputFormat.JSON,
            OutputFormat.TEXT
        ]

