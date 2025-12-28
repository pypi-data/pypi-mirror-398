# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Status Function - Show MCP server health status."""


from typing import Any, Dict, Optional

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
)
from .config_manager import MCPConfigManager


class MCPStatusFunction(FunctionPlugin):
    """
    Show MCP server health status.

    Examples:
    - aii mcp status
    - aii mcp status github
    - aii mcp status --all
    """

    function_name = "mcp_status"
    function_description = "Show health status for MCP servers"
    function_category = FunctionCategory.SYSTEM

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        """Initialize with optional config manager."""
        self.config_manager = config_manager or MCPConfigManager()

    def get_parameters_schema(self) -> ParameterSchema:
        """Return JSON schema for function parameters."""
        return {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "Specific server to check (optional, shows all if omitted)",
                },
                "show_all": {
                    "type": "boolean",
                    "description": "Show all servers including disabled",
                    "default": False,
                },
            },
            "required": [],
        }

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode for this function."""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """List of supported output modes."""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    def get_function_safety(self) -> FunctionSafety:
        """Return safety level for this function."""
        return FunctionSafety.SAFE

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute MCP status command.

        Args:
            parameters: Command parameters (server_name, show_all)
            context: Execution context with health monitor

        Returns:
            ExecutionResult with health status information
        """
        server_name = parameters.get("server_name")
        show_all = parameters.get("show_all", False)

        # Get health monitor from context
        if not hasattr(context, 'mcp_client') or not context.mcp_client:
            return ExecutionResult(
                success=False,
                message="MCP client not available",
                data={"clean_output": "❌ MCP client not available"},
            )

        if not hasattr(context.mcp_client, 'health_monitor') or not context.mcp_client.health_monitor:
            return ExecutionResult(
                success=False,
                message="Health monitoring not enabled",
                data={"clean_output": "⚠️ Health monitoring not enabled"},
            )

        health_monitor = context.mcp_client.health_monitor

        if server_name:
            # Show detailed health for specific server
            health = await health_monitor.get_server_health(server_name)

            if not health:
                return ExecutionResult(
                    success=False,
                    message=f"Server '{server_name}' not found or not monitored",
                    data={
                        "clean_output": f"❌ Server '{server_name}' not found or not monitored"
                    },
                )

            output = self._format_detailed_health(server_name, health)

        else:
            # Show summary for all servers
            all_health = await health_monitor.get_health_report()

            # Filter if not showing all
            if not show_all:
                from ...data.integrations.mcp_health_monitor import HealthStatus

                all_health = {
                    name: h
                    for name, h in all_health.items()
                    if h.status != HealthStatus.DISABLED
                }

            output = self._format_health_summary(all_health)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "health_status": all_health if not server_name else {server_name: health},
                "clean_output": output,
            },
        )

    def _format_health_summary(self, health: Dict[str, Any]) -> str:
        """Format health summary for all servers."""
        from ...data.integrations.mcp_health_monitor import HealthStatus

        if not health:
            return "📊 No MCP servers monitored yet"

        output = ["📊 MCP Server Health Status:\n"]

        # Group by status
        healthy = []
        degraded = []
        unhealthy = []
        disabled = []

        for name, h in health.items():
            if h.status == HealthStatus.HEALTHY:
                healthy.append((name, h))
            elif h.status == HealthStatus.DEGRADED:
                degraded.append((name, h))
            elif h.status == HealthStatus.UNHEALTHY:
                unhealthy.append((name, h))
            else:
                disabled.append((name, h))

        # Show healthy servers
        if healthy:
            output.append("✓ Healthy:")
            for name, h in healthy:
                output.append(f"  {name} ({h.response_time_ms:.0f}ms)")

        # Show degraded servers
        if degraded:
            output.append("\n⚠️ Degraded:")
            for name, h in degraded:
                output.append(f"  {name} ({h.response_time_ms:.0f}ms - slow)")

        # Show unhealthy servers
        if unhealthy:
            output.append("\n✗ Unhealthy:")
            for name, h in unhealthy:
                failures = f"{h.failure_count}/3"
                output.append(f"  {name} ({failures} failures)")
                if h.last_error:
                    output.append(f"    Error: {h.last_error}")

        # Show disabled servers
        if disabled:
            output.append("\n○ Disabled:")
            for name, h in disabled:
                output.append(f"  {name} (auto-disabled after failures)")
                output.append(f"    Run 'aii mcp enable {name}' to retry")

        return "\n".join(output)

    def _format_detailed_health(self, name: str, health: Any) -> str:
        """Format detailed health for single server."""
        from ...data.integrations.mcp_health_monitor import HealthStatus

        status_icon = {
            HealthStatus.HEALTHY: "✓",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "✗",
            HealthStatus.DISABLED: "○",
        }

        output = [f"📊 {name} Server Health:"]
        output.append(
            f"\nStatus: {status_icon[health.status]} {health.status.value}"
        )
        output.append(f"Last check: {self._format_time_ago(health.last_check)}")

        if health.response_time_ms:
            output.append(f"Response time: {health.response_time_ms:.0f}ms")

        if health.failure_count > 0:
            output.append(f"\nFailures: {health.failure_count}/3")

        if health.last_error:
            output.append(f"Last error: {health.last_error}")

        if health.status == HealthStatus.DISABLED:
            output.append(f"\n💡 Tip: Run 'aii mcp enable {name}' to retry connection")

        return "\n".join(output)

    def _format_time_ago(self, dt: Any) -> str:
        """Format datetime as 'X seconds/minutes ago'."""
        from datetime import datetime

        now = datetime.now()
        delta = now - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return f"{int(seconds)} seconds ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes ago"
        else:
            return f"{int(seconds / 3600)} hours ago"
