# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Configuration Loader

Loads MCP server configurations with the following priority:
1. User config: ~/.aii/mcp_servers.json
2. Claude Desktop symlink: ~/Library/Application Support/Claude/claude_desktop_config.json
3. Built-in defaults: Filesystem server

Features:
- 100% pure MCP standard format (compatible with Claude Desktop)
- Environment variable expansion (${VAR_NAME})
- Auto-creation of ~/.aii/ directory
- Interactive wizard for first-time setup
- Validation and error handling
"""


import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from aii.data.integrations.mcp.defaults import get_default_mcp_servers

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for a single MCP server"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    description: str = ""
    enabled: bool = True  # v0.4.10: Health monitoring support


class MCPConfigLoader:
    """
    Loads and manages MCP server configurations.

    Priority order:
    1. User config: ~/.aii/mcp_servers.json
    2. Claude Desktop config (if symlinked or found)
    3. Built-in defaults (filesystem server)
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader.

        Args:
            config_dir: Override config directory (default: ~/.aii/)
        """
        self.config_dir = config_dir or Path.home() / ".aii"
        self.servers: Dict[str, ServerConfig] = {}
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Config directory: {self.config_dir}")

    def load_configurations(self) -> Dict[str, ServerConfig]:
        """
        Load configurations from all sources with priority.

        Returns:
            Dictionary of server name to ServerConfig

        Priority:
        1. User config (~/.aii/mcp_servers.json)
        2. Claude Desktop config (if found)
        3. Built-in defaults
        """
        # Start with empty servers
        self.servers = {}

        # Try loading in priority order
        loaded_from = None

        # Priority 1: User config
        user_config_path = self.config_dir / "mcp_servers.json"
        if user_config_path.exists():
            logger.info(f"Loading user config from: {user_config_path}")
            if self._load_from_file(user_config_path):
                loaded_from = "user"
                logger.info(f"Loaded {len(self.servers)} servers from user config")

        # Priority 2: Claude Desktop config (check common locations)
        if not loaded_from:
            claude_paths = [
                Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
                self.config_dir / "claude_desktop_config.json"  # Symlink location
            ]

            for claude_path in claude_paths:
                if claude_path.exists():
                    logger.info(f"Found Claude Desktop config: {claude_path}")
                    if self._load_from_file(claude_path):
                        loaded_from = "claude_desktop"
                        logger.info(f"Loaded {len(self.servers)} servers from Claude Desktop config")
                        break

        # Priority 3: Built-in defaults
        if not loaded_from:
            logger.info("No user config found, using built-in defaults")
            self._load_defaults()
            loaded_from = "defaults"

        logger.info(f"Configuration loaded from: {loaded_from}")
        logger.info(f"Total servers configured: {len(self.servers)}")

        return self.servers

    def _load_from_file(self, path: Path) -> bool:
        """
        Load configuration from a JSON file.

        Args:
            path: Path to configuration file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(path, 'r') as f:
                config_data = json.load(f)

            # Support both formats:
            # 1. Pure MCP: {"mcpServers": {...}}
            # 2. Claude Desktop: may have other keys too
            servers_data = config_data.get("mcpServers", {})

            if not servers_data:
                logger.warning(f"No 'mcpServers' key found in {path}")
                return False

            # Parse each server
            for server_name, server_config in servers_data.items():
                try:
                    self.servers[server_name] = self._parse_server_config(
                        server_name,
                        server_config
                    )
                    logger.debug(f"Loaded server: {server_name}")
                except Exception as e:
                    logger.error(f"Failed to parse server '{server_name}': {e}")
                    continue

            return len(self.servers) > 0

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")
            return False

    def _parse_server_config(self, name: str, config: Dict[str, Any]) -> ServerConfig:
        """
        Parse a single server configuration.

        Args:
            name: Server name
            config: Server configuration dictionary

        Returns:
            ServerConfig object
        """
        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})
        description = config.get("description", "")
        enabled = config.get("enabled", True)  # v0.6.0: Default to enabled if not specified

        # Expand environment variables
        expanded_command = self._expand_env_vars(command)
        expanded_args = [self._expand_env_vars(arg) for arg in args]
        expanded_env = {
            k: self._expand_env_vars(v)
            for k, v in env.items()
        }

        return ServerConfig(
            name=name,
            command=expanded_command,
            args=expanded_args,
            env=expanded_env,
            description=description,
            enabled=enabled
        )

    def _expand_env_vars(self, value: str) -> str:
        """
        Expand environment variables in format ${VAR_NAME}.

        Args:
            value: String potentially containing ${VAR_NAME} patterns

        Returns:
            String with environment variables expanded
        """
        if not isinstance(value, str):
            return value

        # Simple pattern: ${VAR_NAME}
        import re
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)

    def _load_defaults(self):
        """Load built-in default server configurations"""
        defaults = get_default_mcp_servers()
        servers_data = defaults.get("mcpServers", {})

        for server_name, server_config in servers_data.items():
            self.servers[server_name] = self._parse_server_config(
                server_name,
                server_config
            )

        logger.info(f"Loaded {len(self.servers)} default servers")

    def get_server(self, name: str) -> Optional[ServerConfig]:
        """Get configuration for a specific server"""
        return self.servers.get(name)

    def list_servers(self) -> List[str]:
        """List all configured server names"""
        return list(self.servers.keys())

    def has_servers(self) -> bool:
        """Check if any servers are configured"""
        return len(self.servers) > 0
