"""
DocIntel AI — Ollama Client.

Handles local LLM inference: embedding (bge-m3), verifier (qwen2.5:7b), fallback (llama3.2:3b).
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for Ollama local LLM API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        self.verifier_model = settings.OLLAMA_VERIFIER_MODEL
        self.fallback_model = settings.OLLAMA_FALLBACK_MODEL
        self._client: httpx.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

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
                base_url=self.base_url,
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding vector using bge-m3."""
        response = await self.client.post(
            "/api/embed",
            json={
                "model": self.embedding_model,
                "input": text,
            },
        )
        if response.status_code == 404:
            response = await self.client.post(
                "/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text,
                },
            )
        response.raise_for_status()
        data = response.json()
        if "embeddings" in data:
            return data["embeddings"][0]
        return data["embedding"]

    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        response = await self.client.post(
            "/api/embed",
            json={
                "model": self.embedding_model,
                "input": texts,
            },
        )
        if response.status_code == 404:
            embeddings = []
            for text in texts:
                resp = await self.client.post(
                    "/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text},
                )
                if resp.status_code == 404:
                    resp.raise_for_status()
                embeddings.append(resp.json()["embedding"])
            return embeddings
        response.raise_for_status()
        data = response.json()
        return data["embeddings"]

    async def get_available_chat_model(self) -> str:
        """Find the first non-embedding model available in Ollama."""
        try:
            resp = await self.client.get("/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                for m in models:
                    name = m.get("name", "")
                    if "bge" not in name and "embed" not in name:
                        return name
                if models:
                    return models[0].get("name", "")
        except Exception:
            pass
        return settings.OLLAMA_FALLBACK_MODEL

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        format_json: bool = False,
    ) -> str:
        """Send chat completion request to Ollama with auto-fallback for missing models."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }
        if format_json:
            payload["format"] = "json"

        response = await self.client.post("/api/chat", json=payload)
        
        # Auto-heal 404 Not Found: dynamically pick available chat model from Ollama /api/tags
        if response.status_code == 404:
            available = await self.get_available_chat_model()
            if available:
                logger.info(f"Model '{model}' 404 in Ollama. Auto-switching to '{available}'")
                payload["model"] = available
                response = await self.client.post("/api/chat", json=payload)

        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    async def verify(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
    ) -> str:
        """Run verification using verifier model."""
        return await self.chat(
            model=self.verifier_model,
            messages=messages,
            temperature=temperature,
            format_json=True,
        )

    async def fallback_chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
    ) -> str:
        """Fallback inference using smaller local model."""
        return await self.chat(
            model=self.fallback_model,
            messages=messages,
            temperature=temperature,
        )

    async def health_check(self) -> bool:
        """Check if Ollama is running and models are available."""
        try:
            response = await self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

# Singleton instance
ollama_client = OllamaClient()
