"""User progress model for tracking learning progress and exercise attempts."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from src.models.user import User


class UserProgress(Base, UUIDMixin):
    """Model for tracking user progress through educational content.

    Tracks progress for modules, chapters, and exercises with support for:
    - Reading progress (scroll position, reading time)
    - Exercise attempts (attempts count, best score, last answer)
    - Status tracking (not_started, in_progress, completed)

    Attributes:
        id: Unique identifier (UUID).
        user_id: Reference to the user.
        content_type: Type of content (module, chapter, exercise).
        content_id: Content path (e.g., "module-1/chapter-2").
        status: Progress status (not_started, in_progress, completed).
        progress_percent: Completion percentage (0-100).
        scroll_position: Last scroll position (0-1).
        reading_time_seconds: Cumulative reading time.
        attempts: Number of exercise attempts.
        best_score: Best exercise score (0-100).
        last_answer: Last submitted answer (for exercises).
        started_at: First access timestamp.
        completed_at: Completion timestamp.
        last_accessed_at: Last access timestamp.
    """

    __tablename__ = "user_progress"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    content_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="not_started",
    )
    progress_percent: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    scroll_position: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    reading_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    # Exercise-specific fields (T073)
    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    best_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )
    last_answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="progress_records",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "content_id", name="uq_user_content"),
        Index("ix_progress_user_type", "user_id", "content_type"),
        Index("ix_progress_user_recent", "user_id", "last_accessed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<UserProgress(id={self.id}, user_id={self.user_id}, "
            f"content_id={self.content_id}, status={self.status})>"
        )


class ModuleProgress(Base, UUIDMixin):
    """Aggregated progress per module.

    This model stores computed progress for each module, updated when
    underlying chapter/exercise progress changes.

    Attributes:
        id: Unique identifier (UUID).
        user_id: Reference to the user.
        module_id: Module identifier.
        total_chapters: Number of chapters in module.
        completed_chapters: Number of completed chapters.
        total_exercises: Number of exercises in module.
        completed_exercises: Number of completed exercises.
        overall_progress: Weighted average progress.
        first_accessed_at: First module access.
        last_accessed_at: Last activity timestamp.
        completed_at: Module completion timestamp.
    """

    __tablename__ = "module_progress"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    module_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    total_chapters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    completed_chapters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_exercises: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    completed_exercises: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    overall_progress: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    first_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="module_progress_records",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "module_id", name="uq_user_module"),
        Index("ix_module_progress_user", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModuleProgress(id={self.id}, user_id={self.user_id}, "
            f"module_id={self.module_id}, progress={self.overall_progress:.1f}%)>"
        )
