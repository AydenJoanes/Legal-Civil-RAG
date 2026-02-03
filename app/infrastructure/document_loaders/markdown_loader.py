from typing import List, Dict, Optional
from app.domain.interfaces.document_loader import IDocumentLoader

class MarkdownLoader(IDocumentLoader):
    """
    Loader for Markdown files (.md).
    Treats the entire file content as a single page.
    """

    def load(self, file_bytes: bytes, filename: Optional[str] = None) -> List[Dict]:
        """
        Load Markdown file and return as a single page.
        
        Args:
            file_bytes: Raw bytes of the markdown file
            filename: Original filename
            
        Returns:
            List with one dict containing the full text
        """
        try:
            # Decode bytes to string
            text = file_bytes.decode('utf-8')
            return [{
                "page": 1,
                "text": text
            }]
        except UnicodeDecodeError:
            # Fallback for non-utf-8 encodings if needed, or let it raise
            # For now try latin-1 as fallback
            text = file_bytes.decode('latin-1')
            return [{
                "page": 1,
                "text": text
            }]

    @property
    def supported_extensions(self) -> List[str]:
        return ['.md']
