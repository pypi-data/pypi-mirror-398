# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Catalog Function - List popular pre-configured MCP servers."""


from typing import Any, Dict, List

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


class MCPCatalogFunction(FunctionPlugin):
    """List popular pre-configured MCP servers"""

    @property
    def name(self) -> str:
        return "mcp_catalog"

    @property
    def description(self) -> str:
        return (
            "List popular pre-configured MCP servers. Use when user wants to: "
            "'show mcp catalog', 'list popular mcp servers', 'what mcp servers available', "
            "'mcp server catalog', 'show available servers'. "
            "Examples: 'show popular mcp servers', 'what servers can I install'."
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
        """STANDARD mode: show catalog with details"""
        return OutputMode.STANDARD

    def _get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """
        Get MCP server catalog.

        Returns:
            Dictionary of server definitions
        """
        return {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "description": "GitHub integration (repos, issues, PRs)",
                "category": "Development",
                "env_required": ["GITHUB_TOKEN"],
            },
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "${PROJECT_PATH}"],
                "description": "Local filesystem access",
                "category": "Development",
                "env_required": ["PROJECT_PATH"],
            },
            "postgres": {
                "command": "uvx",
                "args": ["mcp-server-postgres", "--connection-string", "${POSTGRES_URL}"],
                "description": "PostgreSQL database integration",
                "category": "Database",
                "env_required": ["POSTGRES_URL"],
            },
            "chrome-devtools": {
                "command": "npx",
                "args": ["-y", "chrome-devtools-mcp@latest"],
                "description": "Chrome browser automation and DevTools",
                "category": "Automation",
                "env_required": [],
            },
            "puppeteer": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                "description": "Browser automation and web scraping",
                "category": "Automation",
                "env_required": [],
            },
            "slack": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-slack"],
                "description": "Slack workspace integration",
                "category": "Communication",
                "env_required": ["SLACK_BOT_TOKEN"],
            },
            "mongodb": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-mongodb"],
                "description": "MongoDB database integration",
                "category": "Database",
                "env_required": ["MONGODB_URL"],
            },
            "redis": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-redis"],
                "description": "Redis cache integration",
                "category": "Database",
                "env_required": ["REDIS_URL"],
            },
            "docker": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-docker"],
                "description": "Docker container management",
                "category": "DevOps",
                "env_required": [],
            },
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """List popular MCP servers from catalog"""
        catalog = self._get_catalog()

        # Load current config to mark installed servers
        config_manager = MCPConfigManager()
        config = config_manager.load_config()
        installed_servers = set(config.get("mcpServers", {}).keys())

        # Group by category
        by_category: Dict[str, List[tuple[str, Dict[str, Any]]]] = {}
        for server_name, server_info in catalog.items():
            category = server_info["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((server_name, server_info))

        # Build output
        output_lines = ["📦 Popular MCP Servers:", ""]

        for category, servers in sorted(by_category.items()):
            output_lines.append(f"{category}:")
            for server_name, server_info in sorted(servers):
                status = "✓" if server_name in installed_servers else "○"
                output_lines.append(f"  {status} {server_name:<18} - {server_info['description']}")
            output_lines.append("")

        output_lines.append("Legend:")
        output_lines.append("  ✓ = Already installed")
        output_lines.append("  ○ = Available to install")
        output_lines.append("")
        output_lines.append("Install: aii mcp install <server-name>")

        output = "\n".join(output_lines)

        return ExecutionResult(
            success=True,
            message=output,
            data={
                "catalog": catalog,
                "installed": list(installed_servers),
                "count": len(catalog),
                "clean_output": output,
            },
        )
