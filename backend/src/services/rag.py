"""RAG (Retrieval-Augmented Generation) pipeline for educational Q&A."""

import logging
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

from src.services.embeddings import generate_query_embedding
from src.services.gemini import get_gemini_service
from src.services.prompts import (
    NO_CONTEXT_RESPONSE,
    build_followup_prompt,
    build_rag_prompt,
)
from src.services.qdrant import SearchResult, search_similar

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from the RAG pipeline.

    Attributes:
        answer: The generated answer text.
        sources: List of source references used.
        input_tokens: Number of input tokens used.
        output_tokens: Number of output tokens generated.
    """

    answer: str
    sources: list[dict]
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class RAGSource:
    """A source reference for a RAG response.

    Attributes:
        module_id: The module identifier.
        chapter_id: The chapter identifier.
        section: The section title.
        score: The similarity score.
    """

    module_id: str
    chapter_id: str
    section: str
    score: float

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "module_id": self.module_id,
            "chapter_id": self.chapter_id,
            "section": self.section,
            "score": self.score,
        }


async def retrieve_context(
    query: str,
    module_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    limit: int = 5,
    score_threshold: float = 0.7,
) -> list[SearchResult]:
    """Retrieve relevant context chunks for a query.

    Args:
        query: The user's question.
        module_id: Optional module filter.
        chapter_id: Optional chapter filter.
        limit: Maximum number of chunks to retrieve.
        score_threshold: Minimum similarity score.

    Returns:
        List of matching content chunks.
    """
    try:
        # Generate query embedding
        query_embedding = generate_query_embedding(query)

        # Search for similar chunks
        results = await search_similar(
            query_embedding=query_embedding,
            limit=limit,
            module_id=module_id,
            chapter_id=chapter_id,
            score_threshold=score_threshold,
        )

        logger.info(f"Retrieved {len(results)} context chunks for query")
        return results

    except Exception as e:
        logger.error(f"Context retrieval failed: {e}")
        return []


def convert_results_to_chunks(results: list[SearchResult]) -> list[dict]:
    """Convert search results to context chunk dictionaries.

    Args:
        results: List of SearchResult objects.

    Returns:
        List of chunk dictionaries for prompt building.
    """
    return [
        {
            "text": result.text,
            "module_id": result.module_id,
            "chapter_id": result.chapter_id,
            "section_title": result.section_title,
        }
        for result in results
    ]


def extract_sources(results: list[SearchResult]) -> list[RAGSource]:
    """Extract source references from search results.

    Args:
        results: List of SearchResult objects.

    Returns:
        List of RAGSource objects.
    """
    return [
        RAGSource(
            module_id=result.module_id,
            chapter_id=result.chapter_id,
            section=result.section_title,
            score=result.score,
        )
        for result in results
    ]


async def generate_rag_response(
    query: str,
    module_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    selected_text: Optional[str] = None,
    chat_history: Optional[list[dict]] = None,
    context_limit: int = 5,
) -> RAGResponse:
    """Generate a complete RAG response.

    Args:
        query: The user's question.
        module_id: Optional module filter for retrieval.
        chapter_id: Optional chapter filter for retrieval.
        selected_text: Optional text the user selected.
        chat_history: Optional previous messages for follow-up questions.
        context_limit: Maximum number of context chunks.

    Returns:
        RAGResponse with answer, sources, and token usage.
    """
    # Retrieve context
    results = await retrieve_context(
        query=query,
        module_id=module_id,
        chapter_id=chapter_id,
        limit=context_limit,
    )

    sources = extract_sources(results)

    # Handle no context case
    if not results and not selected_text:
        return RAGResponse(
            answer=NO_CONTEXT_RESPONSE,
            sources=[s.to_dict() for s in sources],
            input_tokens=0,
            output_tokens=0,
        )

    # Build prompt
    context_chunks = convert_results_to_chunks(results)

    if chat_history:
        messages = build_followup_prompt(
            query=query,
            chat_history=chat_history,
            context_chunks=context_chunks if results else None,
        )
    else:
        messages = build_rag_prompt(
            query=query,
            context_chunks=context_chunks,
            selected_text=selected_text,
            chapter_id=chapter_id,
        )

    # Generate response
    gemini = get_gemini_service()
    answer, usage = await gemini.generate_response(messages)

    return RAGResponse(
        answer=answer,
        sources=[s.to_dict() for s in sources],
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
    )


async def stream_rag_response(
    query: str,
    module_id: Optional[str] = None,
    chapter_id: Optional[str] = None,
    selected_text: Optional[str] = None,
    chat_history: Optional[list[dict]] = None,
    context_limit: int = 5,
) -> AsyncGenerator[dict, None]:
    """Stream a RAG response with sources first.

    Args:
        query: The user's question.
        module_id: Optional module filter for retrieval.
        chapter_id: Optional chapter filter for retrieval.
        selected_text: Optional text the user selected.
        chat_history: Optional previous messages for follow-up questions.
        context_limit: Maximum number of context chunks.

    Yields:
        Event dictionaries with type and data:
        - {"type": "sources", "data": [...]}: Source references
        - {"type": "chunk", "data": "..."}: Response text chunk
        - {"type": "done", "data": null}: Stream complete
    """
    # Retrieve context
    results = await retrieve_context(
        query=query,
        module_id=module_id,
        chapter_id=chapter_id,
        limit=context_limit,
    )

    sources = extract_sources(results)

    # Yield sources first
    yield {
        "type": "sources",
        "data": [s.to_dict() for s in sources],
    }

    # Handle no context case
    if not results and not selected_text:
        yield {"type": "chunk", "data": NO_CONTEXT_RESPONSE}
        yield {"type": "done", "data": None}
        return

    # Build prompt
    context_chunks = convert_results_to_chunks(results)

    if chat_history:
        messages = build_followup_prompt(
            query=query,
            chat_history=chat_history,
            context_chunks=context_chunks if results else None,
        )
    else:
        messages = build_rag_prompt(
            query=query,
            context_chunks=context_chunks,
            selected_text=selected_text,
            chapter_id=chapter_id,
        )

    # Stream response
    gemini = get_gemini_service()
    async for chunk in gemini.stream_response(messages):
        yield {"type": "chunk", "data": chunk}

    yield {"type": "done", "data": None}
