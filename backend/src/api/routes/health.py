"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from src.db.connection import check_database_connection
from src.services.qdrant import check_qdrant_connection
from src.models.schemas import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its dependencies.",
)
async def health_check() -> HealthResponse:
    """Perform health check on all services.

    Returns:
        HealthResponse with status of each service.
    """
    # Check database connection
    db_healthy = await check_database_connection()

    # The chat needs the vector store as much as the database: report
    # "healthy" only when both answer, so clients (the textbook site) can
    # fall back to in-browser retrieval instead of calling a half-working API.
    try:
        vector_store_healthy = await check_qdrant_connection()
    except Exception:  # noqa: BLE001 - a health check must not raise
        vector_store_healthy = False

    status = "healthy" if (db_healthy and vector_store_healthy) else "degraded"

    return HealthResponse(
        status=status,
        database=db_healthy,
        vector_store=vector_store_healthy,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ping",
    summary="Ping",
    description="Simple ping endpoint for load balancer health checks.",
)
async def ping() -> dict:
    """Simple ping endpoint.

    Returns:
        Simple pong response.
    """
    return {"ping": "pong"}
