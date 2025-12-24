from typing import Dict, Any
import re
from pathlib import Path
from services.base import PDFConverter

PADDLEOCR_AVAILABLE = False
PPStructureV3 = None
PADDLEOCR_ERROR = None

try:
    from paddleocr import PPStructureV3
    PADDLEOCR_AVAILABLE = True
except ImportError as e:
    PADDLEOCR_ERROR = f"Import error: {str(e)}"
    PADDLEOCR_AVAILABLE = False

class PaddleOCRConverter(PDFConverter):
    """Converter implementation for PaddleOCR library"""
    
    def __init__(self):
        self._pipeline = None
        self._error_message = PADDLEOCR_ERROR
        if PADDLEOCR_AVAILABLE:
            try:
                self._pipeline = PPStructureV3(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False
                )
            except Exception as e:
                # If initialization fails, mark as unavailable
                self._pipeline = None
                self._error_message = f"Initialization failed: {str(e)}"
    
    @property
    def name(self) -> str:
        return "paddleocr"
    
    @property
    def available(self) -> bool:
        return PADDLEOCR_AVAILABLE and self._pipeline is not None
    
    @property
    def error_message(self) -> str:
        if not PADDLEOCR_AVAILABLE:
            return self._error_message or "paddleocr not installed"
        if self._pipeline is None:
            return self._error_message or "Failed to initialize PPStructureV3"
        return None
    
    async def convert_to_md(self, file_path: str) -> str:
        if not self.available:
            raise RuntimeError("paddleocr is not available")
        
        try:
            # Run prediction
            output = self._pipeline.predict(input=file_path)
            
            # Collect markdown from all results
            markdown_parts = []
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save markdown files to temp directory
                for res in output:
                    res.save_to_markdown(save_path=temp_dir)
                
                # Find all markdown files in the temp directory
                md_files = sorted(Path(temp_dir).glob("*.md"))
                
                if md_files:
                    # Read all markdown files
                    for md_file in md_files:
                        markdown_parts.append(md_file.read_text(encoding='utf-8'))
                else:
                    # Fallback: try to get markdown from result object
                    for res in output:
                        if hasattr(res, 'to_markdown'):
                            markdown_parts.append(res.to_markdown())
                        elif hasattr(res, 'markdown'):
                            markdown_parts.append(res.markdown)
                        elif hasattr(res, 'get_markdown'):
                            markdown_parts.append(res.get_markdown())
            
            # Combine all markdown parts
            return "\n\n".join(markdown_parts) if markdown_parts else ""
            
        except Exception as e:
            raise RuntimeError(f"PaddleOCR conversion failed: {str(e)}")
    
    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError("paddleocr is not available")
        
        try:
            # Run prediction
            output = self._pipeline.predict(input=file_path)
            
            # Collect JSON from all results
            json_data = []
            import tempfile
            import json
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save JSON files to temp directory
                for res in output:
                    res.save_to_json(save_path=temp_dir)
                
                # Find all JSON files in the temp directory
                json_files = sorted(Path(temp_dir).glob("*.json"))
                
                if json_files:
                    # Read all JSON files
                    for json_file in json_files:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            json_data.append(json.load(f))
                else:
                    # Fallback: try to get JSON from result object
                    for res in output:
                        if hasattr(res, 'to_dict'):
                            json_data.append(res.to_dict())
                        elif hasattr(res, 'dict'):
                            json_data.append(res.dict())
                        elif hasattr(res, 'get_dict'):
                            json_data.append(res.get_dict())
            
            return {
                "content": json_data if len(json_data) > 1 else (json_data[0] if json_data else {}),
                "format": "json",
                "library": self.name
            }
            
        except Exception as e:
            raise RuntimeError(f"PaddleOCR JSON conversion failed: {str(e)}")
    
    async def convert_to_text(self, file_path: str) -> str:
        # Convert to markdown first, then extract plain text
        md_content = await self.convert_to_md(file_path)
        # Simple markdown to text conversion (remove markdown syntax)
        text = re.sub(r'#+\s+', '', md_content)  # Remove headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Remove bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Remove italic
        text = re.sub(r'```[\s\S]*?```', '', text)  # Remove code blocks
        text = re.sub(r'`(.*?)`', r'\1', text)  # Remove inline code
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # Remove links, keep text
        return text

