"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# Error Schemas
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


# =============================================================================
# User Schemas
# =============================================================================


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password")
    display_name: Optional[str] = Field(
        default=None, max_length=100, description="Optional display name"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response."""

    id: UUID = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    display_name: Optional[str] = Field(default=None, description="Display name")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: Optional[str] = Field(default=None, max_length=100)


# =============================================================================
# Token Schemas
# =============================================================================


class TokenPair(BaseModel):
    """Schema for JWT token pair."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiry in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str = Field(..., description="Refresh token to exchange")


class TokenPayload(BaseModel):
    """Schema for decoded JWT payload."""

    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    type: str = Field(..., description="Token type (access/refresh)")


# =============================================================================
# Health Schemas
# =============================================================================


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Overall health status")
    database: bool = Field(..., description="Database connection status")
    vector_store: Optional[bool] = Field(
        default=None, description="Vector store connection status"
    )
    timestamp: datetime = Field(..., description="Health check timestamp")


# =============================================================================
# Chat Schemas
# =============================================================================


class ChatQuery(BaseModel):
    """Schema for chat query request."""

    query: str = Field(
        ..., min_length=1, max_length=2000, description="User's question"
    )
    selected_text: Optional[str] = Field(
        default=None, max_length=5000, description="Selected text for context"
    )
    module_id: Optional[str] = Field(
        default=None, description="Filter to specific module"
    )
    chapter_id: Optional[str] = Field(
        default=None, description="Filter to specific chapter"
    )
    session_id: Optional[UUID] = Field(
        default=None, description="Existing session ID"
    )
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Previous messages for context"
    )


class ChatSource(BaseModel):
    """Schema for RAG source citation."""

    module_id: str = Field(..., description="Source module ID")
    chapter_id: str = Field(..., description="Source chapter ID")
    section: str = Field(..., description="Section title")
    score: float = Field(..., description="Relevance score")


class ChatResponse(BaseModel):
    """Schema for chat response."""

    answer: str = Field(..., description="Generated answer")
    sources: List[ChatSource] = Field(..., description="Source citations")
    session_id: UUID = Field(..., description="Chat session ID")


class ChatSessionSummary(BaseModel):
    """Schema for chat session summary."""

    id: UUID = Field(..., description="Session ID")
    title: Optional[str] = Field(default=None, description="Session title")
    message_count: int = Field(..., description="Number of messages")
    is_active: bool = Field(..., description="Session active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    """Schema for chat message response."""

    id: UUID = Field(..., description="Message ID")
    sequence_number: int = Field(..., description="Message order in session")
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    retrieved_chunks: Optional[List[ChatSource]] = Field(
        default=None, description="RAG sources for assistant messages"
    )
    selection_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Selection context for selection-based Q&A"
    )
    feedback_rating: Optional[int] = Field(
        default=None, description="User feedback rating (1-5)"
    )
    created_at: datetime = Field(..., description="Message timestamp")

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    """Schema for detailed chat session with messages."""

    id: UUID = Field(..., description="Session ID")
    title: Optional[str] = Field(default=None, description="Session title")
    initial_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Initial context"
    )
    messages: List[ChatMessageResponse] = Field(..., description="Session messages")

    model_config = {"from_attributes": True}


class MessageFeedback(BaseModel):
    """Schema for message feedback."""

    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(
        default=None, max_length=1000, description="Optional feedback text"
    )


# =============================================================================
# Progress Schemas
# =============================================================================


class ProgressUpdate(BaseModel):
    """Schema for updating progress."""

    content_type: str = Field(
        ..., pattern="^(module|chapter|exercise)$", description="Content type"
    )
    progress_percent: float = Field(
        ..., ge=0, le=100, description="Progress percentage"
    )
    scroll_position: Optional[float] = Field(
        default=None, ge=0, le=1, description="Scroll position (0-1)"
    )
    reading_time_delta: int = Field(
        default=0, ge=0, description="Seconds to add to reading time"
    )
    # Exercise-specific fields (T074)
    exercise_score: Optional[float] = Field(
        default=None, ge=0, le=100, description="Score for exercise attempt"
    )
    exercise_answer: Optional[str] = Field(
        default=None, max_length=10000, description="Submitted answer for exercise"
    )


class ProgressResponse(BaseModel):
    """Schema for progress response."""

    id: UUID = Field(..., description="Progress record ID")
    content_id: str = Field(..., description="Content identifier")
    content_type: str = Field(..., description="Content type")
    status: str = Field(..., description="Progress status")
    progress_percent: float = Field(..., description="Progress percentage")
    scroll_position: Optional[float] = Field(
        default=None, description="Last scroll position"
    )
    reading_time_seconds: int = Field(..., description="Total reading time")
    # Exercise-specific fields (T074)
    attempts: int = Field(default=0, description="Number of exercise attempts")
    best_score: Optional[float] = Field(
        default=None, description="Best exercise score"
    )
    last_answer: Optional[str] = Field(
        default=None, description="Last submitted answer"
    )
    started_at: Optional[datetime] = Field(default=None, description="First access")
    completed_at: Optional[datetime] = Field(
        default=None, description="Completion timestamp"
    )

    model_config = {"from_attributes": True}


class ProgressSummary(BaseModel):
    """Schema for user progress summary."""

    user_id: UUID = Field(..., description="User ID")
    modules_started: int = Field(..., description="Modules started count")
    modules_completed: int = Field(..., description="Modules completed count")
    chapters_completed: int = Field(..., description="Chapters completed count")
    exercises_completed: int = Field(..., description="Exercises completed count")
    total_reading_time_seconds: int = Field(..., description="Total reading time")
    last_content_id: Optional[str] = Field(
        default=None, description="Last accessed content"
    )
    last_accessed_at: Optional[datetime] = Field(
        default=None, description="Last access timestamp"
    )


class ResumePosition(BaseModel):
    """Schema for resume position."""

    content_id: str = Field(..., description="Content to resume")
    content_type: str = Field(..., description="Content type")
    progress_percent: float = Field(..., description="Current progress")
    scroll_position: Optional[float] = Field(
        default=None, description="Scroll position"
    )


class ModuleProgressResponse(BaseModel):
    """Schema for module-level progress."""

    module_id: str = Field(..., description="Module identifier")
    total_chapters: int = Field(..., description="Total chapters in module")
    completed_chapters: int = Field(..., description="Completed chapters count")
    total_exercises: int = Field(..., description="Total exercises in module")
    completed_exercises: int = Field(..., description="Completed exercises count")
    overall_progress: float = Field(..., description="Overall progress percentage")
    first_accessed_at: Optional[datetime] = Field(
        default=None, description="First access timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Module completion timestamp"
    )
