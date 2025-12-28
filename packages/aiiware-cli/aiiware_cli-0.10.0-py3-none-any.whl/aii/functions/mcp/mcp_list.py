# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP List Function - List all configured MCP servers."""


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


class MCPListFunction(FunctionPlugin):
    """List all configured MCP servers"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_list"

    @property
    def description(self) -> str:
        return (
            "List all configured MCP servers. Use when user wants to: "
            "'list mcp servers', 'show mcp servers', 'what mcp servers', "
            "'mcp server list', 'show configured servers'. "
            "Examples: 'list my mcp servers', 'show all mcp servers'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """STANDARD mode: show list with metadata"""
        return OutputMode.STANDARD

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """List all configured MCP servers"""
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if not servers:
            output = "No MCP servers configured.\n\nTry: aii mcp catalog"
            return ExecutionResult(
                success=True,
                message=output,
                data={"servers": {}, "count": 0, "clean_output": output},
            )

        # Build output
        output_lines = ["📦 Configured MCP Servers:", ""]

        for server_name, server_config in servers.items():
            command = server_config.get("command", "")
            args = server_config.get("args", [])
            args_str = " ".join(args) if isinstance(args, list) else str(args)
            enabled = server_config.get("enabled", True)  # v0.6.0: Default to enabled

            # Show enabled/disabled status
            status_icon = "✓" if enabled else "✗"
            status_text = "" if enabled else " (disabled)"
            output_lines.append(f"{status_icon} {server_name}{status_text}")
            output_lines.append(f"  Command: {command} {args_str}")

            if "env" in server_config:
                env_vars = ", ".join(server_config["env"].keys())
                output_lines.append(f"  Environment: {env_vars}")

            output_lines.append("")

        output_lines.append(f"Total: {len(servers)} server(s)")
        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "servers": servers,
                "count": len(servers),
                "clean_output": output,
            },
        )
