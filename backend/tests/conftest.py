"""Pytest fixtures for backend tests.

Settings are required at import time, so test values are set before the app
is imported. No test talks to a real database, Qdrant or Gemini: those
boundaries are replaced with fakes in the tests that need them.
"""

import os

os.environ.update(
    {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test",
        "QDRANT_URL": "http://localhost:6333",
        "QDRANT_API_KEY": "test-qdrant-key",
        "GOOGLE_API_KEY": "test-google-key",
        "JWT_SECRET_KEY": "test-secret-key-that-is-long-enough-for-hs256",
        "APP_ENV": "test",
    }
)

from typing import AsyncGenerator  # noqa: E402

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from src.api.main import app  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client bound to the app in-process."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
