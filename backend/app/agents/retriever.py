"""
DocIntel AI — Retrieval Agent.

Hybrid retrieval (dense + sparse BM25) with reranking.
"""

import logging
from typing import Any

from app.config import settings
from app.llm.ollama_client import ollama_client
from app.storage.qdrant_store import qdrant_store

logger = logging.getLogger(__name__)

class RetrievalAgent:
    """Handles hybrid retrieval and reranking."""

    def __init__(self):
        self._reranker = None

    @property
    def reranker(self):
        """Lazy-initialize reranker model safely."""
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")
            except Exception as e:
                logger.warning(f"Reranker model unavailable ({e}). Using vector similarity scores.")
                self._reranker = False  # Mark as False so we don't attempt reloading every query
        return self._reranker if self._reranker is not False else None

    async def retrieve(
        self,
        query: str,
        document_ids: list[str] | None = None,
        top_k_initial: int | None = None,
        top_k_final: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant chunks using hybrid search + reranking.
        """
        top_k_initial = top_k_initial or settings.RETRIEVAL_TOP_K_INITIAL
        top_k_final = top_k_final or settings.RETRIEVAL_TOP_K_FINAL

        # Step 1: Generate query embedding via Ollama bge-m3
        query_embedding = await ollama_client.generate_embedding(query)

        # Step 2: Hybrid retrieval from Qdrant
        filter_conds = {}
        if document_ids:
            filter_conds["document_ids"] = document_ids

        candidates = qdrant_store.hybrid_search(
            dense_vector=query_embedding,
            filter_conditions=filter_conds if document_ids else None,
            top_k=top_k_initial,
        )

        if not candidates:
            return []

        # Step 3: Reranking
        reranked = self._rerank(query, candidates, top_k_final)

        # Step 4: Filter by min relevance score
        min_score = settings.RETRIEVAL_MIN_RELEVANCE
        filtered = [c for c in reranked if (c.get("rerank_score") or c.get("score") or 0.0) >= min_score]

        logger.info(
            f"Retrieved {len(filtered)} chunks (from {len(candidates)} candidates) "
            f"for query: {query[:80]}..."
        )

        return filtered

    def _rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int,
    ) -> list[dict]:
        """Rerank candidates using bge-reranker-v2-m3."""
        try:
            if not self.reranker:
                return sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]

            pairs = [
                [query, c["payload"].get("content", "")]
                for c in candidates
            ]

            scores = self.reranker.predict(pairs)
            if isinstance(scores, (float, int)):
                scores = [float(scores)]

            for i, score in enumerate(scores):
                candidates[i]["rerank_score"] = float(score)

            reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
            return reranked[:top_k]

        except Exception as e:
            logger.warning(f"Reranking failed: {e}. Using original scores.")
            return sorted(candidates, key=lambda x: x.get("score", 0.0), reverse=True)[:top_k]

# Singleton instance
retrieval_agent = RetrievalAgent()
