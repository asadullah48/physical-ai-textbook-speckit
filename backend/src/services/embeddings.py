"""Embedding generation service using Google Gemini text-embedding-004."""

from typing import List

import google.generativeai as genai

from src.api.config import get_settings

# Track if API is configured
_api_configured = False


def configure_gemini_api() -> None:
    """Configure the Gemini API with the API key."""
    global _api_configured

    if not _api_configured:
        settings = get_settings()
        genai.configure(api_key=settings.google_api_key)
        _api_configured = True


def generate_embedding(
    text: str,
    task_type: str = "retrieval_document",
) -> List[float]:
    """Generate an embedding for a single text.

    Args:
        text: The text to embed.
        task_type: The type of task for the embedding.
            - "retrieval_document": For content chunks being indexed.
            - "retrieval_query": For user queries.
            - "semantic_similarity": For comparing texts.
            - "classification": For classification tasks.

    Returns:
        768-dimensional embedding vector.
    """
    configure_gemini_api()
    settings = get_settings()

    result = genai.embed_content(
        model=f"models/{settings.embedding_model}",
        content=text,
        task_type=task_type,
    )

    return result["embedding"]


def generate_embeddings_batch(
    texts: List[str],
    task_type: str = "retrieval_document",
    batch_size: int = 100,
) -> List[List[float]]:
    """Generate embeddings for multiple texts.

    Args:
        texts: List of texts to embed.
        task_type: The type of task for the embeddings.
        batch_size: Maximum batch size for API calls.

    Returns:
        List of 768-dimensional embedding vectors.
    """
    configure_gemini_api()
    settings = get_settings()

    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        # Gemini supports batch embedding
        result = genai.embed_content(
            model=f"models/{settings.embedding_model}",
            content=batch,
            task_type=task_type,
        )

        # Handle single vs batch response format
        if isinstance(result["embedding"][0], float):
            # Single item, wrap in list
            embeddings.append(result["embedding"])
        else:
            # Batch response
            embeddings.extend(result["embedding"])

    return embeddings


def generate_query_embedding(query: str) -> List[float]:
    """Generate an embedding optimized for search queries.

    Args:
        query: The search query text.

    Returns:
        768-dimensional embedding vector.
    """
    return generate_embedding(query, task_type="retrieval_query")


def generate_document_embedding(text: str) -> List[float]:
    """Generate an embedding optimized for document indexing.

    Args:
        text: The document text.

    Returns:
        768-dimensional embedding vector.
    """
    return generate_embedding(text, task_type="retrieval_document")
