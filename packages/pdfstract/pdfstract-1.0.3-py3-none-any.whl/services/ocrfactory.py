from typing import Dict, Optional, List, Union
from services.base import PDFConverter, OutputFormat
from services.converters.pymupdf4llm_converter import PyMuPDF4LLMConverter
from services.converters.markitdown_converter import MarkItDownConverter
from services.converters.marker_converter import MarkerConverter
from services.converters.docling_converter import DoclingConverter
from services.converters.paddleocr_converter import PaddleOCRConverter
from services.converters.deepseekocr_transformers_converter import DeepSeekOCRTransformersConverter
from services.converters.pytesseract_converter import PyTesseractConverter
from services.converters.unstructured_converter import UnstructuredConverter
from services.logger import logger

class OCRFactory:
    """
    Factory class for creating and managing PDF converters.
    Implements singleton pattern for converter instances.
    """
    
    def __init__(self):
        self._converters: Dict[str, PDFConverter] = {}
        self._register_default_converters()
    
    def _register_default_converters(self):
        """Register all available converter implementations"""
        converters = [
            PyMuPDF4LLMConverter(),
            MarkItDownConverter(),
            MarkerConverter(),
            DoclingConverter(),
            PaddleOCRConverter(),
            DeepSeekOCRTransformersConverter(),
            PyTesseractConverter(),
            UnstructuredConverter(),
        ]
        
        for converter in converters:
            if converter.available:
                self._converters[converter.name] = converter
                logger.info(f"Registered converter: {converter.name}")
            else:
                # Provide more detailed error message if available
                error_msg = getattr(converter, 'error_message', 'Dependencies not installed')
                logger.warning(f"Converter {converter.name} is not available: {error_msg}")
    
    def get_converter(self, name: str) -> Optional[PDFConverter]:
        """Get a converter by name"""
        return self._converters.get(name)
    
    def list_available_converters(self) -> List[str]:
        """List all available converter names"""
        return list(self._converters.keys())
    
    def list_all_converters(self) -> List[Dict[str, bool]]:
        """List all converters with their availability status"""
        all_converters = [
            "pymupdf4llm",
            "markitdown",
            "marker",
            "docling",
            "paddleocr",
            "deepseekocr",
            "pytesseract",
            "unstructured"
        ]
        
        result = []
        for name in all_converters:
            converter = self._converters.get(name)
            available = converter is not None and converter.available
            result.append({
                "name": name,
                "available": available,
                "error": None if available else getattr(converter, "error_message", "Unavailable")
            })
        return result
    
    def convert(
        self,
        converter_name: str,
        file_path: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Union[str, Dict]:
        """
        Convert PDF using specified converter and format (synchronous wrapper).
        For CLI usage, this uses asyncio.run() internally.
        
        Args:
            converter_name: Name of the converter to use
            file_path: Path to the PDF file
            output_format: Desired output format
            
        Returns:
            Converted content in the specified format
        """
        import asyncio
        return asyncio.run(self.convert_async(converter_name, file_path, output_format))
    
    async def convert_async(
        self,
        converter_name: str,
        file_path: str,
        output_format: OutputFormat = OutputFormat.MARKDOWN
    ) -> Union[str, Dict]:
        """
        Async version of convert method.
        
        Args:
            converter_name: Name of the converter to use
            file_path: Path to the PDF file
            output_format: Desired output format
            
        Returns:
            Converted content in the specified format
        """
        converter = self.get_converter(converter_name)
        if not converter:
            raise ValueError(f"Converter '{converter_name}' is not available")
        
        if not converter.supports_format(output_format):
            raise ValueError(
                f"Converter '{converter_name}' does not support format '{output_format.value}'"
            )
        
        if output_format == OutputFormat.MARKDOWN:
            return await converter.convert_to_md(file_path)
        elif output_format == OutputFormat.JSON:
            return await converter.convert_to_json(file_path)
        elif output_format == OutputFormat.TEXT:
            return await converter.convert_to_text(file_path)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
