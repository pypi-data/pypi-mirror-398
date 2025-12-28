# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Status and health check endpoints."""


import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends

from aii.api.models import StatusResponse, MCPStatusRequest
from aii.api.middleware import verify_api_key, check_rate_limit, get_server_instance

# Get version from package metadata
try:
    from importlib.metadata import version
    __version__ = version("aiiware-cli")
except Exception:
    __version__ = "0.6.3"

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Simple health check endpoint for server monitoring.

    Used by CLI to detect if server is running.
    Returns 200 OK if server is healthy.

    No authentication required for health check.

    Response:
    ```json
    {
      "status": "healthy",
      "version": "0.6.0"
    }
    ```
    """
    return {
        "status": "healthy",
        "version": __version__
    }


@router.get("/api/status", response_model=StatusResponse)
async def get_status():
    """
    Get server health status.

    No authentication required for status endpoint.

    Response:
    ```json
    {
      "status": "healthy",
      "version": "0.4.12",
      "uptime": 3600.5,
      "mcp_servers": {
        "total": 7,
        "enabled": 7
      }
    }
    ```
    """
    server = get_server_instance()

    if not server:
        return StatusResponse(
            status="initializing",
            version=__version__,
            uptime=0.0
        )

    mcp_info = None
    try:
        # Load MCP server config from mcp_servers.json
        mcp_config_path = Path.home() / ".aii" / "mcp_servers.json"
        if mcp_config_path.exists():
            with open(mcp_config_path, "r") as f:
                config = json.load(f)
                servers = config.get("mcpServers", {})

                # Count total and enabled servers
                total = len(servers)
                enabled = sum(1 for s in servers.values() if s.get("enabled", True))

                mcp_info = {
                    "total": total,
                    "enabled": enabled
                }
    except Exception as e:
        # Silently fail for status endpoint
        logger.debug(f"Failed to load MCP server info: {e}")
        pass

    return StatusResponse(
        status="healthy",
        version=__version__,
        uptime=server.get_uptime(),
        mcp_servers=mcp_info,
        initialization=server.initialization_status
    )


@router.post("/api/mcp/status")
async def mcp_status(
    request: MCPStatusRequest,
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit)
):
    """
    Get health status for MCP servers.

    Request:
    ```json
    {
      "server_name": "github"  // optional, null for all
    }
    ```
    """
    server = get_server_instance()

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Execute mcp_status function if available
    try:
        result = await server.engine.process_input(
            user_input=f"mcp status {request.server_name or ''}",
            context=None
        )

        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=500, detail=result.message)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
