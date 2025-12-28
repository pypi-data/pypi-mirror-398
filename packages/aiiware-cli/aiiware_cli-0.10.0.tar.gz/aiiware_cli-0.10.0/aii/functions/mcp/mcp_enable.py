# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Enable Function - Enable a disabled MCP server."""


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


class MCPEnableFunction(FunctionPlugin):
    """Enable a disabled MCP server"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_enable"

    @property
    def description(self) -> str:
        return (
            "Enable a disabled MCP server. Use when user wants to: "
            "'enable mcp server', 'activate mcp server', 'turn on mcp server'. "
            "Examples: 'enable chrome server', 'activate github mcp server'."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "server_name": ParameterSchema(
                name="server_name",
                type="string",
                required=True,
                description="Name of the server to enable",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Enable MCP server"""
        server_name = parameters["server_name"]

        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if server_name not in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found",
                data={"clean_output": f"❌ Server '{server_name}' not found"},
            )

        # v0.6.0: Set enabled=true in config
        servers[server_name]["enabled"] = True
        config["mcpServers"] = servers
        self.config_manager.save_config(config)

        output = f"✓ Server '{server_name}' enabled (will initialize on next startup)"

        return ExecutionResult(
            success=True,
            message=output,
            data={"server_name": server_name, "clean_output": output},
        )
