# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Install Function - Install MCP server from catalog."""


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
from .mcp_add import MCPAddFunction
from .mcp_catalog import MCPCatalogFunction


class MCPInstallFunction(FunctionPlugin):
    """Install MCP server from catalog"""

    def __init__(self, config_manager: Optional[MCPConfigManager] = None):
        self.config_manager = config_manager or MCPConfigManager()

    @property
    def name(self) -> str:
        return "mcp_install"

    @property
    def description(self) -> str:
        return (
            "Install MCP server from catalog. Use when user wants to: "
            "'install mcp server', 'install from catalog', 'install github/chrome/postgres server'. "
            "Examples: 'install github server', 'install chrome mcp server from catalog'."
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
                description="Name of the server from catalog (e.g., 'github', 'chrome-devtools')",
            ),
            "env_vars": ParameterSchema(
                name="env_vars",
                type="object",
                required=False,
                description="Environment variables as dict (e.g., {'GITHUB_TOKEN': 'your-token'})",
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

    def _get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Get catalog (reuse from MCPCatalogFunction)"""
        catalog_func = MCPCatalogFunction()
        return catalog_func._get_catalog()

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Install MCP server from catalog"""
        server_name = parameters["server_name"]
        env_vars = parameters.get("env_vars", {})

        # Get catalog
        catalog = self._get_catalog()

        # Check if server exists in catalog
        if server_name not in catalog:
            available = ", ".join(sorted(catalog.keys()))
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' not found in catalog.\n\nAvailable: {available}",
                data={
                    "clean_output": f"❌ Server '{server_name}' not found in catalog.\n\nTry: aii mcp catalog"
                },
            )

        server_info = catalog[server_name]

        # Check if already installed
        config = self.config_manager.load_config()
        servers = config.get("mcpServers", {})

        if server_name in servers:
            return ExecutionResult(
                success=False,
                message=f"Server '{server_name}' is already installed",
                data={"clean_output": f"✓ Server '{server_name}' is already installed"},
            )

        # Check for required environment variables
        import os
        env_required = server_info.get("env_required", [])
        missing_env = []
        for env_var in env_required:
            # Check if provided in parameters, or set in environment, or placeholder in args
            if (env_var not in env_vars and
                env_var not in os.environ and
                f"${{{env_var}}}" not in str(server_info.get("args", []))):
                missing_env.append(env_var)
            elif env_var in os.environ and env_var not in env_vars:
                # Collect environment variable from system environment
                env_vars[env_var] = os.environ[env_var]

        if missing_env:
            output_lines = [
                f"📦 Installing '{server_name}' from catalog...",
                f"⚠️  Requires environment variables: {', '.join(missing_env)}",
                "",
                "Please provide them when installing:",
                f"  aii mcp add {server_name} {server_info['command']} {' '.join(server_info['args'])}",
                "",
                "Or set them in your environment:",
            ]
            for env_var in missing_env:
                output_lines.append(f"  export {env_var}='your-value-here'")

            output = "\n".join(output_lines)

            return ExecutionResult(
                success=False,
                message=output,
                data={"clean_output": output, "missing_env": missing_env},
            )

        # Install server (delegate to MCPAddFunction)
        add_function = MCPAddFunction(self.config_manager)

        return await add_function.execute(
            {
                "server_name": server_name,
                "command": server_info["command"],
                "args": server_info["args"],
                "env": env_vars,
                "enabled": True,
                "transport": "stdio",
            },
            context,
        )
