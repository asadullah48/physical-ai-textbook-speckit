"""FastAPI dependencies for authentication and common operations."""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.config import Settings, get_settings
from src.models.schemas import TokenPayload

# HTTP Bearer scheme for JWT authentication
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_token(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Optional[TokenPayload]:
    """Extract and validate the JWT token from the Authorization header.

    Args:
        credentials: HTTP Bearer credentials from the request.
        settings: Application settings.

    Returns:
        Decoded token payload if valid, None if no token provided.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    if credentials is None:
        return None

    from src.services.auth import verify_access_token

    token_data = verify_access_token(credentials.credentials, settings)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def require_auth(
    token: Annotated[Optional[TokenPayload], Depends(get_current_token)],
) -> TokenPayload:
    """Require authenticated user.

    Args:
        token: Decoded token payload from get_current_token.

    Returns:
        Token payload.

    Raises:
        HTTPException: If not authenticated.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def optional_auth(
    token: Annotated[Optional[TokenPayload], Depends(get_current_token)],
) -> Optional[TokenPayload]:
    """Optional authentication - returns None if not authenticated.

    Args:
        token: Decoded token payload from get_current_token.

    Returns:
        Token payload if authenticated, None otherwise.
    """
    return token


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[TokenPayload, Depends(require_auth)]
OptionalUser = Annotated[Optional[TokenPayload], Depends(optional_auth)]
AppSettings = Annotated[Settings, Depends(get_settings)]
