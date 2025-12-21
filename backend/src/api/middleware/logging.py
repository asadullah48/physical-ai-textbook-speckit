"""Structured logging middleware for FastAPI."""

import logging
import sys
import time
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.config import get_settings


class StructuredLogger:
    """Structured logger with JSON output for production."""

    def __init__(self, name: str = "physical-ai-textbook"):
        self.logger = logging.getLogger(name)
        self._configure()

    def _configure(self):
        """Configure the logger based on environment."""
        settings = get_settings()

        # Clear existing handlers
        self.logger.handlers = []

        # Set level
        level = logging.DEBUG if settings.debug else logging.INFO
        self.logger.setLevel(level)

        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Format based on environment
        if settings.is_production:
            # JSON format for production
            import json

            class JSONFormatter(logging.Formatter):
                def format(self, record):
                    log_data = {
                        "timestamp": self.formatTime(record),
                        "level": record.levelname,
                        "message": record.getMessage(),
                        "logger": record.name,
                    }
                    if hasattr(record, "extra"):
                        log_data.update(record.extra)
                    if record.exc_info:
                        log_data["exception"] = self.formatException(record.exc_info)
                    return json.dumps(log_data)

            handler.setFormatter(JSONFormatter())
        else:
            # Human-readable format for development
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
            )
            handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def info(self, message: str, **kwargs):
        """Log info message with extra fields."""
        self.logger.info(message, extra={"extra": kwargs})

    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields."""
        self.logger.warning(message, extra={"extra": kwargs})

    def error(self, message: str, **kwargs):
        """Log error message with extra fields."""
        self.logger.error(message, extra={"extra": kwargs})

    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields."""
        self.logger.debug(message, extra={"extra": kwargs})


# Global logger instance
logger = StructuredLogger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid4())[:8]
        request.state.request_id = request_id

        # Log request
        start_time = time.perf_counter()
        logger.info(
            f"Request started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log response
            logger.info(
                f"Request completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise


def configure_logging(app):
    """Configure logging middleware for the application.

    Args:
        app: FastAPI application instance.
    """
    app.add_middleware(RequestLoggingMiddleware)
