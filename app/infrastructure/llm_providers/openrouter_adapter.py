"""
Gemini LLM Adapter - Adapter Pattern Implementation

Uses Google Gemini's native REST API (generateContent endpoint).

Design Pattern: Adapter Pattern
- Adapts Gemini API to our ILLMProvider interface

SOLID Principles:
- SRP: Only handles Gemini API communication
- OCP: New providers can be added without modifying this class
- LSP: Can replace any ILLMProvider implementation
- DIP: Depends on ILLMProvider abstraction
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
    Adapter for Google Gemini API (native REST endpoint).
    Implements Singleton pattern for resource efficiency.
    """
    
    _instance: Optional["OpenRouterAdapter"] = None
    _lock: threading.Lock = threading.Lock()
    DEFAULT_MODEL = "gemini-2.5-flash"
    
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
        model: Optional[str] = None,
    ):
        # Prevent re-initialization in Singleton
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model = model or os.getenv("GEMINI_MODEL") or self.DEFAULT_MODEL
        self._base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        self._initialized = True
        
        logger.info(f"GeminiAdapter initialized with model: {self._model}")
    
    @property
    def model_name(self) -> str:
        return self._model
    
    def _convert_messages_to_gemini_format(
        self, messages: List[Dict[str, str]]
    ) -> tuple:
        """
        Convert OpenAI-style messages to Gemini's native format.
        
        Returns:
            (system_instruction, contents) tuple
        """
        system_text = None
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_text = content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
        
        return system_text, contents
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
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
        if not self._api_key:
            logger.error("Gemini API key not configured")
            raise LLMAuthenticationError()
        
        logger.debug(f"Calling Gemini with {len(messages)} messages...")
        
        # Convert messages to Gemini format
        system_text, contents = self._convert_messages_to_gemini_format(messages)
        
        # Build payload
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        # Add system instruction if present
        if system_text:
            payload["systemInstruction"] = {
                "parts": [{"text": system_text}]
            }
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        # API key goes as query parameter for Gemini
        url = f"{self._base_url}?key={self._api_key}"
        
        try:
            response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60
            )
            
            if response.status_code == 401 or response.status_code == 403:
                logger.error(f"Gemini authentication failed: {response.status_code}")
                raise LLMAuthenticationError()
            
            if response.status_code == 429:
                logger.warning("Gemini rate limit exceeded")
                raise LLMRateLimitError()
            
            response.raise_for_status()
            
            data = response.json()
            
            # Parse Gemini's native response format
            candidates = data.get("candidates", [])
            if not candidates:
                logger.error(f"Gemini returned no candidates: {data}")
                raise LLMResponseError("No candidates in response")
            
            # Extract text from first candidate
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                logger.error("Gemini returned empty parts")
                raise LLMResponseError("Empty parts in response")
            
            answer = parts[0].get("text", "")
            
            if not answer or not answer.strip():
                logger.error("Gemini returned empty content")
                raise LLMResponseError("Empty content in response")
            
            logger.info(f"Gemini response received ({len(answer)} chars)")
            return answer
            
        except (LLMAuthenticationError, LLMRateLimitError, LLMResponseError):
            raise
        except requests.exceptions.Timeout:
            logger.error("Gemini request timed out")
            raise LLMConnectionError("Request timed out after 60 seconds")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Gemini connection failed: {e}")
            raise LLMConnectionError(str(e))
        except requests.exceptions.HTTPError as e:
            logger.error(f"Gemini HTTP error: {e}")
            raise LLMConnectionError(str(e))
        except KeyError as e:
            logger.error(f"Malformed Gemini response: {e}")
            raise LLMResponseError(f"Missing key in response: {e}")
        except Exception as e:
            logger.error(f"Unexpected Gemini error: {e}")
            raise LLMConnectionError(str(e))
    
    def generate_with_context(
        self,
        context: str,
        question: str,
        system_prompt: Optional[str] = None
    ) -> str:
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
    global _llm_provider
    if _llm_provider is None:
        with _provider_lock:
            if _llm_provider is None:
                _llm_provider = OpenRouterAdapter()
    return _llm_provider
