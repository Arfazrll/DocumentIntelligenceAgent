"""
DocIntel AI — Qdrant Vector Store Client.

Manages vector collections, indexing, and hybrid search (dense + sparse BM25).
"""

import logging
from typing import Any, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings

logger = logging.getLogger(__name__)

class QdrantStore:
    """Manages interaction with Qdrant vector database."""

    def __init__(self):
        self._client: QdrantClient | None = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    @property
    def client(self) -> QdrantClient:
        """Lazy-initialize Qdrant client."""
        if self._client is None:
            self._client = QdrantClient(url=settings.QDRANT_URL)
        return self._client

    async def ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
        except (UnexpectedResponse, Exception):
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=1024,  # bge-m3 dimension
                        distance=models.Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "bm25": models.SparseVectorParams(
                        modifier=models.Modifier.IDF,
                    )
                },
            )
            logger.info(f"Collection '{self.collection_name}' created successfully.")

    def upsert_points(
        self,
        points: list[dict[str, Any]],
    ):
        """
        Upsert points to Qdrant.

        Each point dict should contain:
        - id: str (UUID)
        - dense_vector: list[float] (1024-dim)
        - sparse_vector: dict with 'indices' and 'values' (optional)
        - payload: dict with metadata
        """
        qdrant_points = []
        for point in points:
            vectors = {"dense": point["dense_vector"]}

            # Add sparse vector if available
            if "sparse_vector" in point and point["sparse_vector"]:
                vectors["bm25"] = models.SparseVector(
                    indices=point["sparse_vector"]["indices"],
                    values=point["sparse_vector"]["values"],
                )

            qdrant_points.append(
                models.PointStruct(
                    id=point["id"],
                    vector=vectors,
                    payload=point["payload"],
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=qdrant_points,
        )

    def hybrid_search(
        self,
        dense_vector: list[float],
        sparse_vector: Optional[dict] = None,
        filter_conditions: Optional[dict] = None,
        top_k: int = 20,
        fusion_alpha: float = 0.6,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search using dense + sparse vectors with RRF fusion.

        Args:
            dense_vector: Dense embedding vector (1024-dim).
            sparse_vector: Sparse BM25 vector (optional).
            filter_conditions: Qdrant filter conditions.
            top_k: Number of results to return.
            fusion_alpha: Weight for dense vs sparse (0-1, higher = more dense).

        Returns:
            List of results with payload and scores.
        """
        # Build filter
        qdrant_filter = None
        if filter_conditions:
            must_conditions = []
            if "document_ids" in filter_conditions:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchAny(any=filter_conditions["document_ids"]),
                    )
                )
            if must_conditions:
                qdrant_filter = models.Filter(must=must_conditions)

        # If sparse vector available, do hybrid search with prefetch + RRF
        if sparse_vector:
            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    models.Prefetch(
                        query=dense_vector,
                        using="dense",
                        limit=top_k,
                        filter=qdrant_filter,
                    ),
                    models.Prefetch(
                        query=models.SparseVector(
                            indices=sparse_vector["indices"],
                            values=sparse_vector["values"],
                        ),
                        using="bm25",
                        limit=top_k,
                        filter=qdrant_filter,
                    ),
                ],
                query=models.FusionQuery(fusion=models.Fusion.RRF),
                limit=top_k,
            )
        else:
            # Dense-only search
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=dense_vector,
                using="dense",
                limit=top_k,
                query_filter=qdrant_filter,
            )

        # Convert to dict format
        output = []
        for point in results.points:
            output.append({
                "id": str(point.id),
                "score": point.score,
                "payload": point.payload,
            })

        return output

    def delete_by_document(self, document_id: str):
        """Delete all points for a given document."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def get_collection_info(self) -> dict:
        """Get collection statistics."""
        info = self.client.get_collection(self.collection_name)
        return {
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "status": info.status.value,
        }

# Singleton instance
qdrant_store = QdrantStore()
