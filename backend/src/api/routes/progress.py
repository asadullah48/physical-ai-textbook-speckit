"""Progress tracking API endpoints."""

from datetime import datetime, timezone
from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentUser
from src.db.connection import get_db
from src.models.progress import ModuleProgress, UserProgress
from src.models.schemas import (
    ErrorResponse,
    ModuleProgressResponse,
    ProgressResponse,
    ProgressSummary,
    ProgressUpdate,
    ResumePosition,
)

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get(
    "",
    response_model=ProgressSummary,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_progress_summary(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgressSummary:
    """Get the user's overall progress summary.

    Args:
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        Aggregated progress summary.
    """
    user_id = UUID(current_user.sub)

    # Query aggregated progress data
    result = await db.execute(
        select(
            func.count(UserProgress.id).filter(
                UserProgress.content_type == "module",
                UserProgress.status != "not_started"
            ).label("modules_started"),
            func.count(UserProgress.id).filter(
                UserProgress.content_type == "module",
                UserProgress.status == "completed"
            ).label("modules_completed"),
            func.count(UserProgress.id).filter(
                UserProgress.content_type == "chapter",
                UserProgress.status == "completed"
            ).label("chapters_completed"),
            func.count(UserProgress.id).filter(
                UserProgress.content_type == "exercise",
                UserProgress.status == "completed"
            ).label("exercises_completed"),
            func.coalesce(func.sum(UserProgress.reading_time_seconds), 0).label("total_reading_time"),
        ).where(UserProgress.user_id == user_id)
    )
    stats = result.one()

    # Get last accessed content
    last_result = await db.execute(
        select(UserProgress.content_id, UserProgress.last_accessed_at)
        .where(UserProgress.user_id == user_id)
        .order_by(UserProgress.last_accessed_at.desc())
        .limit(1)
    )
    last_content = last_result.first()

    return ProgressSummary(
        user_id=user_id,
        modules_started=stats.modules_started or 0,
        modules_completed=stats.modules_completed or 0,
        chapters_completed=stats.chapters_completed or 0,
        exercises_completed=stats.exercises_completed or 0,
        total_reading_time_seconds=stats.total_reading_time or 0,
        last_content_id=last_content.content_id if last_content else None,
        last_accessed_at=last_content.last_accessed_at if last_content else None,
    )


@router.get(
    "/resume",
    response_model=ResumePosition,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No in-progress content found"},
    },
)
async def get_resume_position(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResumePosition:
    """Get the most recent in-progress content for "Continue Reading" feature.

    Args:
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        Resume position information.

    Raises:
        HTTPException: If no in-progress content found.
    """
    user_id = UUID(current_user.sub)

    # Find most recent in-progress content (chapter or exercise)
    result = await db.execute(
        select(UserProgress)
        .where(
            UserProgress.user_id == user_id,
            UserProgress.status == "in_progress",
            UserProgress.content_type.in_(["chapter", "exercise"]),
        )
        .order_by(UserProgress.last_accessed_at.desc())
        .limit(1)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No in-progress content found",
        )

    return ResumePosition(
        content_id=progress.content_id,
        content_type=progress.content_type,
        progress_percent=progress.progress_percent,
        scroll_position=progress.scroll_position,
    )


@router.get(
    "/modules",
    response_model=List[ModuleProgressResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_module_progress(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> List[ModuleProgressResponse]:
    """Get progress for all modules.

    Args:
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        List of module progress records.
    """
    user_id = UUID(current_user.sub)

    result = await db.execute(
        select(ModuleProgress)
        .where(ModuleProgress.user_id == user_id)
        .order_by(ModuleProgress.module_id)
    )
    modules = result.scalars().all()

    return [
        ModuleProgressResponse(
            module_id=m.module_id,
            total_chapters=m.total_chapters,
            completed_chapters=m.completed_chapters,
            total_exercises=m.total_exercises,
            completed_exercises=m.completed_exercises,
            overall_progress=m.overall_progress,
            first_accessed_at=m.first_accessed_at,
            completed_at=m.completed_at,
        )
        for m in modules
    ]


@router.get(
    "/{content_id:path}",
    response_model=ProgressResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "No progress found"},
    },
)
async def get_content_progress(
    content_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProgress:
    """Get progress for a specific content item.

    Args:
        content_id: Content identifier (e.g., "module-1/chapter-2").
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        Progress record for the content.

    Raises:
        HTTPException: If no progress found.
    """
    user_id = UUID(current_user.sub)

    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No progress found for content: {content_id}",
        )

    return progress


@router.patch(
    "/{content_id:path}",
    response_model=ProgressResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def update_content_progress(
    content_id: str,
    update_data: ProgressUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserProgress:
    """Update progress for a specific content item.

    Args:
        content_id: Content identifier (e.g., "module-1/chapter-2").
        update_data: Progress update data.
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        Updated progress record.
    """
    user_id = UUID(current_user.sub)
    now = datetime.now(timezone.utc)

    # Find or create progress record
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.content_id == content_id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # Create new progress record
        progress = UserProgress(
            user_id=user_id,
            content_id=content_id,
            content_type=update_data.content_type,
            status="in_progress",
            started_at=now,
        )
        db.add(progress)

    # Update progress fields
    progress.progress_percent = update_data.progress_percent
    progress.last_accessed_at = now

    if update_data.scroll_position is not None:
        progress.scroll_position = update_data.scroll_position

    if update_data.reading_time_delta > 0:
        progress.reading_time_seconds += update_data.reading_time_delta

    # Update exercise-specific fields
    if update_data.content_type == "exercise":
        if update_data.exercise_score is not None:
            progress.attempts += 1
            if progress.best_score is None or update_data.exercise_score > progress.best_score:
                progress.best_score = update_data.exercise_score
        if update_data.exercise_answer is not None:
            progress.last_answer = update_data.exercise_answer

    # Update status based on progress
    if progress.progress_percent >= 100:
        progress.status = "completed"
        progress.completed_at = now
    elif progress.progress_percent > 0:
        progress.status = "in_progress"
        if progress.started_at is None:
            progress.started_at = now

    await db.flush()
    await db.refresh(progress)

    return progress
