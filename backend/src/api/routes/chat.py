"""Chat API endpoints for RAG-powered Q&A."""

import json
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.dependencies import CurrentUser, OptionalUser
from src.db.connection import get_db
from src.models.chat import ChatMessage, ChatSession
from src.models.schemas import (
    ChatMessageResponse,
    ChatQuery,
    ChatResponse,
    ChatSessionDetail,
    ChatSessionSummary,
    ChatSource,
    ErrorResponse,
    MessageFeedback,
)
from src.services.rag import generate_rag_response, stream_rag_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def get_or_create_session(
    db: AsyncSession,
    session_id: Optional[UUID],
    user_id: Optional[str],
    initial_context: Optional[dict] = None,
) -> ChatSession:
    """Get an existing session or create a new one.

    Args:
        db: Database session.
        session_id: Optional existing session ID.
        user_id: Optional user ID.
        initial_context: Optional context for new sessions.

    Returns:
        ChatSession instance.
    """
    if session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            return session

    # Create new session
    session = ChatSession(
        user_id=UUID(user_id) if user_id else None,
        initial_context=initial_context,
        is_active=True,
        message_count=0,
    )
    db.add(session)
    await db.flush()
    return session


async def save_messages(
    db: AsyncSession,
    session: ChatSession,
    user_query: str,
    assistant_response: str,
    sources: list[dict],
    selection_context: Optional[dict] = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """Save user and assistant messages to the session.

    Args:
        db: Database session.
        session: Chat session.
        user_query: User's question.
        assistant_response: AI response.
        sources: RAG sources.
        selection_context: Optional selection context.
        input_tokens: Input token count.
        output_tokens: Output token count.
    """
    # User message
    user_msg = ChatMessage(
        session_id=session.id,
        sequence_number=session.message_count + 1,
        role="user",
        content=user_query,
        selection_context=selection_context,
    )
    db.add(user_msg)

    # Assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        sequence_number=session.message_count + 2,
        role="assistant",
        content=assistant_response,
        retrieved_chunks=sources,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(assistant_msg)

    # Update session
    session.message_count += 2

    # Generate title from first query if not set
    if not session.title and user_query:
        session.title = user_query[:100] + "..." if len(user_query) > 100 else user_query

    await db.flush()


@router.post(
    "/query",
    response_model=ChatResponse,
    summary="Query the RAG chatbot",
    description="Send a question and receive a complete response with sources.",
    responses={
        503: {"model": ErrorResponse, "description": "AI service unavailable"},
    },
)
async def query_chat(
    query: ChatQuery,
    user: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChatResponse:
    """Query the chatbot with optional context.

    Args:
        query: The chat query with optional filters.
        user: Optional authenticated user.
        db: Database session.

    Returns:
        ChatResponse with answer, sources, and session ID.
    """
    try:
        # Get or create session
        session = await get_or_create_session(
            db=db,
            session_id=query.session_id,
            user_id=user.sub if user else None,
            initial_context={
                "chapter_id": query.chapter_id,
                "module_id": query.module_id,
            }
            if query.chapter_id or query.module_id
            else None,
        )

        # Build selection context if provided
        selection_context = None
        if query.selected_text:
            selection_context = {
                "selected_text": query.selected_text,
                "chapter_id": query.chapter_id,
            }

        # Generate RAG response
        rag_response = await generate_rag_response(
            query=query.query,
            module_id=query.module_id,
            chapter_id=query.chapter_id,
            selected_text=query.selected_text,
            chat_history=query.chat_history,
        )

        # Save messages
        await save_messages(
            db=db,
            session=session,
            user_query=query.query,
            assistant_response=rag_response.answer,
            sources=rag_response.sources,
            selection_context=selection_context,
            input_tokens=rag_response.input_tokens,
            output_tokens=rag_response.output_tokens,
        )

        # Convert sources to schema
        sources = [
            ChatSource(
                module_id=s.get("module_id", ""),
                chapter_id=s.get("chapter_id", ""),
                section=s.get("section", ""),
                score=s.get("score", 0.0),
            )
            for s in rag_response.sources
        ]

        return ChatResponse(
            answer=rag_response.answer,
            sources=sources,
            session_id=session.id,
        )

    except Exception as e:
        logger.error(f"Chat query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable",
        )


@router.post(
    "/query/stream",
    summary="Query chatbot with streaming response",
    description="Stream response as Server-Sent Events.",
)
async def query_chat_stream(
    query: ChatQuery,
    user: OptionalUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Stream a chatbot response using Server-Sent Events.

    Args:
        query: The chat query with optional filters.
        user: Optional authenticated user.
        db: Database session.

    Returns:
        StreamingResponse with SSE events.
    """

    async def generate():
        try:
            # Get or create session
            session = await get_or_create_session(
                db=db,
                session_id=query.session_id,
                user_id=user.sub if user else None,
            )

            full_response = ""
            sources = []

            async for event in stream_rag_response(
                query=query.query,
                module_id=query.module_id,
                chapter_id=query.chapter_id,
                selected_text=query.selected_text,
                chat_history=query.chat_history,
            ):
                event_type = event.get("type")
                event_data = event.get("data")

                if event_type == "sources":
                    sources = event_data or []
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"

                elif event_type == "chunk":
                    full_response += event_data or ""
                    yield f"data: {json.dumps({'type': 'chunk', 'data': event_data})}\n\n"

                elif event_type == "done":
                    # Save messages to database
                    selection_context = None
                    if query.selected_text:
                        selection_context = {
                            "selected_text": query.selected_text,
                            "chapter_id": query.chapter_id,
                        }

                    await save_messages(
                        db=db,
                        session=session,
                        user_query=query.query,
                        assistant_response=full_response,
                        sources=sources,
                        selection_context=selection_context,
                    )

                    yield f"data: {json.dumps({'type': 'done', 'data': {'session_id': str(session.id)}})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/sessions",
    response_model=list[ChatSessionSummary],
    summary="List user's chat sessions",
)
async def list_chat_sessions(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, le=100),
    include_inactive: bool = Query(default=False),
) -> list[ChatSessionSummary]:
    """List chat sessions for the authenticated user.

    Args:
        user: Authenticated user.
        db: Database session.
        limit: Maximum sessions to return.
        include_inactive: Include archived sessions.

    Returns:
        List of chat session summaries.
    """
    query = select(ChatSession).where(
        ChatSession.user_id == UUID(user.sub)
    )

    if not include_inactive:
        query = query.where(ChatSession.is_active == True)

    query = query.order_by(desc(ChatSession.updated_at)).limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [ChatSessionSummary.model_validate(s) for s in sessions]


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetail,
    summary="Get chat session with messages",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def get_chat_session(
    session_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=50, le=200),
    before_sequence: Optional[int] = Query(default=None),
) -> ChatSessionDetail:
    """Get a chat session with its messages.

    Args:
        session_id: Session ID.
        user: Authenticated user.
        db: Database session.
        limit: Maximum messages to return.
        before_sequence: Pagination cursor.

    Returns:
        Chat session with messages.
    """
    # Get session with messages
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == UUID(user.sub),
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Filter and limit messages
    messages = session.messages
    if before_sequence:
        messages = [m for m in messages if m.sequence_number < before_sequence]

    messages = sorted(messages, key=lambda m: m.sequence_number)[-limit:]

    # Convert messages to response schema
    message_responses = []
    for msg in messages:
        # Convert retrieved_chunks to ChatSource list if present
        retrieved_chunks = None
        if msg.retrieved_chunks:
            retrieved_chunks = [
                ChatSource(
                    module_id=chunk.get("module_id", ""),
                    chapter_id=chunk.get("chapter_id", ""),
                    section=chunk.get("section", ""),
                    score=chunk.get("score", 0.0),
                )
                for chunk in msg.retrieved_chunks
            ]

        message_responses.append(
            ChatMessageResponse(
                id=msg.id,
                sequence_number=msg.sequence_number,
                role=msg.role,
                content=msg.content,
                retrieved_chunks=retrieved_chunks,
                selection_context=msg.selection_context,
                feedback_rating=msg.feedback_rating,
                created_at=msg.created_at,
            )
        )

    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        initial_context=session.initial_context,
        messages=message_responses,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a chat session",
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
    },
)
async def archive_chat_session(
    session_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Archive (soft delete) a chat session.

    Args:
        session_id: Session ID.
        user: Authenticated user.
        db: Database session.
    """
    result = await db.execute(
        update(ChatSession)
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == UUID(user.sub),
        )
        .values(is_active=False)
        .returning(ChatSession.id)
    )

    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )


@router.post(
    "/messages/{message_id}/feedback",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Submit feedback for a message",
    responses={
        404: {"model": ErrorResponse, "description": "Message not found"},
    },
)
async def submit_message_feedback(
    message_id: UUID,
    feedback: MessageFeedback,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Submit feedback for a chat message.

    Args:
        message_id: Message ID.
        feedback: Feedback data.
        user: Authenticated user.
        db: Database session.
    """
    # Verify message belongs to user's session
    result = await db.execute(
        select(ChatMessage)
        .join(ChatSession)
        .where(
            ChatMessage.id == message_id,
            ChatSession.user_id == UUID(user.sub),
        )
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )

    # Update feedback
    message.feedback_rating = feedback.rating
    message.feedback_text = feedback.feedback_text
    await db.flush()
