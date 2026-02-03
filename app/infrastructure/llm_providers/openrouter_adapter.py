"""
OpenRouter LLM Adapter - Adapter Pattern Implementation

Design Pattern: Adapter Pattern
- Adapts OpenRouter API to our ILLMProvider interface
- Allows easy swapping of LLM providers without changing client code

SOLID Principles:
- SRP: Only handles OpenRouter API communication
- OCP: New providers can be added without modifying this class
- LSP: Can replace any ILLMProvider implementation
- ISP: Implements focused interface methods
- DIP: Depends on ILLMProvider abstraction

Exception Handling:
- Timeout → LLMConnectionError
- Rate limit (429) → LLMRateLimitError  
- Auth error (401/403) → LLMAuthenticationError
- Empty response → LLMResponseError
"""
import os
import threading
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

from app.domain.interfaces import ILLMProvider
from app.core.logging import logger
from app.core.exceptions import (
    LLMConnectionError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMResponseError,
)

load_dotenv()


class OpenRouterAdapter(ILLMProvider):
    """
    Adapter for OpenRouter API.
    
    Implements Singleton pattern for resource efficiency.
    Adapts OpenRouter's API to our ILLMProvider interface.
    """
    
    _instance: Optional["OpenRouterAdapter"] = None
    _lock: threading.Lock = threading.Lock()
    
    # Default system prompt for RAG
    DEFAULT_SYSTEM_PROMPT = (
        "You are a document-grounded assistant.\n\n"
        "Rules you MUST follow:\n"
        "- Use ONLY the information present in the provided context.\n"
        "- Do NOT use any external knowledge.\n"
        "- Do NOT make assumptions or guesses.\n"
        "- If the answer is not present in the context, say:\n"
        "  \"The document does not contain this information.\"\n"
        "- Be concise and clear.\n"
        "- Summarize information instead of copying raw text.\n"
        "- Do NOT include IDs, reference numbers, GSTIN, CIN, signatures, "
        "or contact details unless explicitly asked.\n"
    )
    
    def __new__(cls, *args, **kwargs) -> "OpenRouterAdapter":
        """Singleton pattern with double-check locking"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    cls._instance = instance
        return cls._instance
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "meta-llama/llama-3.3-70b-instruct:free",
        base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    ):
        """
        Initialize OpenRouter adapter.
        
        Args:
            api_key: OpenRouter API key (defaults to env var)
            model: Model identifier
            base_url: API endpoint URL
        """
        # Prevent re-initialization in Singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        self._api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self._model = model
        self._base_url = base_url
        self._initialized = True
        
        logger.info(f"OpenRouterAdapter initialized with model: {model}")
    
    @property
    def model_name(self) -> str:
        """Return the model identifier"""
        return self._model
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text completion using OpenRouter.
        
        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, temperature, max_tokens)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Multi-turn chat completion using OpenRouter.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response
            
        Raises:
            LLMAuthenticationError: If API key is invalid
            LLMRateLimitError: If rate limit exceeded
            LLMConnectionError: If API is unreachable or timeout
            LLMResponseError: If response is empty or malformed
        """
        # Edge case: No API key
        if not self._api_key:
            logger.error("OpenRouter API key not configured")
            raise LLMAuthenticationError()
        
        logger.debug(f"Calling OpenRouter with {len(messages)} messages...")
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            response = requests.post(
                self._base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            # Handle specific HTTP errors
            if response.status_code == 401 or response.status_code == 403:
                logger.error(f"OpenRouter authentication failed: {response.status_code}")
                raise LLMAuthenticationError()
            
            if response.status_code == 429:
                logger.warning("OpenRouter rate limit exceeded")
                raise LLMRateLimitError()
            
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            # Edge case: Empty or malformed response
            if not data.get("choices"):
                logger.error(f"OpenRouter returned empty choices: {data}")
                raise LLMResponseError("No choices in response")
            
            answer = data["choices"][0].get("message", {}).get("content", "")
            
            if not answer or not answer.strip():
                logger.error("OpenRouter returned empty content")
                raise LLMResponseError("Empty content in response")
            
            logger.info(f"OpenRouter response received ({len(answer)} chars)")
            return answer
            
        except (LLMAuthenticationError, LLMRateLimitError, LLMResponseError):
            # Re-raise our custom exceptions
            raise
        except requests.exceptions.Timeout:
            logger.error("OpenRouter request timed out")
            raise LLMConnectionError("Request timed out after 60 seconds")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"OpenRouter connection failed: {e}")
            raise LLMConnectionError(str(e))
        except requests.exceptions.HTTPError as e:
            logger.error(f"OpenRouter HTTP error: {e}")
            raise LLMConnectionError(str(e))
        except KeyError as e:
            logger.error(f"Malformed OpenRouter response: {e}")
            raise LLMResponseError(f"Missing key in response: {e}")
        except Exception as e:
            logger.error(f"Unexpected OpenRouter error: {e}")
            raise LLMConnectionError(str(e))
    
    def generate_with_context(
        self,
        context: str,
        question: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Convenience method for RAG: Generate answer given context and question.
        
        Args:
            context: Retrieved document context
            question: User question
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated answer
        """
        system = system_prompt or self.DEFAULT_SYSTEM_PROMPT
        
        prompt = (
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )
        
        return self.generate(prompt, system_prompt=system)


# Singleton accessor function
_llm_provider: Optional[OpenRouterAdapter] = None
_provider_lock = threading.Lock()


def get_llm_provider() -> OpenRouterAdapter:
    """
    Get the singleton LLM provider instance.
    
    Returns:
        OpenRouterAdapter singleton instance
    """
    global _llm_provider
    
    if _llm_provider is None:
        with _provider_lock:
            if _llm_provider is None:
                _llm_provider = OpenRouterAdapter()
    
    return _llm_provider
