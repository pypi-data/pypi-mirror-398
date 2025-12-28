# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Two-tier command routing for AII CLI.

Tier 1: Local commands (no server required)
  - config (init, show, model)
  - mcp (add, remove, list, status)
  - serve (start, stop, status, restart)
  - version, help

Tier 2: AI function commands (server required)
  - All natural language prompts
  - Interactive mode
"""


from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CommandRoute:
    """Command routing result"""
    tier: int  # 1 = local, 2 = server
    command: str  # Command name
    subcommand: Optional[str] = None  # Subcommand (e.g., config init)
    args: Optional[Dict[str, Any]] = None  # Command arguments

    def __post_init__(self):
        """Ensure args is a dict"""
        if self.args is None:
            self.args = {}


class CommandRouter:
    """Route commands to appropriate handlers"""

    # Local commands that don't require server
    LOCAL_COMMANDS = {
        "config": {"init", "show", "model", "list", "set", "validate", "reset", "backup", "provider", "web-search", "oauth"},
        "mcp": {"add", "remove", "list", "status", "enable", "disable", "catalog", "install", "test", "update", "list-tools", "run"},
        "serve": {"start", "stop", "status", "restart"},
        "doctor": set(),
        "template": {"list", "show", "use"},
        "prompt": {"list", "show", "validate", "use"},  # Prompt Library (v0.6.1) - list/show/validate are local, use requires server
        "stats": set(),
        "history": {"list", "search", "continue", "export", "delete"},
        "run": set(),  # Domain operations (v0.6.0) - no subcommands, uses domain/operation args
        "install-completion": set(),
        "uninstall-completion": set(),
        "version": set(),
        "help": set(),
    }

    def route(self, parsed_command: Dict[str, Any]) -> CommandRoute:
        """
        Route command to appropriate tier.

        Args:
            parsed_command: Parsed command from CommandParser

        Returns:
            CommandRoute with tier, command, subcommand, args
        """

        # Check if it's a local command (Tier 1)
        command = parsed_command.get("command")

        if command in self.LOCAL_COMMANDS:
            subcommand = parsed_command.get("subcommand")
            return CommandRoute(
                tier=1,
                command=command,
                subcommand=subcommand,
                args=parsed_command.get("args", {})
            )

        # Check if input_text is actually a local command name
        # (CommandParser treats single words like "help" as input_text)
        input_text = parsed_command.get("input_text", "")
        if input_text and input_text.strip() in self.LOCAL_COMMANDS:
            return CommandRoute(
                tier=1,
                command=input_text.strip(),
                subcommand=None,
                args=parsed_command.get("args", {})
            )

        # Otherwise, it's an AI prompt (Tier 2)
        # Extract user input from various possible keys
        user_input = (
            parsed_command.get("user_input") or
            input_text or
            parsed_command.get("prompt") or
            ""
        )

        # Get args safely (handle None)
        extra_args = parsed_command.get("args")
        if extra_args is None:
            extra_args = {}

        return CommandRoute(
            tier=2,
            command="execute",  # Generic execution command
            args={
                "user_input": user_input,
                **extra_args
            }
        )

    def is_local_command(self, command: str) -> bool:
        """
        Check if command is local (Tier 1).

        Args:
            command: Command name

        Returns:
            True if command is local, False if requires server
        """
        return command in self.LOCAL_COMMANDS

    def get_local_subcommands(self, command: str) -> set:
        """
        Get valid subcommands for a local command.

        Args:
            command: Local command name

        Returns:
            Set of valid subcommands (empty set if none)
        """
        return self.LOCAL_COMMANDS.get(command, set())

    def validate_route(self, route: CommandRoute) -> tuple[bool, Optional[str]]:
        """
        Validate a command route.

        Args:
            route: CommandRoute to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Tier 1 validation
        if route.tier == 1:
            if route.command not in self.LOCAL_COMMANDS:
                return False, f"Unknown local command: {route.command}"

            # Check if subcommand is valid (if any)
            if route.subcommand:
                valid_subcommands = self.LOCAL_COMMANDS[route.command]
                if valid_subcommands and route.subcommand not in valid_subcommands:
                    return False, f"Unknown subcommand '{route.subcommand}' for command '{route.command}'"

        # Tier 2 validation
        elif route.tier == 2:
            if not route.args.get("user_input"):
                return False, "No input provided for AI command"

        else:
            return False, f"Invalid tier: {route.tier}"

        return True, None
