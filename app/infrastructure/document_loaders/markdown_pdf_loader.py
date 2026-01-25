"""
Markdown PDF Loader - Implements IDocumentLoader Interface

This loader uses pymupdf4llm to extract text from PDF files while PRESERVING STRUCTURE.
Standard loaders lose table structure and headers. This loader converts them to
Markdown, which LLMs understand perfectly.

Design Pattern: Factory Method (Product)
SOLID Principle:
    - Single Responsibility (only handles PDF -> Markdown loading)
    - Liskov Substitution (can replace PDFLoader)

Dependencies: pymupdf4llm, pymupdf
"""
import tempfile
import os
from typing import List, Dict
import pymupdf4llm

from app.domain.interfaces.document_loader import IDocumentLoader
from app.core.logging import logger
from app.core.exceptions import EmptyDocumentError, CorruptedDocumentError


class MarkdownPDFLoader(IDocumentLoader):
    """
    Advanced PDF loader that converts content to Markdown.
    
    BEST FOR:
    - Tables (converted to Markdown tables)
    - Headers & Structure (converted to # Header)
    - Lists (converted to - Item)
    
    This structural preservation allows the LLM to understand the *hierarchy*
    and *tabular data* in construction contracts.
    """
    
    def load(self, file_bytes: bytes, filename: str = "document.pdf") -> List[Dict]:
        """
        Load PDF and convert to Markdown pages.
        """
        logger.debug(f"Loading PDF as Markdown: {filename}")
        
        # Edge case: Empty file
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyDocumentError(filename)
            
        # pymupdf4llm requires a file path, so we write to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        try:
            # Convert PDF to Markdown
            # This returns a list where each item corresponds to a page if split properly,
            # but pymupdf4llm by default returns one big string or handles pages differently
            # depending on version. We'll use the robust method.
            
            # Get full markdown text with page chunks
            md_data = pymupdf4llm.to_markdown(tmp_path, page_chunks=True)
            
            pages = []
            for entry in md_data:
                # entry is a dict with 'metadata' and 'text' typically
                page_num = entry.get("metadata", {}).get("page", 0) + 1
                text = entry.get("text", "")
                
                if text.strip():
                    pages.append({
                        "page": page_num,
                        "text": text.strip()
                    })
            
            if not pages:
                logger.warning(f"No text found in {filename} via Markdown extraction. Attempting OCR Fallback...")
                from app.infrastructure.document_loaders.ocr_loader import OCRLoader
                return OCRLoader().load(file_bytes, filename)
                
            logger.info(f"Converted {len(pages)} pages to Markdown for: {filename}")
            return pages
            
        except Exception as e:
            logger.error(f"Markdown extraction failed: {e}. Attempting OCR Fallback...")
            try:
                from app.infrastructure.document_loaders.ocr_loader import OCRLoader
                return OCRLoader().load(file_bytes, filename)
            except Exception as ocr_error:
                raise CorruptedDocumentError(filename, f"Markdown & OCR failed. Original: {e}, OCR: {ocr_error}")
            
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    @property
    def supported_extensions(self) -> List[str]:
        return [".pdf"]
