"""Qdrant vector database client and operations."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.api.config import get_settings

# Global client instance
_client: Optional[AsyncQdrantClient] = None


@dataclass
class ContentChunk:
    """Represents a chunk of textbook content for vector storage.

    Attributes:
        id: Unique chunk identifier.
        text: The chunk text content.
        module_id: Parent module identifier.
        chapter_id: Parent chapter identifier.
        section_title: Section heading.
        content_type: Type of content (explanation, code, exercise).
        position: Order within chapter.
        token_count: Number of tokens in the chunk.
        metadata: Additional metadata.
    """

    id: str
    text: str
    module_id: str
    chapter_id: str
    section_title: str
    content_type: str  # "explanation", "code", "exercise", "summary"
    position: int
    token_count: int
    metadata: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        """Convert to Qdrant payload format.

        Returns:
            Dictionary suitable for Qdrant point payload.
        """
        payload = {
            "text": self.text,
            "module_id": self.module_id,
            "chapter_id": self.chapter_id,
            "section_title": self.section_title,
            "content_type": self.content_type,
            "position": self.position,
            "token_count": self.token_count,
        }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload


@dataclass
class SearchResult:
    """Represents a search result from Qdrant.

    Attributes:
        chunk_id: The matched chunk ID.
        score: Similarity score (0-1).
        text: The chunk text.
        module_id: Module identifier.
        chapter_id: Chapter identifier.
        section_title: Section title.
    """

    chunk_id: str
    score: float
    text: str
    module_id: str
    chapter_id: str
    section_title: str


async def get_qdrant_client() -> AsyncQdrantClient:
    """Get or create the Qdrant async client.

    Returns:
        AsyncQdrantClient instance.
    """
    global _client

    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=True,  # 2-3x faster for cloud connections
            timeout=30,
        )

    return _client


async def close_qdrant_client() -> None:
    """Close the Qdrant client connection."""
    global _client

    if _client is not None:
        await _client.close()
        _client = None


async def ensure_collection_exists() -> None:
    """Ensure the textbook content collection exists with proper configuration."""
    settings = get_settings()
    client = await get_qdrant_client()

    collections = await client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if settings.qdrant_collection_name not in collection_names:
        await client.create_collection(
            collection_name=settings.qdrant_collection_name,
            vectors_config=VectorParams(
                size=768,  # text-embedding-004 dimensions
                distance=Distance.COSINE,
            ),
        )

        # Create payload indexes for filtering
        for field in ["module_id", "chapter_id", "content_type"]:
            await client.create_payload_index(
                collection_name=settings.qdrant_collection_name,
                field_name=field,
                field_schema="keyword",
            )


async def upsert_chunks(
    chunks: List[ContentChunk],
    embeddings: List[List[float]],
) -> None:
    """Insert or update content chunks with their embeddings.

    Args:
        chunks: List of content chunks to upsert.
        embeddings: Corresponding embedding vectors.
    """
    if len(chunks) != len(embeddings):
        raise ValueError("Number of chunks must match number of embeddings")

    settings = get_settings()
    client = await get_qdrant_client()

    points = [
        PointStruct(
            id=chunk.id,
            vector=embedding,
            payload=chunk.to_payload(),
        )
        for chunk, embedding in zip(chunks, embeddings)
    ]

    await client.upsert(
        collection_name=settings.qdrant_collection_name,
        points=points,
    )


async def search_similar(
    query_embedding: List[float],
    limit: int = 5,
    module_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    content_type: Optional[str] = None,
    score_threshold: float = 0.7,
) -> List[SearchResult]:
    """Search for similar content chunks.

    Args:
        query_embedding: The query vector.
        limit: Maximum number of results.
        module_id: Filter by module.
        chapter_id: Filter by chapter.
        content_type: Filter by content type.
        score_threshold: Minimum similarity score.

    Returns:
        List of search results ordered by similarity.
    """
    settings = get_settings()
    client = await get_qdrant_client()

    # Build filter conditions
    conditions = []
    if module_id:
        conditions.append(
            FieldCondition(key="module_id", match=MatchValue(value=module_id))
        )
    if chapter_id:
        conditions.append(
            FieldCondition(key="chapter_id", match=MatchValue(value=chapter_id))
        )
    if content_type:
        conditions.append(
            FieldCondition(key="content_type", match=MatchValue(value=content_type))
        )

    query_filter = Filter(must=conditions) if conditions else None

    results = await client.search(
        collection_name=settings.qdrant_collection_name,
        query_vector=query_embedding,
        query_filter=query_filter,
        limit=limit,
        score_threshold=score_threshold,
    )

    return [
        SearchResult(
            chunk_id=str(result.id),
            score=result.score,
            text=result.payload.get("text", ""),
            module_id=result.payload.get("module_id", ""),
            chapter_id=result.payload.get("chapter_id", ""),
            section_title=result.payload.get("section_title", ""),
        )
        for result in results
    ]


async def check_qdrant_connection() -> bool:
    """Check if Qdrant is reachable.

    Returns:
        True if connection successful, False otherwise.
    """
    try:
        client = await get_qdrant_client()
        await client.get_collections()
        return True
    except Exception:
        return False


async def delete_chunks(chunk_ids: List[str]) -> None:
    """Delete chunks by their IDs.

    Args:
        chunk_ids: List of chunk IDs to delete.
    """
    settings = get_settings()
    client = await get_qdrant_client()

    await client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=chunk_ids,
    )


async def get_collection_info() -> Dict[str, Any]:
    """Get information about the content collection.

    Returns:
        Dictionary with collection statistics.
    """
    settings = get_settings()
    client = await get_qdrant_client()

    info = await client.get_collection(settings.qdrant_collection_name)

    return {
        "name": settings.qdrant_collection_name,
        "vectors_count": info.vectors_count,
        "points_count": info.points_count,
        "status": info.status.name,
    }
