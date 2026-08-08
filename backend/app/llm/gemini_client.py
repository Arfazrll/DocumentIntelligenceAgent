"""
DocIntel AI — Gemini Client.

Handles Google Gemini 2.0 Flash API calls (extraction & enrichment).
"""

import asyncio
import logging
import time
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self):
        self.model = settings.GEMINI_MODEL
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self.max_retries = 3
        self.base_delay = 2.0

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize httpx client matching current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        if self._client is None or getattr(self, "_loop", None) != current_loop or self._client.is_closed:
            self._loop = current_loop
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
        response_mime_type: Optional[str] = None,
    ) -> str:
        """Generate content using Gemini API, with fallback to local Ollama."""
        from app.llm.ollama_client import ollama_client

        if getattr(settings, "USE_LOCAL_LLM", False) or not self.api_key or self.api_key.startswith("AIzaxxxxx"):
            logger.info("Using local Ollama LLM")
            msgs: list[dict[str, str]] = []
            if system_instruction:
                msgs.append({"role": "system", "content": system_instruction})
            msgs.append({"role": "user", "content": prompt})
            return await ollama_client.chat(
                model=settings.OLLAMA_FALLBACK_MODEL,
                messages=msgs,
                temperature=temperature,
                format_json=(response_mime_type == "application/json"),
            )

        url = f"{self.base_url}/models/{self.model}:generateContent"

        contents = [{"parts": [{"text": prompt}]}]

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_mime_type:
            generation_config["responseMimeType"] = response_mime_type

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    url,
                    headers={"X-goog-api-key": self.api_key},
                    params={"key": self.api_key},
                    json=payload,
                )

                if response.status_code == 429:
                    logger.warning("Gemini 429 rate limit hit. Delegating request to Groq client.")
                    from app.llm.groq_client import groq_client
                    msgs: list[dict[str, str]] = []
                    if system_instruction:
                        msgs.append({"role": "system", "content": system_instruction})
                    msgs.append({"role": "user", "content": prompt})
                    resp_fmt = {"type": "json_object"} if response_mime_type == "application/json" else None
                    return await groq_client.chat(
                        messages=msgs,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        response_format=resp_fmt,
                    )

                response.raise_for_status()
                data = response.json()

                # Extract text from response
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        text_val = parts[0].get("text", "")
                        return str(text_val) if text_val is not None else ""
                return ""

            except httpx.HTTPStatusError as e:
                if e.response.status_code != 429:
                    raise
                if attempt >= self.max_retries - 1:
                    raise

        return ""

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Generate JSON output from Gemini."""
        return await self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
        )

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            result = await self.generate("Say 'ok'", max_tokens=10)
            return bool(result)
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

# Singleton instance
gemini_client = GeminiClient()
