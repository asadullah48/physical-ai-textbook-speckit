"""Authentication API endpoints."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.config import Settings, get_settings
from src.api.dependencies import CurrentUser, require_auth
from src.db.connection import get_db
from src.models.refresh_token import RefreshToken
from src.models.schemas import (
    ErrorResponse,
    TokenPair,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
)
from src.models.user import User
from src.services.auth import (
    create_token_pair,
    get_refresh_token_expiry,
    hash_password,
    hash_token,
    verify_password,
    verify_refresh_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
    },
)
async def register_user(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Register a new user account.

    Args:
        user_data: User registration data.
        db: Database session.

    Returns:
        Created user information.

    Raises:
        HTTPException: If email is already registered.
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        display_name=user_data.display_name,
        role="student",
        is_active=True,
        is_verified=False,
    )

    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=TokenPair,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPair:
    """Login and obtain access and refresh tokens.

    Args:
        login_data: User login credentials.
        request: HTTP request for client info.
        db: Database session.
        settings: Application settings.

    Returns:
        Token pair with access and refresh tokens.

    Raises:
        HTTPException: If credentials are invalid.
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == login_data.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)

    # Create token pair
    token_pair = create_token_pair(user.id, settings)

    # Store refresh token hash
    refresh_token = RefreshToken(
        token_hash=hash_token(token_pair.refresh_token),
        user_id=user.id,
        device_info=request.headers.get("User-Agent", "Unknown")[:255],
        ip_address=request.client.host if request.client else None,
        expires_at=get_refresh_token_expiry(settings),
    )
    db.add(refresh_token)

    return token_pair


@router.post(
    "/refresh",
    response_model=TokenPair,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
    },
)
async def refresh_token(
    token_data: TokenRefresh,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenPair:
    """Refresh access token using a valid refresh token.

    Args:
        token_data: Refresh token.
        request: HTTP request for client info.
        db: Database session.
        settings: Application settings.

    Returns:
        New token pair.

    Raises:
        HTTPException: If refresh token is invalid or expired.
    """
    # Verify JWT refresh token
    token_payload = verify_refresh_token(token_data.refresh_token, settings)
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Check if token hash exists and is not revoked
    token_hash = hash_token(token_data.refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # Revoke old token
    stored_token.is_revoked = True
    stored_token.revoked_at = datetime.now(timezone.utc)

    # Get user
    user_id = UUID(token_payload.sub)

    # Create new token pair
    token_pair = create_token_pair(user_id, settings)

    # Store new refresh token
    new_refresh_token = RefreshToken(
        token_hash=hash_token(token_pair.refresh_token),
        user_id=user_id,
        device_info=request.headers.get("User-Agent", "Unknown")[:255],
        ip_address=request.client.host if request.client else None,
        expires_at=get_refresh_token_expiry(settings),
    )
    db.add(new_refresh_token)

    return token_pair


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def logout_user(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Logout and revoke all refresh tokens for the current user.

    Args:
        current_user: Authenticated user from token.
        db: Database session.
    """
    user_id = UUID(current_user.sub)

    # Revoke all active refresh tokens for this user
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,
        )
    )
    tokens = result.scalars().all()

    now = datetime.now(timezone.utc)
    for token in tokens:
        token.is_revoked = True
        token.revoked_at = now


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def get_current_user(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Get the current authenticated user's profile.

    Args:
        current_user: Authenticated user from token.
        db: Database session.

    Returns:
        User profile information.

    Raises:
        HTTPException: If user not found.
    """
    user_id = UUID(current_user.sub)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
