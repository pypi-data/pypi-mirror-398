from typing import Dict, Any
from services.base import PDFConverter

try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False


class UnstructuredConverter(PDFConverter):
    """Converter implementation using unstructured.io library"""
    
    def __init__(self):
        self._init_error = None
        if not UNSTRUCTURED_AVAILABLE:
            self._init_error = "unstructured library not installed"
    
    @property
    def name(self) -> str:
        return "unstructured"
    
    @property
    def available(self) -> bool:
        return UNSTRUCTURED_AVAILABLE and self._init_error is None
    
    @property
    def error_message(self) -> str:
        if not UNSTRUCTURED_AVAILABLE:
            return "unstructured library not installed. Install with: uv add unstructured[pdf]"
        return self._init_error
    
    async def convert_to_md(self, file_path: str) -> str:
        """Convert PDF to Markdown using unstructured.io"""
        if not self.available:
            raise RuntimeError("unstructured converter is not available")
        
        try:
            # Partition PDF into document elements
            elements = partition_pdf(file_path)
            
            # Convert elements to markdown
            markdown_lines = []
            for element in elements:
                # Get the text representation
                text = str(element)
                if text.strip():
                    markdown_lines.append(text)
            
            return "\n\n".join(markdown_lines).strip()
        
        except Exception as e:
            raise RuntimeError(f"Unstructured conversion failed: {str(e)}")
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        """Convert PDF to JSON using unstructured.io"""
        if not self.available:
            raise RuntimeError("unstructured converter is not available")
        
        try:
            # Partition PDF into document elements
            elements = partition_pdf(file_path)
            
            # Convert elements to structured format
            json_data = []
            for element in elements:
                json_data.append({
                    "type": type(element).__name__,
                    "text": str(element),
                    "metadata": element.metadata.to_dict() if hasattr(element, 'metadata') else {}
                })
            
            return {
                "content": json_data,
                "format": "json",
                "library": self.name,
                "total_elements": len(json_data)
            }
        
        except Exception as e:
            raise RuntimeError(f"Unstructured JSON conversion failed: {str(e)}")
    
    async def convert_to_text(self, file_path: str) -> str:
        """Convert PDF to plain text using unstructured.io"""
        if not self.available:
            raise RuntimeError("unstructured converter is not available")
        
        try:
            # Partition PDF into document elements
            elements = partition_pdf(file_path)
            
            # Extract plain text
            text_lines = []
            for element in elements:
                text = str(element)
                if text.strip():
                    text_lines.append(text)
            
            return "\n\n".join(text_lines).strip()
        
        except Exception as e:
            raise RuntimeError(f"Unstructured text conversion failed: {str(e)}")

