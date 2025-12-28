# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Client-side MCP executor for cloud-compatible architecture.

This module handles MCP tool execution on the client side when the Aii server
is running in cloud mode (v0.6.0+).

Architecture:
- Server: Selects MCP tools based on user request (LLM intelligence)
- Client: Executes MCP tools locally (stdio transport requirement)
- Communication: WebSocket messages for tool queries and execution requests
"""


import asyncio
import logging
import sys
import os
from contextlib import contextmanager
from typing import Any

from ..data.integrations.mcp.client_manager import MCPClientManager
from ..data.integrations.mcp.models import MCPTool, ToolCallResult

logger = logging.getLogger(__name__)


@contextmanager
def suppress_mcp_server_logs():
    """
    Context manager to suppress MCP server subprocess stderr at the OS level.

    MCP servers write initialization logs to stderr. Since they run as subprocesses
    with inherited file descriptors, we need to redirect FD 2 (stderr) at the OS level.

    stdout (FD 1) is NOT redirected because MCP uses it for JSON-RPC communication.
    """
    # Save original stderr file descriptor
    stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(stderr_fd)

    try:
        # Redirect stderr to /dev/null at OS level
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        os.close(devnull_fd)
        yield
    finally:
        # Restore original stderr
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(saved_stderr_fd)


class ClientMCPExecutor:
    """
    Client-side MCP executor for cloud-compatible architecture.

    Handles MCP tool execution requests from the server via WebSocket.

    Flow:
    1. Server sends mcp_query_tools request → Client returns available tools
    2. Server sends mcp_tool_request → Client executes tool and returns result
    """

    def __init__(self, mcp_client: MCPClientManager):
        """
        Initialize client MCP executor.

        Args:
            mcp_client: MCPClientManager instance with configured MCP servers
        """
        self.mcp_client = mcp_client
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize MCP client (connect to all configured servers).

        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True

        try:
            # v0.6.0: Suppress MCP server initialization logs (stderr at OS level)
            with suppress_mcp_server_logs():
                await self.mcp_client.initialize()
            self._initialized = True
            logger.info("Client MCP executor initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}", exc_info=True)
            return False

    async def handle_query_tools(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Handle mcp_query_tools request from server.

        Server asks: "What MCP tools are available?"
        Client responds with list of all available tools across all servers.

        Args:
            message: WebSocket message with type="mcp_query_tools"

        Returns:
            Response message with type="mcp_query_tools_response" and tools list
        """
        request_id = message.get("request_id", "unknown")
        logger.info(f"Handling mcp_query_tools request: {request_id}")

        # Ensure client is initialized
        if not self._initialized:
            await self.initialize()

        try:
            # v0.6.0: Pass user_request for smart lazy connection (only connect to relevant servers)
            user_request = message.get("user_request")
            tools = await self.mcp_client.discover_all_tools(user_request=user_request)

            # Convert MCPTool objects to serializable dicts
            tools_data = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "server_name": tool.server_name,
                }
                for tool in tools
            ]

            logger.info(f"Found {len(tools_data)} MCP tools across all servers")

            return {
                "type": "mcp_query_tools_response",
                "request_id": request_id,
                "success": True,
                "tools": tools_data,
            }

        except Exception as e:
            logger.error(f"Error querying MCP tools: {e}", exc_info=True)
            return {
                "type": "mcp_query_tools_response",
                "request_id": request_id,
                "success": False,
                "error": str(e),
                "tools": [],
            }

    async def handle_tool_execution(self, message: dict[str, Any]) -> dict[str, Any]:
        """
        Handle mcp_tool_request from server.

        Server asks: "Execute this tool with these arguments"
        Client executes tool locally and returns result.

        Args:
            message: WebSocket message with:
                - type: "mcp_tool_request"
                - tool_name: Name of tool to execute
                - arguments: Tool arguments (dict)

        Returns:
            Response message with type="mcp_tool_response" and execution result
        """
        request_id = message.get("request_id", "unknown")
        tool_name = message.get("tool_name")
        arguments = message.get("arguments", {})

        logger.info(f"Handling mcp_tool_request: {request_id} - Tool: {tool_name}")

        # Validate request
        if not tool_name:
            return {
                "type": "mcp_tool_response",
                "request_id": request_id,
                "success": False,
                "error": "Missing tool_name in request",
            }

        # Ensure client is initialized
        if not self._initialized:
            await self.initialize()

        try:
            # Execute tool via MCP client with timeout (v0.6.0)
            # Prevent hanging on slow/broken MCP servers
            result: ToolCallResult = await asyncio.wait_for(
                self.mcp_client.call_tool(
                    tool_name=tool_name,
                    arguments=arguments
                ),
                timeout=30.0  # 30 second timeout for MCP tool execution
            )

            # Serialize content (may contain complex types)
            serializable_content = self._make_content_serializable(result.content)

            logger.info(
                f"Tool '{tool_name}' executed successfully on client "
                f"(server: {result.server_name})"
            )

            return {
                "type": "mcp_tool_response",
                "request_id": request_id,
                "success": result.success,
                "content": serializable_content,
                "server_name": result.server_name,
                "error": result.error if not result.success else None,
            }

        except asyncio.TimeoutError:
            error_msg = f"MCP tool '{tool_name}' timed out after 30 seconds. The server may be slow or unresponsive."
            logger.error(error_msg)
            return {
                "type": "mcp_tool_response",
                "request_id": request_id,
                "success": False,
                "error": error_msg,
            }
        except Exception as e:
            logger.error(f"Error executing MCP tool '{tool_name}': {e}", exc_info=True)
            return {
                "type": "mcp_tool_response",
                "request_id": request_id,
                "success": False,
                "error": str(e),
            }

    def _make_content_serializable(self, content: Any) -> Any:
        """
        Convert content to JSON-serializable format.

        MCP tool results may contain complex types that need serialization.

        Args:
            content: Tool result content

        Returns:
            JSON-serializable content
        """
        if content is None:
            return None

        # List of content items
        if isinstance(content, list):
            return [self._make_content_serializable(item) for item in content]

        # Dict-like content
        if isinstance(content, dict):
            return {
                key: self._make_content_serializable(value)
                for key, value in content.items()
            }

        # String content
        if isinstance(content, str):
            return content

        # Numeric content
        if isinstance(content, (int, float, bool)):
            return content

        # Object with __dict__ (like MCP content objects)
        if hasattr(content, "__dict__"):
            return self._make_content_serializable(content.__dict__)

        # Object with to_dict() method
        if hasattr(content, "to_dict"):
            return self._make_content_serializable(content.to_dict())

        # Fallback: string representation
        return str(content)

    async def shutdown(self):
        """Shutdown MCP client and cleanup resources."""
        if self._initialized:
            try:
                await self.mcp_client.shutdown()
                self._initialized = False
                logger.info("Client MCP executor shut down")
            except Exception as e:
                logger.error(f"Error shutting down MCP client: {e}", exc_info=True)
