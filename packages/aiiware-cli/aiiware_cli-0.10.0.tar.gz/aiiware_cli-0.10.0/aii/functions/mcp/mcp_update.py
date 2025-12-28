# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Update Function - Update MCP server to latest version."""


import logging
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

logger = logging.getLogger(__name__)


class MCPUpdateFunction(FunctionPlugin):
    """
    Update MCP server to latest version (v0.4.10).

    Checks npm registry for latest version, shows changelog, and safely updates.
    """

    @property
    def name(self) -> str:
        return "mcp_update"

    @property
    def description(self) -> str:
        return "Update MCP server to the latest version from npm registry"

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
                description="Name of the MCP server to update",
            ),
            "auto_confirm": ParameterSchema(
                name="auto_confirm",
                type="boolean",
                required=False,
                description="Skip confirmation prompt",
                default=False,
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Updates require confirmation

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY  # Modifying installed packages

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Check for updates and update MCP server"""
        server_name = parameters.get("server_name")
        auto_confirm = parameters.get("auto_confirm", False)

        if not server_name:
            return ExecutionResult(
                success=False,
                message="❌ Server name is required",
                data={"clean_output": "Server name required"},
            )

        try:
            # Load server configuration
            from ...data.integrations.mcp.config_loader import MCPConfigLoader

            config_loader = MCPConfigLoader()
            config_loader.load_configurations()

            server_config = config_loader.get_server(server_name)
            if not server_config:
                return ExecutionResult(
                    success=False,
                    message=f"❌ Server '{server_name}' not found",
                    data={"clean_output": f"Server '{server_name}' not found"},
                )

            # Get current version
            current_version = await self._get_current_version(server_config)

            # Fetch latest version from npm
            latest_info = await self._fetch_latest_version(server_config)

            if not latest_info:
                return ExecutionResult(
                    success=False,
                    message=f"❌ Could not fetch latest version for '{server_name}'",
                    data={"clean_output": "Could not fetch latest version"},
                )

            latest_version = latest_info.get("version")

            # Compare versions
            if current_version == latest_version:
                message = f"✅ {server_name} is already up to date (v{current_version})"
                return ExecutionResult(
                    success=True,
                    message=message,
                    data={
                        "clean_output": message,
                        "current_version": current_version,
                        "latest_version": latest_version,
                        "up_to_date": True,
                    },
                )

            # Show update information
            changelog = latest_info.get("changelog", "No changelog available")
            message_lines = [
                f"📦 Update available for {server_name}:",
                f"   Current: v{current_version}",
                f"   Latest:  v{latest_version}",
                "",
                "📋 What's new:",
                changelog,
            ]

            if not auto_confirm:
                message_lines.append("")
                message_lines.append("Update? (requires confirmation)")

            message = "\n".join(message_lines)

            # If auto_confirm, proceed with update
            if auto_confirm:
                update_result = await self._perform_update(server_config, latest_version)
                if update_result["success"]:
                    return ExecutionResult(
                        success=True,
                        message=f"✅ {server_name} updated to v{latest_version}",
                        data={
                            "clean_output": f"Updated to v{latest_version}",
                            "old_version": current_version,
                            "new_version": latest_version,
                        },
                    )
                else:
                    return ExecutionResult(
                        success=False,
                        message=f"❌ Update failed: {update_result['error']}",
                        data={"clean_output": f"Update failed: {update_result['error']}"},
                    )

            # Return update info for confirmation
            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "clean_output": f"Update available: v{current_version} → v{latest_version}",
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "changelog": changelog,
                    "requires_confirmation": True,
                },
            )

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return ExecutionResult(
                success=False,
                message=f"❌ Error checking for updates: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"},
            )

    async def _get_current_version(self, server_config) -> str:
        """Get currently installed version of the server"""
        package_name = self._extract_package_name(server_config)
        if not package_name:
            return "unknown"

        # Try to get version from npm list
        import subprocess

        try:
            result = subprocess.run(
                ["npm", "list", "-g", package_name, "--json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                if package_name in dependencies:
                    return dependencies[package_name].get("version", "unknown")

            return "unknown"
        except Exception:
            return "unknown"

    def _extract_package_name(self, server_config) -> str:
        """Extract npm package name from server command"""
        # Build full command from command + args
        full_command_parts = [server_config.command] + server_config.args

        # Handle different command formats
        if "npx" in full_command_parts:
            # npx -y @modelcontextprotocol/server-github
            # npx chrome-devtools-mcp@latest
            # Find the package name after npx (skip flags like -y)
            for part in full_command_parts[1:]:
                if not part.startswith("-"):  # Skip flags
                    # Handle versioned packages: package@version -> package
                    if "@" in part and not part.startswith("@"):
                        # Not a scoped package, has version: chrome-devtools-mcp@latest
                        package_name = part.split("@")[0]
                    else:
                        # Scoped package or no version: @modelcontextprotocol/server-github
                        package_name = part
                    return package_name
            return ""
        else:
            return server_config.command

    async def _fetch_latest_version(self, server_config) -> Optional[dict]:
        """Fetch latest version from npm registry"""
        import subprocess

        package_name = self._extract_package_name(server_config)
        if not package_name:
            return None

        try:
            # Get package info from npm
            result = subprocess.run(
                ["npm", "view", package_name, "--json"],
                capture_output=True,
                text=True,
                timeout=15,
            )

            if result.returncode == 0:
                import json

                data = json.loads(result.stdout)
                version = data.get("version", "unknown")
                description = data.get("description", "")

                return {
                    "version": version,
                    "changelog": description or "No changelog available",
                    "package_name": package_name,
                }

            return None
        except Exception as e:
            logger.error(f"Error fetching npm package info: {e}")
            return None

    async def _perform_update(
        self, server_config, new_version: str
    ) -> dict[str, Any]:
        """Perform the actual update"""
        import subprocess

        package_name = self._extract_package_name(server_config)
        if not package_name:
            return {"success": False, "error": "Could not determine package name"}

        try:
            # Reinstall with latest version
            result = subprocess.run(
                ["npm", "install", "-g", f"{package_name}@{new_version}"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                return {"success": True, "version": new_version}
            else:
                return {"success": False, "error": result.stderr or "Update failed"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Update timed out (>60s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}
