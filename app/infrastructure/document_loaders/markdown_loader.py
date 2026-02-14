"""
Markdown Loader - Implements IDocumentLoader Interface

This loader reads raw Markdown (.md) files directly.
Unlike MarkdownPDFLoader (which converts PDFs to Markdown),
this loader handles files that are ALREADY in Markdown format.

Design Pattern: Factory Method (Product)
SOLID Principle:
    - Single Responsibility (only handles .md file loading)
    - Liskov Substitution (can be used anywhere IDocumentLoader is expected)
"""
from typing import List, Dict, Optional

from app.domain.interfaces.document_loader import IDocumentLoader
from app.core.logging import logger
from app.core.exceptions import EmptyDocumentError


class MarkdownLoader(IDocumentLoader):
    """
    Loader for raw Markdown (.md) files.
    
    Since Markdown files don't have pages, the entire file content 
    is treated as a single "page" (page 1). If the file is very large,
    we split it by top-level headings (# or ##) to create logical sections.
    """
    
    # Max characters before we split by headings
    SPLIT_THRESHOLD = 5000
    
    def load(self, file_bytes: bytes, filename: str = "document.md") -> List[Dict]:
        """
        Load a Markdown file and return its content as pages.
        
        For shorter files: returns as a single page.
        For larger files: splits by markdown headings into logical sections.
        """
        logger.debug(f"Loading Markdown file: {filename}")
        
        if not file_bytes or len(file_bytes) == 0:
            raise EmptyDocumentError(filename)
        
        # Decode bytes to string
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to latin-1 which never fails
            text = file_bytes.decode("latin-1")
        
        text = text.strip()
        
        if not text:
            raise EmptyDocumentError(filename)
        
        # For smaller files, return as single page
        if len(text) <= self.SPLIT_THRESHOLD:
            logger.info(f"Loaded Markdown file as single page: {filename} ({len(text)} chars)")
            return [{"page": 1, "text": text}]
        
        # For larger files, split by top-level headings for better chunking
        pages = self._split_by_headings(text)
        
        if not pages:
            # Fallback: return as single page
            return [{"page": 1, "text": text}]
        
        logger.info(f"Split Markdown file into {len(pages)} sections: {filename}")
        return pages
    
    def _split_by_headings(self, text: str) -> List[Dict]:
        """
        Split markdown text by top-level headings (# or ##) into logical sections.
        Each section becomes a 'page' for the ingestion pipeline.
        """
        import re
        
        # Split on lines that start with # or ##
        sections = re.split(r'(?=^#{1,2}\s)', text, flags=re.MULTILINE)
        
        pages = []
        page_num = 1
        
        for section in sections:
            section = section.strip()
            if section:
                pages.append({
                    "page": page_num,
                    "text": section
                })
                page_num += 1
        
        return pages
    
    @property
    def supported_extensions(self) -> List[str]:
        return [".md"]
