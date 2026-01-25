"""
Chat Service - Facade Pattern + Builder Pattern Implementation

Design Patterns:
- Facade: Provides a simplified interface to the RAG chat subsystem
- Builder: Uses RAGPromptBuilder for flexible prompt construction

Orchestrates: Tag Inference, Retrieval, Prompt Building, LLM Generation

SOLID Principles:
- SRP: Only handles chat/RAG workflow
- OCP: New prompt styles via different builders
- DIP: Depends on abstractions (ILLMProvider, RetrievalService, PromptBuilder)
"""
from typing import Dict, Any, Optional

from app.domain.interfaces import ILLMProvider
from app.domain.builders import RAGPromptBuilder, PromptBuilder, ConstructionLegalPromptBuilder
from app.infrastructure.llm_providers import get_llm_provider
from app.application.retrieval_service import RetrievalService
from app.services.tag_inference import infer_tag_from_text
from app.core.logging import logger


class ChatService:
    """
    Facade for RAG chat operations.
    
    Orchestrates the complete RAG pipeline:
    1. Infer tag from user message
    2. Retrieve relevant context
    3. Build prompt using Builder Pattern
    4. Generate answer using LLM
    """
    
    def __init__(
        self,
        llm_provider: Optional[ILLMProvider] = None,
        retrieval_service: Optional[RetrievalService] = None,
        prompt_builder: Optional[PromptBuilder] = None
    ):
        """
        Initialize with dependencies (Dependency Injection).
        
        Args:
            llm_provider: LLM service (defaults to Singleton OpenRouter)
            retrieval_service: Retrieval facade (defaults to new instance)
            prompt_builder: Prompt builder (defaults to RAGPromptBuilder)
        """
        self._llm_provider = llm_provider or get_llm_provider()
        self._retrieval_service = retrieval_service or RetrievalService()
        self._prompt_builder = prompt_builder or ConstructionLegalPromptBuilder()
        
        logger.debug("ChatService initialized with dependencies")
    
    def chat(
        self,
        message: str,
        tag: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Process a chat message with RAG.
        
        Facade method that orchestrates:
        1. Tag inference (if not provided)
        2. Context retrieval
        3. Prompt building (Builder Pattern)
        4. LLM answer generation
        
        Args:
            message: User's question/message
            tag: Optional explicit tag (otherwise inferred)
            top_k: Number of context chunks to retrieve
            
        Returns:
            Dict with message, tag, and answer
        """
        logger.info(f"Chat request: {message[:50]}...")
        
        # 1. Infer tag if not provided
        inferred_tag = tag or infer_tag_from_text(message)
        logger.debug(f"Using tag: {inferred_tag}")
        
        # 2. Handle wildcard in message
        if "*" in message:
            query_for_retrieval = "*"
        else:
            query_for_retrieval = message
        
        # 3. Retrieve context using RetrievalService
        context = self._retrieval_service.get_context(
            query=query_for_retrieval,
            tag=inferred_tag,
            top_k=top_k
        )
        logger.debug(f"Retrieved context: {len(context)} chars")
        
        # 4. Build prompt using Builder Pattern
        self._prompt_builder.reset()
        messages = (self._prompt_builder
            .add_context(context, "Retrieved Documents")
            .set_query(message)
            .build_messages())
        
        logger.debug(f"Built prompt with {len(messages)} messages")
        
        # 5. Generate answer using LLM (Adapter Pattern)
        answer = self._llm_provider.chat(messages)
        logger.success(f"Generated response for: {message[:30]}...")
        
        return {
            "message": message,
            "inferred_tag": inferred_tag,
            "answer": answer
        }
    
    def chat_with_builder(
        self,
        message: str,
        builder: PromptBuilder,
        tag: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Chat using a custom prompt builder.
        
        Allows injection of different prompt building strategies.
        
        Args:
            message: User's question
            builder: Custom PromptBuilder instance
            tag: Optional tag filter
            top_k: Number of context chunks
            
        Returns:
            Dict with message, tag, and answer
        """
        logger.info(f"Chat with custom builder: {message[:50]}...")
        
        # Infer tag
        inferred_tag = tag or infer_tag_from_text(message)
        
        # Retrieve context
        context = self._retrieval_service.get_context(
            query=message if "*" not in message else "*",
            tag=inferred_tag,
            top_k=top_k
        )
        
        # Build prompt with custom builder
        builder.reset()
        messages = (builder
            .add_context(context, "Context")
            .set_query(message)
            .build_messages())
        
        # Generate answer
        answer = self._llm_provider.chat(messages)
        
        return {
            "message": message,
            "inferred_tag": inferred_tag,
            "answer": answer
        }
    
    def chat_with_context(
        self,
        message: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Chat with explicitly provided context (no retrieval).
        
        Uses Builder Pattern for prompt construction.
        
        Args:
            message: User's question
            context: Pre-built context string
            
        Returns:
            Dict with message and answer
        """
        logger.info(f"Chat with custom context: {message[:50]}...")
        
        answer = self._llm_provider.generate_with_context(
            context=context,
            question=message
        )
        
        return {
            "message": message,
            "answer": answer
        }
