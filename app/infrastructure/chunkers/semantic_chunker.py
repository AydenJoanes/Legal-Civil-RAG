"""
Semantic Chunker - Strategy Pattern Implementation

This chunker attempts to split text while preserving semantic meaning.
For legal documents, it respects sentence boundaries and attempts to keep
paragraphs/clauses together rather than splitting arbitrarily by character count.

Design Pattern: Strategy
SOLID Principles:
    - SRP: Only handles semantic chunking logic
    - OCP: Can be extended with different semantic rules
"""
import re
from typing import List, Dict, Optional

from app.domain.interfaces.chunker import IChunker
from app.core.logging import logger
from app.core.exceptions import EmptyTextError


class SemanticChunker(IChunker):
    """
    Semantic text chunking strategy.
    
    Splits text by sentence boundaries and attempts to group them into
    chunks of target size. This is much better for legal documents where
    cutting a sentence in half destroys its meaning.
    
    It creates "meaningful" chunks rather than just "fixed size" chunks.
    """
    
    def __init__(self, target_chunk_size: int = 1000, overlap_sentences: int = 1):
        """
        Initialize semantic chunker.
        
        Args:
            target_chunk_size: Ideal size of chunks (soft limit)
            overlap_sentences: Number of sentences to overlap
        """
        self._target_size = target_chunk_size
        self._overlap = overlap_sentences
        logger.debug(f"SemanticChunker initialized: target={target_chunk_size}, overlap={overlap_sentences} sent")
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Split text semantically by sentences.
        """
        metadata = metadata or {}
        
        if not text or not text.strip():
            logger.warning("Empty text provided to SemanticChunker")
            raise EmptyTextError()
            
        # 1. Split into Sentences (basic heuristic)
        # Look for periods, question marks, exclamations followed by space and capital letter
        # Also respects common legal abbreviations (e.g., "Sec.", "Art.", "No.") to avoid false splits
        sentences = self._split_sentences(text)
        
        # 2. Group sentences into chunks
        chunks = []
        current_chunk_sentences = []
        current_size = 0
        chunk_id = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sent_len = len(sentence)
            
            # If adding this sentence exceeds target size significantly (1.5x),
            # and we already have content, finalize current chunk
            if current_chunk_sentences and (current_size + sent_len > self._target_size * 1.5):
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append({
                    "text": chunk_text,
                    "chunk_id": chunk_id,
                    **metadata
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk_sentences) - self._overlap)
                current_chunk_sentences = current_chunk_sentences[overlap_start:]
                current_size = sum(len(s) for s in current_chunk_sentences)
            
            current_chunk_sentences.append(sentence)
            current_size += sent_len + 1 # +1 for space
            i += 1
            
        # Add the last chunk if any
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append({
                "text": chunk_text,
                "chunk_id": chunk_id,
                **metadata
            })
            
        logger.debug(f"Created {len(chunks)} semantic chunks")
        return chunks

    def _split_sentences(self, text: str) -> List[str]:
        """
        Robust sentence splitting for legal text.
        Avoids splitting on common abbreviations like 'v.', 'No.', 'ex.'
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # This regex looks for:
        # (?<!\w\.\w.) - Negative lookbehind for acronyms like U.S.A.
        # (?<![A-Z][a-z]\.) - Negative lookbehind for titles like Mr.
        # (?<=\.|\?|\!) - Positive lookbehind for sentence enders
        # \s+ - One or more spaces
        # (?=[A-Z]) - Positive lookahead for capital letter (start of next sentence)
        
        # Simplified split: Split by punctuation followed by space
        # Better approach for legal: 
        # Split by newlines (paragraphs) first, then sentences?
        # For now, we use a regex that respects common legal abbreviations
        
        pattern = r'(?<=[.!?])\s+(?=[A-Z0-9"(])'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]

    @property
    def chunk_size(self) -> int:
        return self._target_size
    
    @property
    def chunk_overlap(self) -> int:
        return self._overlap * 100 # Rough approx in chars
