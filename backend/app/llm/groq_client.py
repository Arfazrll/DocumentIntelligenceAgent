"""
DocIntel AI — Groq Client.

Handles Groq API calls for Llama 3.3 70B (reasoning/synthesizer).
Includes retry with exponential backoff for rate limiting.
"""

import asyncio
import logging
import time
from typing import Any, AsyncGenerator, Optional

from groq import AsyncGroq, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for Groq API (Llama 3.3 70B)."""

    def __init__(self):
        self.model = settings.GROQ_MODEL
        self._client: AsyncGroq | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.max_retries = 3
        self.base_delay = 2.0  # seconds

    @property
    def client(self) -> AsyncGroq:
        """Lazy-initialize Groq client matching current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is None or getattr(self, "_loop", None) != current_loop:
            self._loop = current_loop
            self._client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._client

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 4096,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send chat completion request with fallback to local Ollama."""
        from app.llm.ollama_client import ollama_client

        if getattr(settings, "USE_LOCAL_LLM", False):
            logger.info("USE_LOCAL_LLM=True: Using local Ollama LLM")
            return await ollama_client.chat(
                model=settings.OLLAMA_FALLBACK_MODEL,
                messages=messages,
                temperature=temperature,
                format_json=bool(response_format),
            )

        for attempt in range(self.max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response: Any = await self.client.chat.completions.create(**kwargs)
                return str(response.choices[0].message.content or "")

            except Exception as e:
                logger.warning(f"Groq API error/rate limit: {e}. Switching to local Ollama model ({settings.OLLAMA_FALLBACK_MODEL}).")
                return await ollama_client.chat(
                    model=settings.OLLAMA_FALLBACK_MODEL,
                    messages=messages,
                    temperature=temperature,
                    format_json=bool(response_format),
                )

        return ""

    async def chat_stream(
        self,
        messages: list[Any],
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion tokens."""
        for attempt in range(self.max_retries):
            try:
                stream: Any = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )
                async for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                return

            except RateLimitError as e:
                delay = self.base_delay * (2 ** attempt)
                logger.warning(
                    f"Groq rate limit hit during stream (attempt {attempt + 1}). "
                    f"Retrying in {delay}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    async def health_check(self) -> bool:
        """Check if Groq API is accessible."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False

# Singleton instance
groq_client = GroqClient()
