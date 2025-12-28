# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
FastAPI-based HTTP server for AII API mode.

Features:
- RESTful API for function execution
- WebSocket streaming for real-time responses
- API key authentication
- Rate limiting per key
- CORS support for web integrations
- OpenAPI documentation
"""


from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Optional
from datetime import datetime

# Get version from package metadata (single source of truth: pyproject.toml)
try:
    from importlib.metadata import version
    __version__ = version("aiiware-cli")
except Exception:
    __version__ = "0.5.2"  # Fallback if package not installed

logger = logging.getLogger(__name__)

from aii.core.engine import AIIEngine
from aii.config.manager import ConfigManager
from aii.api.auth import APIKeyAuth
from aii.api.middleware import RateLimiter, set_server_instance
from aii.api.request_id import RequestIDMiddleware
from aii.api.routes import execute_router, functions_router, status_router, models_router, stats_router
from aii.api.websocket import handle_websocket_connection


app = FastAPI(
    title="Aii API",
    description="AI-powered command-line assistant API",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request ID middleware (must be first to ensure all requests get IDs)
app.add_middleware(RequestIDMiddleware)

# CORS middleware for web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Make configurable via config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules
app.include_router(execute_router)
app.include_router(functions_router)
app.include_router(status_router)
app.include_router(models_router)  # v0.8.0: Model discovery endpoint
app.include_router(stats_router)  # v0.9.0: Analytics endpoints


class APIServer:
    """
    HTTP server for AII API mode.

    Lifecycle:
    1. Initialize with AIIEngine and ConfigManager
    2. Start server with uvicorn
    3. Handle requests with authentication and rate limiting
    4. Shutdown gracefully

    Security:
    - API key authentication via Aii-API-Key header
    - Rate limiting per key (100 req/min default)
    - Request/response logging
    - CORS configuration
    """

    def __init__(self, engine: AIIEngine, config: ConfigManager, initialization_status: dict = None):
        self.engine = engine
        self.config = config
        self.rate_limiter = RateLimiter(config)
        self.auth = APIKeyAuth(config)
        self.start_time = datetime.now()
        self.server: Optional[uvicorn.Server] = None
        # Track initialization status for client guidance
        self.initialization_status = initialization_status or {
            "llm_provider": True,  # Assume initialized by default
            "llm_error": None,
            "web_search": False,
            "web_error": None
        }
        # Set global server instance for middleware access
        set_server_instance(self)

    async def start_server(self, host: str = "127.0.0.1", port: int = 8080):
        """Start HTTP server with uvicorn."""
        # Start execution logger (v0.9.0)
        if hasattr(self.engine, 'execution_logger') and self.engine.execution_logger:
            await self.engine.execution_logger.start()

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        self.server = uvicorn.Server(config)

        # Start server
        await self.server.serve()

    async def shutdown(self):
        """Graceful shutdown."""
        # Stop execution logger (v0.9.0)
        if hasattr(self.engine, 'execution_logger') and self.engine.execution_logger:
            await self.engine.execution_logger.stop()

        if self.server:
            self.server.should_exit = True

    def get_uptime(self) -> float:
        """Get server uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


# Global server instance (set by start_api_server)
server: Optional[APIServer] = None


# WebSocket endpoint for streaming
@app.websocket("/ws/execute")
async def websocket_execute(websocket: WebSocket):
    """
    WebSocket endpoint for streaming function execution.

    Delegates to handle_websocket_connection for modular pattern handling.
    See aii.api.websocket.handler for implementation details.
    """
    await handle_websocket_connection(websocket, server)
