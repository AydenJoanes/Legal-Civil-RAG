"""
Retrieval Service - Facade Pattern Implementation

Design Pattern: Facade
- Provides a simplified interface to the retrieval subsystem
- Orchestrates: Embedder, Vector Store

SOLID Principles:
- SRP: Only handles document retrieval
- DIP: Depends on abstractions (IEmbedder, IVectorStore)
"""
import re
from typing import List, Dict, Any, Optional, Set

from app.domain.interfaces import IEmbedder, IVectorStore
from app.infrastructure.embedders import get_embedder
from app.infrastructure.persistence import PostgresVectorStore
from app.core.logging import logger


class RetrievalService:
    """
    Facade for document retrieval operations.
    
    Orchestrates:
    1. Query embedding generation
    2. Vector similarity search
    """
    
    def __init__(
        self,
        embedder: Optional[IEmbedder] = None,
        vector_store: Optional[IVectorStore] = None
    ):
        """
        Initialize with dependencies (Dependency Injection).
        
        Args:
            embedder: Embedding service (defaults to Singleton MiniLM)
            vector_store: Vector storage (defaults to PostgresVectorStore)
        """
        self._embedder = embedder or get_embedder()
        self._vector_store = vector_store or PostgresVectorStore()
        
        logger.debug("RetrievalService initialized with dependencies")
    
    def retrieve(
        self,
        query: str,
        tag: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant documents for a query.
        
        Facade method that handles:
        - Wildcard queries (return all with optional tag filter)
        - Semantic search (embed query + vector similarity)
        
        Args:
            query: Search query (use "*" for wildcard)
            tag: Optional tag filter
            top_k: Maximum results to return
            
        Returns:
            Dict with query and results
        """
        effective_tag = None if tag == "OTHERS" else tag
        logger.info(
            f"Retrieving for query: {query[:50]}..., tag: {tag}, "
            f"effective_tag: {effective_tag}"
        )
        
        # Handle wildcard query
        if query.strip() == "*":
            results = self._vector_store.search(
                query_embedding=None,
                tag=effective_tag,
                top_k=top_k
            )
            logger.info(f"Wildcard search returned {len(results)} results")
            
            return {
                "query": query,
                "tag": tag,
                "results": results,
                "result_count": len(results)
            }
        
        # Semantic search
        query_embedding = self._embedder.embed_text(query)
        candidate_k = max(top_k * 4, 12)
        
        results = self._vector_store.search(
            query_embedding=query_embedding,
            tag=effective_tag,
            top_k=candidate_k
        )
        logger.info(f"Semantic search returned {len(results)} raw results")

        reranked_results = self._rerank_results(query=query, results=results, top_k=top_k)
        logger.info(f"Reranked to top {len(reranked_results)} results")
        
        return {
            "query": query,
            "tag": tag,
            "results": reranked_results,
            "result_count": len(reranked_results)
        }

    def _tokenize(self, text: str) -> Set[str]:
        """Tokenize text into lowercase terms for lightweight lexical scoring."""
        return set(re.findall(r"[a-zA-Z0-9]{2,}", (text or "").lower()))

    def _rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """
        Hybrid reranking: semantic order + lexical overlap + source filename hints.

        This keeps vector search recall while improving precision for regulatory fee queries
        where exact keywords (fee, charge, section, project name, etc.) matter.
        """
        if not results:
            return []

        query_tokens = self._tokenize(query)
        query_lower = (query or "").lower()
        numeric_tokens = set(re.findall(r"\d+(?:\.\d+)?", query or ""))

        scored: List[Dict[str, Any]] = []
        total = max(len(results), 1)

        for idx, item in enumerate(results):
            content = item.get("content", "")
            source = (item.get("source") or "").lower()

            content_tokens = self._tokenize(content)
            overlap = query_tokens.intersection(content_tokens)
            lexical_score = (len(overlap) / max(len(query_tokens), 1)) * 2.5

            # Keep contribution from initial semantic ordering.
            semantic_order_score = ((total - idx) / total) * 1.2

            number_score = 0.0
            if numeric_tokens:
                matched_nums = sum(1 for n in numeric_tokens if n in content)
                number_score = (matched_nums / max(len(numeric_tokens), 1)) * 0.8

            source_bonus = 0.0
            if any(k in query_lower for k in ["fee", "fees", "charge", "charges"]):
                if "charges for services rendered" in source:
                    source_bonus += 1.0
                if "kreatfees" in source or "kreat_notification" in source:
                    source_bonus += 0.3
            if "project name" in query_lower and "change of project name" in source:
                source_bonus += 0.4
            if "section" in query_lower and "act" in query_lower:
                if "charges for services rendered" in source:
                    source_bonus += 0.3

            final_score = semantic_order_score + lexical_score + number_score + source_bonus

            scored.append(
                {
                    **item,
                    "_score": final_score,
                }
            )

        ranked = sorted(scored, key=lambda x: x["_score"], reverse=True)
        return [{k: v for k, v in r.items() if k != "_score"} for r in ranked[:top_k]]
    
    def get_context(
        self,
        query: str,
        tag: Optional[str] = None,
        top_k: int = 5
    ) -> str:
        """
        Get concatenated context for RAG.
        
        Convenience method for chat service.
        
        Args:
            query: Search query
            tag: Optional tag filter
            top_k: Maximum chunks to include
            
        Returns:
            Concatenated context string
        """
        result = self.retrieve(query, tag, top_k)
        
        if not result["results"]:
            return "No relevant context found."

        context_sections = []
        for idx, r in enumerate(result["results"], start=1):
            source = r.get("source") or "unknown"
            page = r.get("page")
            header = f"[Source {idx}] file={source}"
            if page is not None:
                header += f", page={page}"
            context_sections.append(f"{header}\n{r['content']}")

        return "\n\n".join(context_sections)
