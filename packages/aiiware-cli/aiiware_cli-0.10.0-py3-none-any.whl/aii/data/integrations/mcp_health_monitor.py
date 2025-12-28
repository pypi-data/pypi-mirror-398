# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Health Monitor - Background server health monitoring with circuit breaker pattern.

This module provides automatic health monitoring for MCP servers with:
- Background health checks every 60 seconds
- Circuit breaker pattern (3 failures → auto-disable)
- Retry logic with exponential backoff
- Response time categorization (HEALTHY/DEGRADED/UNHEALTHY)
- Auto-reconnect on transient failures

Part of v0.4.10: MCP Reliability & Intelligence
"""


import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Server health states."""

    HEALTHY = "healthy"      # All checks passing, response time < 2s
    DEGRADED = "degraded"    # Slow but working, response time 2-5s
    UNHEALTHY = "unhealthy"  # Failing health checks
    DISABLED = "disabled"    # Auto-disabled after failures


@dataclass
class ServerHealth:
    """Health status for single MCP server."""

    server_name: str
    status: HealthStatus
    last_check: datetime
    failure_count: int
    last_error: Optional[str] = None
    response_time_ms: Optional[float] = None
    uptime_percentage: Optional[float] = None


class MCPHealthMonitor:
    """
    Monitors MCP server health with circuit breaker pattern.

    Features:
    - Background health checks every 60 seconds
    - Circuit breaker: 3 consecutive failures → auto-disable
    - Auto-reconnect with exponential backoff
    - Health status reporting
    - Retry logic for transient failures

    Example:
        monitor = MCPHealthMonitor(mcp_client, verbose=True)
        await monitor.start_monitoring()

        # Check health
        health = await monitor.get_server_health("github")
        if health.status == HealthStatus.HEALTHY:
            print("Server is healthy!")

        # Get all server health
        report = await monitor.get_health_report()

        await monitor.stop_monitoring()
    """

    def __init__(
        self,
        mcp_client: Any,  # MCPClientManager
        verbose: bool = False,
        check_interval: float = 60.0,
        health_check_timeout: float = 5.0
    ):
        """
        Initialize health monitor.

        Args:
            mcp_client: MCP client manager instance
            verbose: Enable verbose logging
            check_interval: Seconds between health checks (default: 60)
            health_check_timeout: Timeout for health checks in seconds (default: 5)
        """
        self.client = mcp_client
        self.verbose = verbose
        self.check_interval = check_interval
        self.health_check_timeout = health_check_timeout

        self.health_status: Dict[str, ServerHealth] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False

    async def start_monitoring(self) -> None:
        """Start background health monitoring task."""
        if self.running:
            logger.warning("Health monitoring already running")
            return

        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        if self.verbose:
            logger.info("🔍 Health monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop background monitoring gracefully."""
        if not self.running:
            return

        self.running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                # Wait for task to complete with timeout
                await asyncio.wait_for(self.monitoring_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                # Expected - task was cancelled or took too long
                pass
            except Exception as e:
                logger.warning(f"Error stopping health monitoring: {e}")

            self.monitoring_task = None

        if self.verbose:
            logger.info("Health monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Background loop checking server health every check_interval seconds."""
        while self.running:
            try:
                # Get all enabled servers
                servers = self._get_enabled_servers()

                # Check each server's health
                for server_name in servers:
                    # Check if still running (may have been stopped during loop)
                    if not self.running:
                        break

                    try:
                        await self._check_server(server_name)
                    except asyncio.CancelledError:
                        # Monitoring stopped - exit gracefully
                        break
                    except Exception as e:
                        logger.warning(f"Health check failed for {server_name}: {e}")

                # Wait before next check (with early exit if stopped)
                if self.running:
                    try:
                        await asyncio.sleep(self.check_interval)
                    except asyncio.CancelledError:
                        break

            except asyncio.CancelledError:
                # Monitoring stopped - exit cleanly
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                if self.running:
                    try:
                        await asyncio.sleep(self.check_interval)
                    except asyncio.CancelledError:
                        break

    def _get_enabled_servers(self) -> list[str]:
        """Get list of enabled MCP servers from client."""
        try:
            # Get servers from MCP client config
            if hasattr(self.client, 'config') and self.client.config:
                servers = self.client.config.get('mcpServers', {})
                return [
                    name for name, config in servers.items()
                    if config.get('enabled', True)
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting enabled servers: {e}")
            return []

    async def _check_server(self, server_name: str) -> ServerHealth:
        """
        Check health of single server.

        Process:
        1. Try to connect (with timeout)
        2. Call list_tools (simple health check)
        3. Measure response time
        4. Update health status
        5. Handle failures (circuit breaker)

        Args:
            server_name: Name of server to check

        Returns:
            ServerHealth object with current status
        """
        start_time = time.time()

        try:
            # Check if monitoring is still running (may have been stopped)
            if not self.running:
                raise asyncio.CancelledError("Health monitoring stopped")

            # Get server config
            if server_name not in self.client.config_loader.servers:
                raise ValueError(f"Server '{server_name}' not found")

            server_config = self.client.config_loader.servers[server_name]

            # Import MCP client dependencies
            from mcp import StdioServerParameters
            from mcp.client.stdio import stdio_client
            from mcp import ClientSession

            # Create temporary connection for health check
            server_params = StdioServerParameters(
                command=server_config.command,
                args=server_config.args,
                env=server_config.env or {}
            )

            # Simple health check: list tools with temporary session
            # Wrap in shield to allow graceful cleanup even if cancelled
            try:
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await asyncio.wait_for(
                            session.initialize(),
                            timeout=self.health_check_timeout
                        )
                        tools_response = await asyncio.wait_for(
                            session.list_tools(),
                            timeout=self.health_check_timeout
                        )
                        tools = tools_response.tools
            except asyncio.CancelledError:
                # Gracefully handle cancellation during connection
                raise

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Determine health status based on response time
            if response_time < 2000:
                status = HealthStatus.HEALTHY
            elif response_time < 5000:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            # Update health record (success resets failure count)
            health = ServerHealth(
                server_name=server_name,
                status=status,
                last_check=datetime.now(),
                failure_count=0,  # Reset on success
                response_time_ms=response_time
            )

            self.health_status[server_name] = health

            if self.verbose and status == HealthStatus.DEGRADED:
                logger.warning(f"⚠️ {server_name}: Slow response ({response_time:.0f}ms)")

            return health

        except asyncio.CancelledError:
            # Health monitoring was stopped - don't treat as failure
            if self.verbose:
                logger.debug(f"Health check for {server_name} cancelled")
            # Return current status or create a placeholder
            return self.health_status.get(server_name) or ServerHealth(
                server_name=server_name,
                status=HealthStatus.UNHEALTHY,
                last_check=datetime.now(),
                failure_count=0,
                last_error="Health check cancelled"
            )

        except asyncio.TimeoutError:
            # Health check timed out
            return await self._handle_failure(
                server_name,
                f"Health check timeout after {self.health_check_timeout}s"
            )

        except Exception as e:
            # Health check failed
            return await self._handle_failure(
                server_name,
                str(e)
            )

    async def _handle_failure(
        self,
        server_name: str,
        error: str
    ) -> ServerHealth:
        """
        Handle health check failure with circuit breaker logic.

        Circuit Breaker Pattern:
        - 1st failure: Log warning, retry next check
        - 2nd failure: Log warning, retry next check
        - 3rd failure: Auto-disable server, alert user

        Args:
            server_name: Name of server that failed
            error: Error message

        Returns:
            ServerHealth object with UNHEALTHY or DISABLED status
        """
        # Get current health or create new record
        current = self.health_status.get(server_name)

        if current:
            failure_count = current.failure_count + 1
        else:
            failure_count = 1

        # Create failure health record
        health = ServerHealth(
            server_name=server_name,
            status=HealthStatus.UNHEALTHY if failure_count < 3 else HealthStatus.DISABLED,
            last_check=datetime.now(),
            failure_count=failure_count,
            last_error=error,
            response_time_ms=None
        )

        self.health_status[server_name] = health

        # Circuit breaker: 3 failures → auto-disable
        if failure_count >= 3:
            if self.verbose:
                logger.error(f"🔴 {server_name}: Auto-disabled after 3 failures")
                logger.error(f"   Last error: {error}")
                logger.info(f"   Run 'aii mcp enable {server_name}' to retry")

            # Disable server in config
            await self._disable_server(server_name)

        elif self.verbose:
            logger.warning(f"⚠️ {server_name}: Health check failed ({failure_count}/3)")
            logger.warning(f"   Error: {error}")

        return health

    async def _disable_server(self, server_name: str) -> None:
        """Disable server in configuration."""
        try:
            # Update server config to disabled
            if hasattr(self.client, 'config') and self.client.config:
                servers = self.client.config.get('mcpServers', {})
                if server_name in servers:
                    servers[server_name]['enabled'] = False
                    # Save config changes
                    # Note: Actual config saving depends on MCPClientManager implementation
        except Exception as e:
            logger.error(f"Error disabling server {server_name}: {e}")

    async def get_health_report(self) -> Dict[str, ServerHealth]:
        """
        Get current health status for all servers.

        Returns:
            Dictionary mapping server names to ServerHealth objects
        """
        return self.health_status.copy()

    async def get_server_health(self, server_name: str) -> Optional[ServerHealth]:
        """
        Get health status for specific server.

        Args:
            server_name: Name of server to check

        Returns:
            ServerHealth object or None if not monitored
        """
        return self.health_status.get(server_name)

    # ========== Retry Logic with Exponential Backoff ==========

    async def execute_with_retry(
        self,
        operation: Callable,
        server_name: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """
        Execute MCP operation with automatic retry and exponential backoff.

        Retry Strategy:
        - 1st attempt: Immediate
        - 2nd attempt: Wait base_delay (1s)
        - 3rd attempt: Wait base_delay * 2 (2s)
        - 4th attempt: Wait base_delay * 4 (4s)

        Args:
            operation: Async callable to execute
            server_name: Name of server for health tracking
            max_retries: Maximum retry attempts (default: 3)
            base_delay: Base delay for exponential backoff (default: 1.0s)

        Returns:
            Result from operation

        Raises:
            Last exception if all retries fail

        Example:
            async def query_github():
                return await mcp_client.call_tool("github", "search_repos", {...})

            result = await monitor.execute_with_retry(
                query_github,
                "github",
                max_retries=3
            )
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                # Attempt operation
                result = await operation()

                # Success - reset failure count
                if server_name in self.health_status:
                    self.health_status[server_name].failure_count = 0

                return result

            except Exception as e:
                last_exception = e

                # Determine if error is retryable
                if not self._is_retryable_error(e):
                    # Don't retry non-transient errors
                    raise

                # Last attempt - give up
                if attempt == max_retries:
                    await self._handle_failure(server_name, str(e))
                    raise

                # Calculate backoff delay
                delay = base_delay * (2 ** attempt)  # Exponential: 1s, 2s, 4s

                if self.verbose:
                    logger.warning(f"⚠️ {server_name}: Retry {attempt + 1}/{max_retries} after {delay}s")
                    logger.warning(f"   Error: {str(e)}")

                # Wait before retry
                await asyncio.sleep(delay)

        # Should never reach here, but raise last exception just in case
        if last_exception:
            raise last_exception

        raise RuntimeError("execute_with_retry: Unexpected state")

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if error is worth retrying.

        Retryable:
        - Network timeouts
        - Connection refused (server restarting)
        - Rate limit errors
        - Temporary server errors (5xx)

        Non-retryable:
        - Authentication failures (401, 403)
        - Not found (404)
        - Invalid parameters (400)
        - Server not installed

        Args:
            error: Exception to check

        Returns:
            True if error is retryable, False otherwise
        """
        error_msg = str(error).lower()

        # Retryable patterns
        retryable_patterns = [
            "timeout",
            "connection refused",
            "connection reset",
            "connection error",
            "rate limit",
            "too many requests",
            "server error",
            "temporarily unavailable",
            "503",
            "502",
            "504",
            "network",
        ]

        for pattern in retryable_patterns:
            if pattern in error_msg:
                return True

        # Non-retryable patterns
        non_retryable_patterns = [
            "authentication",
            "unauthorized",
            "forbidden",
            "not found",
            "invalid parameter",
            "server not installed",
            "401",
            "403",
            "404",
            "400",
        ]

        for pattern in non_retryable_patterns:
            if pattern in error_msg:
                return False

        # Default: retry unknown errors (conservative approach)
        return True
