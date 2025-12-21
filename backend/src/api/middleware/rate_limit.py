"""Rate limiting middleware for FastAPI.

Implements a sliding window rate limiter using in-memory storage.
For production, consider using Redis for distributed rate limiting.
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.config import get_settings


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10  # Max requests in 1 second


class SlidingWindowCounter:
    """Sliding window rate limiter implementation."""

    def __init__(self):
        # {client_key: [(timestamp, count), ...]}
        self.windows: Dict[str, list] = defaultdict(list)

    def is_allowed(
        self,
        client_key: str,
        window_seconds: int,
        max_requests: int,
    ) -> tuple[bool, int]:
        """Check if request is allowed and return remaining quota.

        Args:
            client_key: Unique identifier for the client.
            window_seconds: Size of the sliding window in seconds.
            max_requests: Maximum requests allowed in the window.

        Returns:
            Tuple of (is_allowed, remaining_requests).
        """
        now = time.time()
        window_start = now - window_seconds

        # Get existing window data
        window_data = self.windows[client_key]

        # Remove expired entries
        window_data = [(ts, count) for ts, count in window_data if ts > window_start]

        # Count requests in current window
        total_requests = sum(count for _, count in window_data)

        if total_requests >= max_requests:
            return False, 0

        # Add current request
        window_data.append((now, 1))
        self.windows[client_key] = window_data

        remaining = max_requests - total_requests - 1
        return True, max(0, remaining)

    def cleanup(self, max_age_seconds: int = 3600):
        """Remove old entries to prevent memory growth.

        Args:
            max_age_seconds: Remove entries older than this.
        """
        cutoff = time.time() - max_age_seconds
        for key in list(self.windows.keys()):
            self.windows[key] = [
                (ts, count) for ts, count in self.windows[key] if ts > cutoff
            ]
            if not self.windows[key]:
                del self.windows[key]


# Global rate limiter instance
_rate_limiter = SlidingWindowCounter()


def get_client_key(request: Request) -> str:
    """Get unique identifier for rate limiting.

    Uses IP address for unauthenticated requests,
    user ID for authenticated requests.

    Args:
        request: FastAPI request object.

    Returns:
        Unique client identifier.
    """
    # Check for authenticated user
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"

    # Fall back to IP
    client_ip = request.client.host if request.client else "unknown"

    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    return f"ip:{client_ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(
        self,
        app,
        config: Optional[RateLimitConfig] = None,
        exclude_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.exclude_paths = exclude_paths or ["/api/health", "/docs", "/openapi.json"]
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Get client key
        client_key = get_client_key(request)

        # Check per-minute limit
        allowed, remaining = _rate_limiter.is_allowed(
            f"{client_key}:minute",
            window_seconds=60,
            max_requests=self.config.requests_per_minute,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # Check burst limit
        burst_allowed, _ = _rate_limiter.is_allowed(
            f"{client_key}:burst",
            window_seconds=1,
            max_requests=self.config.burst_limit,
        )

        if not burst_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": "1"},
            )

        # Periodic cleanup
        now = time.time()
        if now - self._last_cleanup > 300:  # Every 5 minutes
            _rate_limiter.cleanup()
            self._last_cleanup = now

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


def configure_rate_limiting(app, config: Optional[RateLimitConfig] = None):
    """Configure rate limiting middleware for the application.

    Args:
        app: FastAPI application instance.
        config: Optional rate limit configuration.
    """
    settings = get_settings()

    # Only enable rate limiting in production by default
    if not settings.is_production and not settings.debug:
        return

    app.add_middleware(
        RateLimitMiddleware,
        config=config,
        exclude_paths=["/api/health", "/docs", "/redoc", "/openapi.json"],
    )
