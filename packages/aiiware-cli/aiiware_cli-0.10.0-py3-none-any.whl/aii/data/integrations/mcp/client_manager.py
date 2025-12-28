# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Client Manager

Manages connections to multiple MCP servers and provides unified access
to tools, resources, and prompts across all connected servers.

Features:
- Multi-server connection management
- Tool/resource/prompt discovery and aggregation
- Tool invocation routing
- Session lifecycle management
- Error handling and graceful degradation
"""


import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aii.data.integrations.mcp.config_loader import MCPConfigLoader, ServerConfig
from aii.data.integrations.mcp.models import (
    MCPTool,
    MCPResource,
    MCPPrompt,
    ServerConnection,
    ConnectionState,
    ToolCallResult
)

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to multiple MCP servers.

    This is the core component that:
    1. Connects to all configured MCP servers
    2. Discovers capabilities (tools/resources/prompts)
    3. Routes requests to appropriate servers
    4. Manages session lifecycle
    """

    def __init__(self, config_loader: Optional[MCPConfigLoader] = None, enable_health_monitoring: bool = True):
        """
        Initialize MCP Client Manager.

        Args:
            config_loader: Optional config loader (creates default if None)
            enable_health_monitoring: Enable background health monitoring (v0.4.10)
        """
        self.config_loader = config_loader or MCPConfigLoader()
        self.connections: Dict[str, ServerConnection] = {}
        self._tool_cache: Dict[str, List[MCPTool]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._initialized = False
        self._entered = False

        # Health monitoring (v0.4.10)
        self.health_monitor: Optional[Any] = None
        self._enable_health_monitoring = enable_health_monitoring

    async def __aenter__(self):
        """
        Enter async context - connect to all MCP servers.

        This must be called to establish connections. All operations
        (tool calls, etc.) happen within this context.
        """
        if self._entered:
            raise RuntimeError("MCPClientManager is already entered")

        await self.initialize()
        self._entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context - disconnect from all MCP servers.

        Properly closes all connections and cleans up resources.
        """
        await self.shutdown()
        self._entered = False
        return False

    async def initialize(self):
        """
        Initialize the client manager with lazy connection (v0.4.11 optimization).

        Loads server configurations but does NOT connect to servers yet.
        Connections are created on-demand when tools are actually called.

        Benefits:
        - Fast startup: <500ms (vs 3-5s connecting to all servers)
        - Clean output: No server startup logs until needed
        - Lower resource usage: Only connect to servers you actually use
        """
        if self._initialized:
            logger.debug("MCP Client Manager already initialized")
            return

        logger.info("Initializing MCP Client Manager (lazy connection mode)")

        # Load configurations
        servers = self.config_loader.load_configurations()
        logger.info(f"Loaded {len(servers)} server configurations")

        # v0.4.11: SKIP connect_all_servers() - connect on-demand instead!
        # This makes startup instant and eliminates noisy server logs

        # Start health monitoring (v0.4.11)
        # Note: Health checks will connect to servers on-demand
        import os
        debug = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")
        if debug:
            print(f"🔍 DEBUG: Starting health monitoring (lazy mode)")

        if self._enable_health_monitoring:
            await self._start_health_monitoring()

        self._initialized = True
        logger.info(f"MCP Client Manager initialized (lazy mode, {len(self.config_loader.servers)} servers configured)")

    async def connect_all_servers(self):
        """
        Discover tools from all configured MCP servers.

        Creates temporary connections to each server to discover available
        tools, then cleanly closes the connections.

        Note: Only connects to ENABLED servers (v0.6.0 - skip disabled servers)
        """
        servers = self.config_loader.servers

        # Discover tools from servers in parallel (v0.6.0: filter by enabled status)
        tasks = [
            self.discover_server_tools(server_name, server_config)
            for server_name, server_config in servers.items()
            if server_config.enabled  # v0.6.0: Skip disabled servers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log results
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        logger.info(f"Tool discovery: {successful} successful, {failed} failed")

    async def discover_server_tools(self, server_name: str, config: ServerConfig) -> bool:
        """
        Discover tools from a server using a PERSISTENT connection (v0.4.10 optimization).

        Args:
            server_name: Name of the server
            config: Server configuration

        Returns:
            True if discovery successful, False otherwise
        """
        logger.info(f"Discovering tools from server: {server_name}")

        # Create connection metadata object
        connection = ServerConnection(
            name=server_name,
            state=ConnectionState.CONNECTING
        )
        self.connections[server_name] = connection

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or {}
            )

            # Create PERSISTENT connection (v0.4.10)
            # Store context managers to keep connection alive
            stdio_context = stdio_client(server_params)
            read, write = await stdio_context.__aenter__()

            session_context = ClientSession(read, write)
            session = await session_context.__aenter__()

            # Store contexts for cleanup
            connection.stdio_context = stdio_context
            connection.session = session
            connection._session_context = session_context  # Keep reference for cleanup

            # Initialize
            await session.initialize()

            # Discover tools
            tools_response = await session.list_tools()
            connection.tools = [
                MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema,
                    server_name=server_name
                )
                for tool in tools_response.tools
            ]
            logger.info(f"Discovered {len(connection.tools)} tools from {server_name}")

            # Discover resources (optional)
            try:
                resources_response = await session.list_resources()
                connection.resources = [
                    MCPResource(
                        uri=resource.uri,
                        name=resource.name,
                        description=resource.description,
                        mime_type=resource.mimeType,
                        server_name=server_name
                    )
                    for resource in resources_response.resources
                ]
                logger.info(f"Discovered {len(connection.resources)} resources from {server_name}")
            except Exception as e:
                logger.debug(f"No resources from {server_name}: {e}")

            # Discover prompts (optional)
            try:
                prompts_response = await session.list_prompts()
                connection.prompts = [
                    MCPPrompt(
                        name=prompt.name,
                        description=prompt.description,
                        arguments=prompt.arguments,
                        server_name=server_name
                    )
                    for prompt in prompts_response.prompts
                ]
                logger.info(f"Discovered {len(connection.prompts)} prompts from {server_name}")
            except Exception as e:
                logger.debug(f"No prompts from {server_name}: {e}")

            # Connection closed cleanly - mark as available
            connection.state = ConnectionState.CONNECTED
            return True

        except Exception as e:
            logger.error(f"Failed to discover tools from {server_name}: {e}")
            connection.state = ConnectionState.ERROR
            connection.error = str(e)
            return False

    async def connect_server(self, server_name: str, config: ServerConfig) -> bool:
        """
        DEPRECATED: Use discover_server_tools() instead.

        This method attempted to maintain persistent connections but fails
        due to async context manager lifecycle issues. Use per-request
        connections via call_tool() instead.

        Args:
            server_name: Name of the server
            config: Server configuration

        Returns:
            True if connected successfully, False otherwise
        """
        logger.info(f"Connecting to server: {server_name}")

        # Create connection object
        connection = ServerConnection(
            name=server_name,
            state=ConnectionState.CONNECTING
        )
        self.connections[server_name] = connection

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or {}
            )

            # Connect to server using stdio transport
            # Use proper nested async with to ensure correct lifecycle
            stdio_ctx = stdio_client(server_params)
            read, write = await stdio_ctx.__aenter__()
            connection.stdio_context = stdio_ctx

            # Create and enter session context
            session_ctx = ClientSession(read, write)
            await session_ctx.__aenter__()
            connection.session = session_ctx

            # Initialize the session
            await session_ctx.initialize()

            # Update connection state
            connection.state = ConnectionState.CONNECTED
            logger.info(f"Successfully connected to {server_name}")

            # Discover capabilities
            await self._discover_capabilities(server_name, connection)

            return True

        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            connection.state = ConnectionState.ERROR
            connection.error = str(e)

            # Clean up on error
            if connection.session:
                try:
                    await connection.session.__aexit__(type(e), e, e.__traceback__)
                except:
                    pass
            if connection.stdio_context:
                try:
                    await connection.stdio_context.__aexit__(type(e), e, e.__traceback__)
                except:
                    pass

            return False

    async def _discover_capabilities(self, server_name: str, connection: ServerConnection):
        """
        Discover capabilities (tools/resources/prompts) from a server.

        Args:
            server_name: Name of the server
            connection: Server connection object
        """
        if not connection.session:
            return

        try:
            # Discover tools
            tools_response = await connection.session.list_tools()
            connection.tools = [
                MCPTool(
                    name=tool.name,
                    description=tool.description or "",
                    input_schema=tool.inputSchema,
                    server_name=server_name
                )
                for tool in tools_response.tools
            ]
            logger.info(f"Discovered {len(connection.tools)} tools from {server_name}")

            # Discover resources
            try:
                resources_response = await connection.session.list_resources()
                connection.resources = [
                    MCPResource(
                        uri=resource.uri,
                        name=resource.name,
                        description=resource.description,
                        mime_type=resource.mimeType,
                        server_name=server_name
                    )
                    for resource in resources_response.resources
                ]
                logger.info(f"Discovered {len(connection.resources)} resources from {server_name}")
            except Exception as e:
                logger.debug(f"No resources from {server_name}: {e}")

            # Discover prompts
            try:
                prompts_response = await connection.session.list_prompts()
                connection.prompts = [
                    MCPPrompt(
                        name=prompt.name,
                        description=prompt.description,
                        arguments=prompt.arguments,
                        server_name=server_name
                    )
                    for prompt in prompts_response.prompts
                ]
                logger.info(f"Discovered {len(connection.prompts)} prompts from {server_name}")
            except Exception as e:
                logger.debug(f"No prompts from {server_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover capabilities from {server_name}: {e}")

    def _infer_servers_from_request(self, user_request: str) -> List[str]:
        """
        Infer which servers are likely needed based on user request (v0.4.11).

        Uses keyword matching to determine relevant servers, avoiding
        unnecessary connections for unrelated servers.

        Args:
            user_request: User's natural language request

        Returns:
            List of server names likely needed (empty = all servers)
        """
        # Ensure servers are loaded
        if not self.config_loader.servers:
            self.config_loader.load_configurations()

        request_lower = user_request.lower()
        relevant_servers = []

        # GitHub keywords - check if request mentions GitHub OR GitHub operations
        github_keywords = ["github"]
        github_operations = ["issue", "pull request", "pr", "repository", "repo"]

        has_github_mention = any(kw in request_lower for kw in github_keywords)
        has_github_operation = any(op in request_lower for op in github_operations)

        if (has_github_mention or has_github_operation) and "github" in self.config_loader.servers:
            relevant_servers.append("github")

        # Filesystem keywords
        filesystem_keywords = [
            "file", "read", "write", "directory", "folder", "path",
            "create file", "delete file", "list files", "search files"
        ]
        if any(kw in request_lower for kw in filesystem_keywords):
            if "filesystem" in self.config_loader.servers:
                relevant_servers.append("filesystem")

        # Chinese railway keywords (12306)
        railway_keywords = [
            "火车", "高铁", "动车", "车票", "余票", "12306",
            "车站", "列车", "查询火车", "查询车票", "北京", "上海"
        ]
        if any(kw in request_lower for kw in railway_keywords):
            if "12306-mcp" in self.config_loader.servers:
                relevant_servers.append("12306-mcp")

        # Browser/web automation keywords
        browser_keywords = [
            "browser", "chrome", "screenshot", "navigate", "click",
            "puppeteer", "devtools", "web page"
        ]
        if any(kw in request_lower for kw in browser_keywords):
            if "chrome-devtools" in self.config_loader.servers:
                relevant_servers.append("chrome-devtools")
            if "puppeteer" in self.config_loader.servers:
                relevant_servers.append("puppeteer")

        # Airbnb keywords
        airbnb_keywords = ["airbnb", "listing", "property", "accommodation"]
        if any(kw in request_lower for kw in airbnb_keywords):
            if "airbnb" in self.config_loader.servers:
                relevant_servers.append("airbnb")

        # Google Maps keywords (v0.6.0)
        maps_keywords = [
            "map", "maps", "google maps", "directions", "route", "navigation",
            "location", "geocode", "address", "place", "places api",
            "3d maps", "photorealistic", "street view", "elevation",
            "distance matrix", "nearby", "poi", "point of interest"
        ]
        if any(kw in request_lower for kw in maps_keywords):
            # Check for both possible Google Maps server names
            for server_name in self.config_loader.servers:
                if "google" in server_name.lower() and "map" in server_name.lower():
                    if server_name not in relevant_servers:  # Avoid duplicates
                        relevant_servers.append(server_name)

        return relevant_servers

    async def discover_all_tools(self, user_request: str = None) -> List[MCPTool]:
        """
        Discover and aggregate tools from servers (v0.4.11 smart lazy connection).

        With smart lazy connection, this method:
        1. Infers relevant servers from user request (if provided)
        2. Connects only to relevant servers
        3. Falls back to all servers if inference is uncertain

        Args:
            user_request: Optional user request for server inference

        Returns:
            List of all available tools across connected servers
        """
        # Lazy initialization
        if not self._initialized:
            await self.initialize()

        # v0.4.11 smart lazy connection: Selective server discovery
        if user_request:
            # Infer which servers are needed
            relevant_servers = self._infer_servers_from_request(user_request)

            if relevant_servers:
                # Connect only to inferred servers (if not already connected)
                logger.info(f"Inferred relevant servers from request: {relevant_servers}")
                for server_name in relevant_servers:
                    if server_name not in self.connections or self.connections[server_name].state != ConnectionState.CONNECTED:
                        logger.info(f"Connecting to {server_name} (smart lazy mode)")
                        server_config = self.config_loader.get_server(server_name)
                        if server_config:
                            await self.discover_server_tools(server_name, server_config)
            elif not self.connections:
                # No clear inference and no connections yet - connect to all servers
                logger.info("Could not infer servers, connecting all (fallback mode)...")
                await self.connect_all_servers()
        elif not self.connections:
            # No user request provided and no connections yet - connect all servers
            logger.info("No context provided, connecting all servers (lazy mode)...")
            await self.connect_all_servers()

        all_tools = []

        for server_name, connection in self.connections.items():
            if connection.state == ConnectionState.CONNECTED:
                all_tools.extend(connection.tools)

        logger.info(f"Total tools available: {len(all_tools)}")
        return all_tools

    async def discover_all_resources(self) -> List[MCPResource]:
        """
        Discover and aggregate resources from all connected servers.

        Returns:
            List of all available resources across all servers
        """
        # Lazy initialization
        if not self._initialized:
            await self.initialize()

        all_resources = []

        for server_name, connection in self.connections.items():
            if connection.state == ConnectionState.CONNECTED:
                all_resources.extend(connection.resources)

        logger.info(f"Total resources available: {len(all_resources)}")
        return all_resources

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """
        Get a specific tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            MCPTool if found, None otherwise
        """
        for connection in self.connections.values():
            for tool in connection.tools:
                if tool.name == tool_name:
                    return tool
        return None

    def find_server_for_tool(self, tool_name: str) -> Optional[str]:
        """
        Find which server provides a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Server name if found, None otherwise
        """
        tool = self.get_tool(tool_name)
        return tool.server_name if tool else None

    async def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """
        Call a tool by routing to the appropriate server.

        Uses per-request connection pattern: creates a fresh connection,
        calls the tool, and cleanly exits. This ensures proper async
        lifecycle management.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            ToolCallResult with the result
        """
        # Lazy initialization (for tool discovery only)
        if not self._initialized:
            await self.initialize()

        # Find which server provides this tool
        server_name = self.find_server_for_tool(tool_name)

        if not server_name:
            return ToolCallResult(
                success=False,
                content=None,
                error=f"Tool '{tool_name}' not found in any server",
                is_error=True
            )

        # Get server connection (v0.4.11: lazy connection on-demand)
        connection = self.connections.get(server_name)
        if not connection or not connection.session:
            # Lazy connection: Connect on first use
            logger.info(f"Connecting to '{server_name}' on-demand (lazy mode)")

            # Get server config
            server_config = self.config_loader.get_server(server_name)
            if not server_config:
                return ToolCallResult(
                    success=False,
                    content=None,
                    error=f"Server '{server_name}' configuration not found",
                    server_name=server_name,
                    is_error=True
                )

            # Discover tools (creates persistent connection)
            await self.discover_server_tools(server_name, server_config)

            # Get connection again
            connection = self.connections.get(server_name)
            if not connection or not connection.session:
                # Connection failed - fallback to temporary
                logger.warning(f"Failed to establish persistent connection for '{server_name}', using temporary")
                return await self._call_tool_with_temp_connection(server_name, tool_name, arguments)

        # Use persistent connection (v0.4.10 optimization)
        try:
            logger.info(f"Calling tool '{tool_name}' on server '{server_name}' (reusing persistent connection)")

            # Call the tool using existing session
            result = await connection.session.call_tool(
                tool_name,
                arguments=arguments or {}
            )

            return ToolCallResult(
                success=not result.isError if hasattr(result, 'isError') else True,
                content=result.content,
                error=None,
                server_name=server_name,
                is_error=result.isError if hasattr(result, 'isError') else False
            )

        except Exception as e:
            # Extract more detailed error information
            error_msg = str(e)

            # For ExceptionGroup/TaskGroup errors, try to extract the underlying exception
            if hasattr(e, '__cause__') and e.__cause__:
                error_msg = f"{error_msg} (caused by: {e.__cause__})"
            if hasattr(e, 'exceptions'):
                # ExceptionGroup - extract first exception and drill down to root cause
                def extract_deepest_error(ex):
                    """Recursively extract the deepest error message"""
                    if hasattr(ex, 'exceptions') and ex.exceptions:
                        # Nested ExceptionGroup - go deeper
                        return extract_deepest_error(ex.exceptions[0])
                    return str(ex)

                # Get the deepest error from the first exception
                deepest_error = extract_deepest_error(e.exceptions[0])

                # Check if it's a GitHub validation error and make it more readable
                if "Validation Failed" in deepest_error or "Validation Error" in deepest_error:
                    # Extract just the meaningful part
                    query_str = str(arguments.get("query", "")) if isinstance(arguments, dict) else ""
                    if "user:@" in query_str and "user:@me" not in query_str:
                        error_msg = (
                            f"❌ GitHub API Validation Error\n\n"
                            f"{deepest_error}\n\n"
                            f"💡 Tip: Use 'user:username' not 'user:@username'\n"
                            f"   - For authenticated user: user:@me\n"
                            f"   - For other users: user:ttware (no @ symbol)"
                        )
                    else:
                        error_msg = f"❌ GitHub API Validation Error\n\n{deepest_error}"
                else:
                    error_msg = deepest_error

            logger.error(f"Error calling tool '{tool_name}': {error_msg}", exc_info=True)

            return ToolCallResult(
                success=False,
                content=None,
                error=error_msg,
                server_name=server_name,
                is_error=True
            )

    async def _call_tool_with_temp_connection(
        self,
        server_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """
        Fallback: Call tool with temporary connection (v0.4.10).

        Used when persistent connection is not available.
        """
        server_config = self.config_loader.get_server(server_name)
        if not server_config:
            return ToolCallResult(
                success=False,
                content=None,
                error=f"Server '{server_name}' configuration not found",
                server_name=server_name,
                is_error=True
            )

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args,
                env=server_config.env or {}
            )

            # Temporary connection
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await session.call_tool(
                        tool_name,
                        arguments=arguments or {}
                    )

                    return ToolCallResult(
                        success=not result.isError if hasattr(result, 'isError') else True,
                        content=result.content,
                        error=None,
                        server_name=server_name,
                        is_error=result.isError if hasattr(result, 'isError') else False
                    )

        except Exception as e:
            logger.error(f"Temporary connection failed: {e}", exc_info=True)
            return ToolCallResult(
                success=False,
                content=None,
                error=str(e),
                server_name=server_name,
                is_error=True
            )

    async def shutdown(self):
        """
        Shutdown the client manager and properly cleanup persistent connections (v0.4.11 fix).

        This properly exits all context managers in the reverse order they were entered
        to avoid anyio "cancel scope in different task" errors.
        """
        logger.info("Shutting down MCP Client Manager")

        # Stop health monitoring FIRST (v0.4.10)
        if self.health_monitor:
            await self.health_monitor.stop_monitoring()
            self.health_monitor = None

        # Properly close all persistent connections (v0.4.11 fix)
        # We MUST exit context managers in reverse order: session → stdio
        for server_name, connection in list(self.connections.items()):
            try:
                connection.state = ConnectionState.DISCONNECTED

                # Exit session context manager first
                if connection._session_context and connection.session:
                    try:
                        await connection._session_context.__aexit__(None, None, None)
                    except Exception as e:
                        logger.debug(f"Error closing session for {server_name}: {e}")

                # Then exit stdio context manager
                if connection.stdio_context:
                    try:
                        await connection.stdio_context.__aexit__(None, None, None)
                    except Exception as e:
                        logger.debug(f"Error closing stdio for {server_name}: {e}")

                # Clear references
                connection.session = None
                connection._session_context = None
                connection.stdio_context = None

                logger.debug(f"Cleaned up {server_name}")

            except Exception as e:
                logger.warning(f"Error during cleanup of {server_name}: {e}")

        logger.info("MCP Client Manager shutdown complete")

    def is_connected(self) -> bool:
        """Check if any servers are connected"""
        return any(
            conn.state == ConnectionState.CONNECTED
            for conn in self.connections.values()
        )

    def has_configured_servers(self) -> bool:
        """
        Check if any MCP servers are configured (v0.4.11 lazy connection support).

        This is preferred over is_connected() for prerequisite checks since
        lazy connection means servers aren't connected until first use.

        Returns:
            True if at least one enabled server is configured
        """
        return any(
            config.enabled
            for config in self.config_loader.servers.values()
        )

    def get_connection_status(self) -> Dict[str, str]:
        """Get connection status for all servers"""
        return {
            name: conn.state.value
            for name, conn in self.connections.items()
        }

    @property
    def config(self) -> Dict[str, Any]:
        """
        Get MCP configuration for health monitor.

        Returns configuration compatible with health monitor expectations.
        """
        return {
            'mcpServers': {
                name: {
                    'enabled': config.enabled,
                    'command': config.command,
                    'args': config.args,
                }
                for name, config in self.config_loader.servers.items()
            }
        }

    async def _start_health_monitoring(self) -> None:
        """Start background health monitoring (v0.4.10)."""
        try:
            import os
            debug = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")

            if debug:
                print("🔍 DEBUG: Starting health monitoring...")

            from aii.data.integrations.mcp_health_monitor import MCPHealthMonitor

            self.health_monitor = MCPHealthMonitor(
                mcp_client=self,
                verbose=debug,
                check_interval=60.0,  # Check every 60 seconds
                health_check_timeout=5.0  # 5 second timeout
            )

            await self.health_monitor.start_monitoring()
            logger.info("Health monitoring started")

            if debug:
                print(f"✅ DEBUG: Health monitor started. Servers: {len(self.health_monitor._get_enabled_servers())}")

        except Exception as e:
            logger.error(f"Failed to start health monitoring: {e}")
            print(f"❌ DEBUG: Health monitoring failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail initialization if health monitoring fails
            self.health_monitor = None

    async def get_connection(self, server_name: str):
        """
        Get connection to server (for health monitoring).

        This is a simplified method for health monitoring compatibility.
        Returns the actual server connection if it exists.
        """
        if server_name not in self.config_loader.servers:
            raise ValueError(f"Server '{server_name}' not found in configuration")

        server_config = self.config_loader.servers[server_name]
        if not server_config.enabled:
            raise ValueError(f"Server '{server_name}' is disabled")

        # Reuse existing connection if available (v0.4.10: avoid duplicate connections)
        if server_name in self.connections:
            return self.connections[server_name]

        # Otherwise create temporary connection for health check
        return await self._create_connection(server_config)

    async def _create_connection(self, server_config: ServerConfig):
        """Create a simple connection object for health checking."""
        class SimpleConnection:
            def __init__(self, server_config):
                self.server_config = server_config

            async def list_tools(self):
                """Simple tool listing for health check."""
                # Create temporary stdio connection
                server_params = StdioServerParameters(
                    command=self.server_config.command,
                    args=self.server_config.args,
                    env=self.server_config.env
                )

                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.list_tools()
                        return result.tools

        return SimpleConnection(server_config)
