"""
Chat Route - Thin Controller using Service Layer

Design Pattern: Facade (via ChatService)
- Route is now a thin controller that delegates to ChatService
- All RAG orchestration logic is in the service layer

SOLID Principles:
- SRP: Route only handles HTTP concerns
- DIP: Depends on ChatService abstraction
"""
from fastapi import APIRouter
from typing import Optional

from app.application import ChatService
from app.core.logging import logger

router = APIRouter()

# Service instance (Facade Pattern)
chat_service = ChatService()


@router.post("/")
def chat(
    message: str,
    tag: Optional[str] = None,
    top_k: int = 8
):
    """
    Process a chat message with RAG.
    
    The route is now a thin controller:
    - Receives request parameters
    - Delegates to ChatService (Facade)
    - Returns response
    """
    logger.info(f"Chat request: {message[:50]}...")
    
    # Delegate to service (Facade Pattern)
    result = chat_service.chat(
        message=message,
        tag=tag,
        top_k=top_k
    )
    
    return result
