# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Remove Function - Remove MCP server from configuration."""


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


class MCPRemoveFunction(FunctionPlugin):
    """Remove MCP server from configuration"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_remove"

    @property
    def description(self) -> str:
        return (
            "Remove MCP server from configuration. Use when user wants to: "
            "'remove mcp server', 'delete mcp server', 'uninstall mcp server', "
            "'remove chrome/github/postgres server'. "
            "Examples: 'remove chrome server', 'delete github mcp server'."
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
                description="Name of the server to remove",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        """Potentially destructive: confirm before removing"""
        return True

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Remove MCP server from configuration"""
        server_name = parameters["server_name"]

        # Load config
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        # Check if server exists
        if server_name not in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found",
                data={"clean_output": f"❌ Server '{server_name}' not found"},
            )

        # Backup before removing
        self.config_manager.backup_config()

        # Remove server
        del servers[server_name]
        config["mcpServers"] = servers

        # Save config
        if not self.config_manager.save_config(config):
            return ExecutionResult(
                success=False,
                message="Failed to save configuration",
                data={"clean_output": "❌ Failed to save configuration"},
            )

        output = f"✓ Removed '{server_name}' server"

        return ExecutionResult(
            success=True,
            message=output,
            data={"server_name": server_name, "clean_output": output},
        )
