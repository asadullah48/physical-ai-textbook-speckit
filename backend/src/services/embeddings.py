"""Gemini embeddings for retrieval, on the current ``google-genai`` SDK.

* ``generate_query_embedding`` embeds a reader's question (task type
  ``RETRIEVAL_QUERY``) - used by the RAG pipeline at request time.
* ``generate_document_embedding`` / ``EmbeddingsService`` embed textbook
  chunks (task type ``RETRIEVAL_DOCUMENT``) - used by the ingestion script.

Query and document vectors must come from the same model and dimension, so
both read ``EMBEDDING_MODEL`` / ``EMBEDDING_DIMENSION`` from settings.
"""

from functools import lru_cache
from typing import List, Optional

from google import genai
from google.genai import types

from src.api.config import get_settings


@lru_cache(maxsize=4)
def get_genai_client(api_key: Optional[str] = None) -> genai.Client:
    """One client per API key for the process (shared with the chat service)."""
    return genai.Client(api_key=api_key or get_settings().google_api_key)


def _embed(text: str, task_type: str, title: Optional[str] = None) -> List[float]:
    settings = get_settings()
    config = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=settings.embedding_dimension,
        title=title if task_type == "RETRIEVAL_DOCUMENT" else None,
    )
    result = get_genai_client().models.embed_content(
        model=settings.embedding_model, contents=text, config=config
    )
    return list(result.embeddings[0].values)


def generate_query_embedding(text: str) -> List[float]:
    """Embed a user question for similarity search."""
    return _embed(text, "RETRIEVAL_QUERY")


def generate_document_embedding(text: str, title: Optional[str] = None) -> List[float]:
    """Embed a textbook chunk for storage in the vector database."""
    return _embed(text, "RETRIEVAL_DOCUMENT", title)


class EmbeddingsService:
    """Batch helper used by the ingestion script."""

    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            get_genai_client(api_key)
        self.embedding_dimension = get_settings().embedding_dimension

    def embed(self, text: str) -> List[float]:
        return generate_document_embedding(text)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [generate_document_embedding(t) for t in texts]


def get_embeddings_service() -> EmbeddingsService:
    """Get a configured embeddings service."""
    return EmbeddingsService()
