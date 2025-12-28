# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Add Function - Add MCP server to configuration."""


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


class MCPAddFunction(FunctionPlugin):
    """
    Add MCP server to configuration.

    Examples:
    - aii mcp add chrome npx chrome-devtools-mcp@latest
    - aii mcp add postgres uvx mcp-server-postgres --connection-string $DB_URL
    - aii mcp add github npx @modelcontextprotocol/server-github
    """

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        """
        Initialize function.

        Args:
            config_manager: Config manager instance (DIP: dependency injection)
        """
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_add"

    @property
    def description(self) -> str:
        return (
            "Add MCP server to configuration. Use when user wants to: "
            "'add mcp server', 'install mcp server', 'configure mcp server', "
            "'add chrome/github/postgres server', 'setup mcp'. "
            "Examples: 'add chrome mcp server', 'install github server', "
            "'configure postgres mcp server with connection string'."
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
                description="Short name for the server (e.g., 'chrome', 'postgres', 'github')",
            ),
            "command": ParameterSchema(
                name="command",
                type="string",
                required=True,
                description="Command to run (e.g., 'npx', 'uvx', 'node')",
            ),
            "args": ParameterSchema(
                name="args",
                type="array",
                required=True,
                description="Command arguments as list (e.g., ['chrome-devtools-mcp@latest'])",
            ),
            "env": ParameterSchema(
                name="env",
                type="object",
                required=False,
                description="Environment variables as dict (e.g., {'API_KEY': '${GITHUB_TOKEN}'})",
            ),
            "enabled": ParameterSchema(
                name="enabled",
                type="boolean",
                required=False,
                description="Enable server immediately (default: true)",
            ),
            "transport": ParameterSchema(
                name="transport",
                type="string",
                required=False,
                description="Transport protocol: 'stdio', 'sse', or 'http' (default: 'stdio')",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        """Safe operation: just modifies config file"""
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """CLEAN mode: users want just the confirmation"""
        return OutputMode.CLEAN

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """
        Add MCP server to configuration.

        Args:
            parameters: Function parameters
            context: Execution context

        Returns:
            ExecutionResult with success status
        """
        server_name = parameters["server_name"]
        command = parameters["command"]
        args = parameters["args"]
        env = parameters.get("env", {})
        enabled = parameters.get("enabled", True)
        transport = parameters.get("transport", "stdio")

        # Validate transport
        if transport not in ["stdio", "sse", "http"]:
            return ExecutionResult(
                success=False,
                message=f"Invalid transport '{transport}'. Must be: stdio, sse, or http",
                data={"clean_output": f"❌ Invalid transport '{transport}'"},
            )

        # Load existing config
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        # Check if server already exists
        if server_name in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' already exists. Use 'aii mcp remove {server_name}' first.",
                data={
                    "clean_output": f"❌ Server '{server_name}' already exists.\n\nUse: aii mcp remove {server_name}"
                },
            )

        # Build server config
        server_config = {
            "command": command,
            "args": args if isinstance(args, list) else [args],
        }

        if env:
            server_config["env"] = env

        # Add server to config
        servers[server_name] = server_config
        config["mcpServers"] = servers

        # Backup before saving
        self.config_manager.backup_config()

        # Save config
        if not self.config_manager.save_config(config):
            return ExecutionResult(
                success=False,
                message="Failed to save configuration",
                data={"clean_output": "❌ Failed to save configuration"},
            )

        # Build output message
        output_lines = [
            f"✓ Added '{server_name}' server",
            f"✓ Configuration saved to {self.config_manager.config_path}",
            f"✓ Transport: {transport}",
        ]

        if env:
            output_lines.append(f"✓ Environment variables: {', '.join(env.keys())}")

        output_lines.append("")
        output_lines.append(
            f"Try it: aii \"use {server_name} mcp server to [your task]\""
        )

        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "server_name": server_name,
                "config": server_config,
                "config_path": str(self.config_manager.config_path),
                "clean_output": output,
            },
        )
