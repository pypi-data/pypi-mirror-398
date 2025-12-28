# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Request ID middleware for request tracing.

Automatically generates and injects unique request IDs for every API request,
enabling correlation between client errors and server logs.

Features:
- Auto-generate UUIDs for each request
- Accept client-provided request IDs (Aii-Request-ID header)
- Inject request ID into request.state
- Add request ID to response headers
- Integrate with logging (contextvars)
"""


import uuid
import logging
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Context variable for request ID (thread-safe)
# This allows accessing request_id from anywhere in the request lifecycle
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default=None)


def get_request_id() -> str:
    """
    Get current request ID from context.

    Returns:
        Current request ID, or None if not set

    Usage:
        request_id = get_request_id()
        logger.info(f"Processing request {request_id}")
    """
    return request_id_ctx_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all requests.

    Features:
    1. Generate UUID for each request
    2. Accept client-provided request ID (Aii-Request-ID header)
    3. Inject into request.state.request_id
    4. Add to response headers (Aii-Request-ID)
    5. Store in context variable for logging

    Usage:
        app.add_middleware(RequestIDMiddleware)

    Client can provide request ID:
        curl -H "Aii-Request-ID: my-custom-id" http://localhost:16169/api/status

    Client receives request ID in response:
        Aii-Request-ID: abc123def456...
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with request ID injection.

        Flow:
        1. Check for client-provided request ID (Aii-Request-ID header)
        2. Generate UUID if not provided
        3. Inject into request.state
        4. Set context variable (for logging)
        5. Process request
        6. Add request ID to response headers
        """
        # Check if client provided request ID
        request_id = request.headers.get("Aii-Request-ID")

        # Generate new UUID if not provided
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        # Inject into request state (accessible in route handlers)
        request.state.request_id = request_id

        # Set context variable (accessible in logging)
        request_id_ctx_var.set(request_id)

        # Log request with ID
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["Aii-Request-ID"] = request_id

            # Log response with ID
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                }
            )

            return response

        except Exception as e:
            # Log error with request ID
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True
            )
            raise

        finally:
            # Clear context variable
            request_id_ctx_var.set(None)


class RequestIDLogFilter(logging.Filter):
    """
    Logging filter to add request ID to log records.

    Usage:
        import logging

        # Configure logging with request ID
        handler = logging.StreamHandler()
        handler.addFilter(RequestIDLogFilter())

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s'
        )
        handler.setFormatter(formatter)

        logger = logging.getLogger(__name__)
        logger.addHandler(handler)

    Output:
        2025-11-05 10:30:00 - aii.api - INFO - [req_abc123] - Request started
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request_id to log record.

        If request_id is already in extra data, use it.
        Otherwise, get from context variable.
        """
        if not hasattr(record, "request_id"):
            request_id = get_request_id()
            record.request_id = request_id if request_id else "-"

        return True
