"""
Document Loader Factory - Factory Method Pattern

This factory creates the appropriate document loader based on file extension.
Adding support for new document types (DOCX, TXT, etc.) requires only:
1. Creating a new loader class implementing IDocumentLoader
2. Registering it in this factory

NO changes needed to existing code - follows Open/Closed Principle.

Design Pattern: Factory Method
SOLID Principles:
    - Open/Closed (extend without modifying existing code)
    - Dependency Inversion (returns interface, not concrete class)
"""
from typing import Dict, Type, Optional

from app.domain.interfaces.document_loader import IDocumentLoader
from app.infrastructure.document_loaders.pdf_loader import PDFLoader
from app.infrastructure.document_loaders.markdown_pdf_loader import MarkdownPDFLoader
from app.infrastructure.document_loaders.markdown_loader import MarkdownLoader
from app.core.logging import logger


class DocumentLoaderFactory:
    """
    Factory for creating document loaders based on file extension.
    
    Usage:
        loader = DocumentLoaderFactory.get_loader("document.pdf")
        pages = loader.load(file_bytes)
    
    To add new document type:
        1. Create new loader class implementing IDocumentLoader
        2. Register: DocumentLoaderFactory.register(".docx", DocxLoader)
    """
    
    # Registry mapping extensions to loader classes
    _loaders: Dict[str, Type[IDocumentLoader]] = {}
    
    @classmethod
    def _initialize_default_loaders(cls) -> None:
        """Register default loaders if registry is empty"""
        if not cls._loaders:
            cls.register(".pdf", MarkdownPDFLoader)
            cls.register(".md", MarkdownLoader)
    
    @classmethod
    def register(cls, extension: str, loader_class: Type[IDocumentLoader]) -> None:
        """
        Register a new document loader for a file extension.
        
        Args:
            extension: File extension (e.g., ".pdf", ".docx")
            loader_class: Class implementing IDocumentLoader
        """
        ext = extension.lower()
        cls._loaders[ext] = loader_class
        logger.debug(f"Registered loader for {ext}: {loader_class.__name__}")
    
    @classmethod
    def get_loader(cls, filename: str) -> IDocumentLoader:
        """
        Get the appropriate loader for a file.
        
        Args:
            filename: Name of the file to load
            
        Returns:
            IDocumentLoader instance for the file type
            
        Raises:
            ValueError: If no loader exists for the file type
        """
        cls._initialize_default_loaders()
        
        # Extract extension
        ext = cls._get_extension(filename)
        
        loader_class = cls._loaders.get(ext)
        if loader_class is None:
            supported = list(cls._loaders.keys())
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported types: {supported}"
            )
        
        logger.debug(f"Using {loader_class.__name__} for {filename}")
        return loader_class()
    
    @classmethod
    def get_supported_extensions(cls) -> list:
        """Return list of all supported file extensions"""
        cls._initialize_default_loaders()
        return list(cls._loaders.keys())
    
    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if a file type is supported"""
        cls._initialize_default_loaders()
        ext = cls._get_extension(filename)
        return ext in cls._loaders
    
    @staticmethod
    def _get_extension(filename: str) -> str:
        """Extract lowercase extension from filename"""
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", 1)[-1].lower()
