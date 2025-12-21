"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.config import get_settings
from src.api.middleware.cors import configure_cors
from src.api.middleware.error_handler import configure_error_handlers
from src.api.middleware.logging import configure_logging
from src.api.middleware.rate_limit import configure_rate_limiting
from src.api.routes import auth, chat, health, progress
from src.db.connection import close_database
from src.services.qdrant import close_qdrant_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events.

    Args:
        app: The FastAPI application instance.
    """
    # Startup
    settings = get_settings()
    print(f"Starting Physical AI Textbook API in {settings.app_env} mode")

    yield

    # Shutdown
    print("Shutting down Physical AI Textbook API")
    await close_database()
    await close_qdrant_client()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Physical AI Textbook API",
        description="Backend API for the Physical AI & Humanoid Robotics Textbook platform",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Configure middleware
    configure_cors(app)
    configure_logging(app)
    configure_rate_limiting(app)
    configure_error_handlers(app)

    # Register routers
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(progress.router)

    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        return JSONResponse(
            content={
                "name": "Physical AI Textbook API",
                "version": "1.0.0",
                "docs": "/docs",
            }
        )

    return app


# Application instance
app = create_app()
