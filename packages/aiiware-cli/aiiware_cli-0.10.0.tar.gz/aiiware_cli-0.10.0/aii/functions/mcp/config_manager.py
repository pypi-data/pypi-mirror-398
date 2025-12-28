# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Server Configuration Manager

Shared utility for MCP function plugins.
"""


import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MCPConfigManager:
    """
    Manages MCP server configuration file operations.

    Follows SRP: Single responsibility for config file I/O.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config manager.

        Args:
            config_path: Override config file path (default: ~/.aii/mcp_servers.json)
        """
        self.config_path = config_path or (Path.home() / ".aii" / "mcp_servers.json")
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict[str, Any]:
        """
        Load MCP server configuration.

        Returns:
            Configuration dictionary with 'mcpServers' key
        """
        if not self.config_path.exists():
            return {"mcpServers": {}}

        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)
            return config if isinstance(config, dict) else {"mcpServers": {}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {"mcpServers": {}}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"mcpServers": {}}

    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save MCP server configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            self._ensure_config_dir()
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def backup_config(self) -> bool:
        """
        Create backup of current configuration.

        Returns:
            True if backup created successfully
        """
        if not self.config_path.exists():
            return True

        try:
            backup_path = self.config_path.with_suffix(".json.backup")
            import shutil

            shutil.copy2(self.config_path, backup_path)
            logger.info(f"Config backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup config: {e}")
            return False

    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server."""
        config = self.load_config()
        return config.get("mcpServers", {}).get(server_name)

    def server_exists(self, server_name: str) -> bool:
        """Check if server exists in configuration."""
        return self.get_server(server_name) is not None

    def list_servers(self) -> Dict[str, Any]:
        """List all configured servers."""
        config = self.load_config()
        return config.get("mcpServers", {})
