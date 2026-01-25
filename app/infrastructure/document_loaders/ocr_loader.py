"""
OCR PDF Loader - Fallback Strategy

This loader uses Tesseract OCR (via pytesseract) to extract text from scanned images/PDFs.
It is used as a FALLBACK when standard extraction fails (empty text).

Dependencies: 
- tesseract-ocr (System)
- pytesseract (Python)
- pdf2image (Python)
"""
import tempfile
import os
from typing import List, Dict
import pytesseract
from pdf2image import convert_from_path

from app.domain.interfaces.document_loader import IDocumentLoader
from app.core.logging import logger
from app.core.exceptions import CorruptedDocumentError, EmptyDocumentError

class OCRLoader(IDocumentLoader):
    """
    Loader for Scanned PDFs using OCR.
    """
    
    def load(self, file_bytes: bytes, filename: str = "document.pdf") -> List[Dict]:
        logger.info(f"Attempting OCR extraction for: {filename}")
        
        if not file_bytes:
            raise EmptyDocumentError(filename)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name

        try:
            # 1. Convert PDF pages to Images
            # dpi=300 is standard for good OCR results
            images = convert_from_path(tmp_path, dpi=300)
            
            pages = []
            for i, image in enumerate(images):
                # 2. Run Tesseract OCR on each image
                text = pytesseract.image_to_string(image)
                
                if text.strip():
                    pages.append({
                        "page": i + 1,
                        "text": text.strip()
                    })
            
            if not pages:
                raise EmptyDocumentError(f"{filename} (OCR found no text)")
                
            logger.success(f"OCR extracted info from {len(pages)} pages for {filename}")
            return pages

        except Exception as e:
            logger.error(f"OCR Failed for {filename}: {e}")
            raise CorruptedDocumentError(filename, str(e))
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]
