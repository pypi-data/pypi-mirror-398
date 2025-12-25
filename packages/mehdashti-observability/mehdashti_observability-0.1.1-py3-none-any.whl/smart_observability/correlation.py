"""Correlation ID middleware and utilities for request tracing."""

import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable to store the current correlation ID
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Header name for correlation ID
CORRELATION_ID_HEADER = "X-Correlation-Id"


def get_correlation_id() -> str | None:
    """
    Get the current correlation ID from context.

    Returns:
        The correlation ID for the current request, or None if not set.

    Example:
        ```python
        correlation_id = get_correlation_id()
        logger.info("Processing request", extra={"correlation_id": correlation_id})
        ```
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID in context.

    Args:
        correlation_id: The correlation ID to set

    Example:
        ```python
        set_correlation_id("123e4567-e89b-12d3-a456-426614174000")
        ```
    """
    _correlation_id.set(correlation_id)


def generate_correlation_id() -> str:
    """
    Generate a new correlation ID.

    Returns:
        A new UUID v4 correlation ID

    Example:
        ```python
        correlation_id = generate_correlation_id()
        # => "123e4567-e89b-12d3-a456-426614174000"
        ```
    """
    return str(uuid.uuid4())


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    FastAPI/Starlette middleware that adds correlation ID tracking to requests.

    This middleware:
    1. Extracts correlation ID from incoming request headers (X-Correlation-Id)
    2. Generates a new correlation ID if none provided
    3. Stores the correlation ID in context for the duration of the request
    4. Adds the correlation ID to the response headers

    Example:
        ```python
        from fastapi import FastAPI
        from smart_observability import CorrelationMiddleware

        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/users")
        async def get_users():
            correlation_id = get_correlation_id()
            logger.info("Fetching users", extra={"correlation_id": correlation_id})
            return {"users": []}
        ```
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and inject correlation ID.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The HTTP response with correlation ID header
        """
        # Extract correlation ID from request header or generate new one
        correlation_id = request.headers.get(
            CORRELATION_ID_HEADER, generate_correlation_id()
        )

        # Store in context for the duration of the request
        set_correlation_id(correlation_id)

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers
        response.headers[CORRELATION_ID_HEADER] = correlation_id

        return response
