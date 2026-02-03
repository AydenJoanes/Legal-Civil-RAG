"""
Cross-Encoder Reranker Implementation

Uses a Cross-Encoder model to re-score retrieval candidates.
Cross-Encoders are more accurate than Bi-Encoders (embeddings) but slower,
so they are best used as a second stage (Reranking).
"""
from typing import List, Dict
from sentence_transformers import CrossEncoder
from app.core.logging import logger

class CrossEncoderReranker:
    """
    Reranks documents using a Cross-Encoder model.
    Singleton-ish usage recommended to avoid reloading model.
    """
    
    _model = None
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        if CrossEncoderReranker._model is None:
            logger.info(f"Loading Cross-Encoder model: {model_name}")
            CrossEncoderReranker._model = CrossEncoder(model_name)
        self.model = CrossEncoderReranker._model

    def rank(self, query: str, documents: List[Dict], top_k: int) -> List[Dict]:
        """
        Rerank a list of documents based on relevance to the query.
        
        Args:
            query: Search query
            documents: List of document dicts (must have 'content' or 'text' key)
            top_k: Number of top results to return
            
        Returns:
            Top k documents, re-ordered by relevance score
        """
        if not documents:
            return []
            
        # Prepare pairs for cross-encoder
        # We need to handle 'content' vs 'text' key discrepancy if any
        pairs = []
        for doc in documents:
            text = doc.get("content") or doc.get("text", "")
            pairs.append([query, text])
            
        # Predict scores
        scores = self.model.predict(pairs)
        
        # Attach scores to documents
        for i, doc in enumerate(documents):
            doc["score"] = float(scores[i])
            
        # Sort by score descending
        sorted_docs = sorted(documents, key=lambda x: x["score"], reverse=True)
        
        # Return top k
        return sorted_docs[:top_k]
