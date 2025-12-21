"""CORS middleware configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
        expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
        max_age=600,  # Cache preflight requests for 10 minutes
    )
