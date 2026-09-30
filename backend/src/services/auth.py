"""JWT authentication service."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from src.api.config import Settings
from src.models.schemas import TokenPayload, TokenPair

# bcrypt is used directly: passlib 1.7.4 (unmaintained since 2020) crashes
# against bcrypt>=4.1 during its backend self-test, which broke every
# registration and login. Hashes stay standard $2b$ strings, so any hash
# written earlier by passlib still verifies.
_BCRYPT_MAX_BYTES = 72  # bcrypt ignores input past 72 bytes; make it explicit


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        Bcrypt hash of the password.
    """
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(_password_bytes(plain_password), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    """Hash a refresh token using SHA-256.

    Args:
        token: The refresh token to hash.

    Returns:
        SHA-256 hash of the token.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_refresh_token() -> str:
    """Generate a secure random refresh token.

    Returns:
        A cryptographically secure random token.
    """
    return secrets.token_urlsafe(32)


def create_access_token(
    user_id: UUID,
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: The user's UUID.
        settings: Application settings.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT access token.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token_jwt(
    user_id: UUID,
    settings: Settings,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        user_id: The user's UUID.
        settings: Application settings.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT refresh token.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(user_id: UUID, settings: Settings) -> TokenPair:
    """Create a pair of access and refresh tokens.

    Args:
        user_id: The user's UUID.
        settings: Application settings.

    Returns:
        TokenPair with access and refresh tokens.
    """
    access_token = create_access_token(user_id, settings)
    refresh_token = create_refresh_token_jwt(user_id, settings)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


def verify_access_token(token: str, settings: Settings) -> Optional[TokenPayload]:
    """Verify and decode a JWT access token.

    Args:
        token: The JWT access token to verify.
        settings: Application settings.

    Returns:
        TokenPayload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "access":
            return None

        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload["type"],
        )
    except JWTError:
        return None


def verify_refresh_token(token: str, settings: Settings) -> Optional[TokenPayload]:
    """Verify and decode a JWT refresh token.

    Args:
        token: The JWT refresh token to verify.
        settings: Application settings.

    Returns:
        TokenPayload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "refresh":
            return None

        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            type=payload["type"],
        )
    except JWTError:
        return None


def get_refresh_token_expiry(settings: Settings) -> datetime:
    """Get the expiration datetime for a new refresh token.

    Args:
        settings: Application settings.

    Returns:
        Expiration datetime.
    """
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
