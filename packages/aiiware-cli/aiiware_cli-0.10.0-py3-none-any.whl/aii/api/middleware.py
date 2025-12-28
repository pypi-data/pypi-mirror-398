# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Middleware components for Aii API server (rate limiting, authentication)."""


from datetime import datetime
from typing import Dict

from fastapi import HTTPException, Depends, Header
from fastapi.responses import JSONResponse

from aii.config.manager import ConfigManager
from aii.api.errors import (
    MissingAPIKeyError,
    InvalidAPIKeyError,
    RateLimitError,
    ErrorResponse,
    format_error_response,
)


class RateLimiter:
    """Rate limiter per API key."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.limits: Dict[str, tuple[int, datetime]] = {}  # api_key -> (count, window_start)
        self.max_requests = config.get("api.rate_limit.max_requests", 100)
        self.window_seconds = config.get("api.rate_limit.window_seconds", 60)

    def allow(self, api_key: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.now()

        if api_key not in self.limits:
            self.limits[api_key] = (1, now)
            return True

        count, window_start = self.limits[api_key]

        # Check if window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            # Reset window
            self.limits[api_key] = (1, now)
            return True

        # Check if limit exceeded
        if count >= self.max_requests:
            return False

        # Increment count
        self.limits[api_key] = (count + 1, window_start)
        return True

    def get_remaining(self, api_key: str) -> int:
        """Get remaining requests in current window."""
        if api_key not in self.limits:
            return self.max_requests

        count, window_start = self.limits[api_key]
        now = datetime.now()

        # Window expired
        if (now - window_start).total_seconds() > self.window_seconds:
            return self.max_requests

        return max(0, self.max_requests - count)


# Global server instance reference (set by server.py)
# This allows middleware to access server.auth and server.rate_limiter
_server_instance = None


def set_server_instance(server_inst):
    """Set global server instance for middleware access."""
    global _server_instance
    _server_instance = server_inst


def get_server_instance():
    """Get global server instance."""
    return _server_instance


# Authentication middleware
async def verify_api_key(
    aii_api_key_new: str = Header(None, alias="Aii-API-Key"),
    aii_api_key_old: str = Header(None, alias="AII-API-Key")
) -> str:
    """
    Verify API key from Aii-API-Key or AII-API-Key header.

    Accepts both formats for backward compatibility:
    - Aii-API-Key (recommended)
    - AII-API-Key (legacy)

    Raises structured errors:
    - MissingAPIKeyError (401) if header is missing
    - InvalidAPIKeyError (401) if key is invalid
    """
    # Accept both new and old header formats (backward compatibility)
    aii_api_key = aii_api_key_new or aii_api_key_old

    if not aii_api_key:
        error = MissingAPIKeyError()
        error_detail = format_error_response(error)
        raise HTTPException(
            status_code=error.status_code,
            detail=ErrorResponse(error=error_detail).dict()
        )

    server = get_server_instance()
    if not server or not server.auth.verify_key(aii_api_key):
        error = InvalidAPIKeyError()
        error_detail = format_error_response(error)
        raise HTTPException(
            status_code=error.status_code,
            detail=ErrorResponse(error=error_detail).dict()
        )

    return aii_api_key


# Rate limiting middleware
async def check_rate_limit(api_key: str = Depends(verify_api_key)):
    """
    Check rate limit for API key.

    Raises structured RateLimitError (429) if limit exceeded.
    """
    server = get_server_instance()
    if not server:
        return

    if not server.rate_limiter.allow(api_key):
        remaining = server.rate_limiter.get_remaining(api_key)
        retry_after = server.rate_limiter.window_seconds

        error = RateLimitError(retry_after=retry_after)
        error_detail = format_error_response(error)

        raise HTTPException(
            status_code=error.status_code,
            detail=ErrorResponse(error=error_detail).dict(),
            headers={
                "X-RateLimit-Limit": str(server.rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(retry_after),
                "Retry-After": str(retry_after)
            }
        )
