"""Chat models for conversation tracking and history."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from src.models.user import User


class ChatSession(Base, UUIDMixin, TimestampMixin):
    """Model for a chat conversation session.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Optional owner user ID (NULL for anonymous).
        title: Auto-generated session title from first message.
        initial_context: Context info (page_url, chapter_id, etc.).
        is_active: Whether the session is active.
        message_count: Number of messages in the session.
    """

    __tablename__ = "chat_sessions"

    user_id: Mapped[Optional[Any]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    initial_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    message_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="chat_sessions",
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.sequence_number",
    )

    __table_args__ = (
        Index("ix_chat_sessions_user_active", "user_id", "is_active"),
        Index("ix_chat_sessions_user_updated", "user_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, user_id={self.user_id}, messages={self.message_count})>"


class ChatMessage(Base, UUIDMixin):
    """Model for an individual chat message.

    Attributes:
        id: Unique identifier (UUID).
        session_id: Parent session ID.
        sequence_number: Order within the session.
        role: Message role (user, assistant, system).
        content: Message text content.
        retrieved_chunks: RAG context for assistant messages.
        selection_context: Context for selection-based Q&A.
        input_tokens: Token usage (input).
        output_tokens: Token usage (output).
        feedback_rating: User feedback rating (1-5).
        feedback_text: User feedback comment.
        created_at: Message timestamp.
    """

    __tablename__ = "chat_messages"

    session_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    retrieved_chunks: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    selection_context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    input_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    output_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    feedback_rating: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    feedback_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )

    __table_args__ = (
        Index("ix_chat_messages_session_seq", "session_id", "sequence_number"),
        Index("ix_chat_messages_session_created", "session_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"
