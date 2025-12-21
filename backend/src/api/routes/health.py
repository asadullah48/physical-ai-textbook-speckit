"""Health check endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter

from src.db.connection import check_database_connection
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

    # TODO: Add vector store health check when Qdrant service is implemented
    vector_store_healthy = None

    # Determine overall status
    if db_healthy:
        status = "healthy"
    else:
        status = "degraded"

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
