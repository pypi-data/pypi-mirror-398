# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Error Handler - Translate cryptic MCP errors into helpful messages

Converts JSON-RPC error codes and MCP protocol errors into actionable,
user-friendly messages with suggestions for resolution.

JSON-RPC Error Codes:
- -32700: Parse error
- -32600: Invalid request
- -32601: Method not found
- -32602: Invalid params
- -32603: Internal error
"""


import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """MCP protocol error with code and message"""

    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        """
        Initialize MCP error.

        Args:
            code: JSON-RPC error code
            message: Error message
            data: Optional additional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP Error {code}: {message}")


class MCPErrorHandler:
    """
    Translates MCP errors into helpful, actionable messages.

    Follows SRP: Single responsibility for error translation.
    """

    # JSON-RPC standard error codes
    ERROR_MESSAGES = {
        -32700: "Failed to parse the request. This is usually a bug in AII.",
        -32600: "Invalid request format. This is usually a bug in AII.",
        -32601: "Tool not found. The MCP server doesn't have this tool.",
        -32602: "Invalid arguments. Check the tool's parameter requirements.",
        -32603: "Internal server error. The MCP server encountered a problem.",
    }

    def handle_error(
        self,
        error: Exception,
        server_name: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate helpful error message from MCP error.

        Args:
            error: The error exception
            server_name: Name of the MCP server
            tool_name: Name of the tool (if applicable)
            arguments: Tool arguments (if applicable)

        Returns:
            Formatted error message with suggestions
        """
        # Extract error code and message
        if isinstance(error, MCPError):
            code = error.code
            message = error.message
        elif hasattr(error, "code") and hasattr(error, "message"):
            code = error.code
            message = error.message
        else:
            # Generic error
            return self._format_generic_error(error, server_name, tool_name)

        # Get base message for error code
        base_message = self.ERROR_MESSAGES.get(
            code, f"Unknown error (code: {code})"
        )

        # Build error output
        output_lines = [
            f"⚠️  {server_name} MCP Error: {base_message}",
            "",
            f"Details: {message}",
            "",
        ]

        # Add context-specific suggestions
        suggestions = self._get_suggestions(code, server_name, tool_name, arguments)
        if suggestions:
            output_lines.append("Suggestions:")
            for suggestion in suggestions:
                output_lines.append(f"  {suggestion}")
            output_lines.append("")

        # Add debug info for tool calls
        if tool_name and arguments:
            output_lines.append("Debug Info:")
            output_lines.append(f"  Tool: {tool_name}")
            output_lines.append(f"  Arguments: {arguments}")
            output_lines.append("")

        # Add help command
        output_lines.append(f"Need help? Try: aii \"list tools for {server_name}\"")

        return "\n".join(output_lines)

    def _get_suggestions(
        self,
        code: int,
        server_name: str,
        tool_name: Optional[str],
        arguments: Optional[Dict[str, Any]],
    ) -> list[str]:
        """
        Get context-specific suggestions for error code.

        Args:
            code: Error code
            server_name: Server name
            tool_name: Tool name (if applicable)
            arguments: Arguments (if applicable)

        Returns:
            List of suggestion strings
        """
        suggestions = []

        if code == -32601:  # Method not found
            suggestions.append(f"List available tools: aii \"show {server_name} tools\"")
            suggestions.append(f"Or try: aii \"use {server_name} to [describe your task]\"")

        elif code == -32602:  # Invalid params
            if tool_name:
                suggestions.append(
                    f"Check tool signature: aii \"describe {server_name} {tool_name} tool\""
                )
            if arguments:
                import json
                suggestions.append(
                    f"Arguments provided:\n    {json.dumps(arguments, indent=2)}"
                )

        elif code == -32603:  # Internal error
            suggestions.append(f"Try restarting the server: aii mcp disable {server_name} && aii mcp enable {server_name}")
            suggestions.append("Check server logs for more details")

        elif code == -32700 or code == -32600:  # Parse/request error
            suggestions.append("This may be a bug in AII. Please report it:")
            suggestions.append("  https://github.com/anthropics/aii/issues")

        return suggestions

    def _format_generic_error(
        self,
        error: Exception,
        server_name: str,
        tool_name: Optional[str],
    ) -> str:
        """
        Format generic (non-MCP) error.

        Args:
            error: The error exception
            server_name: Server name
            tool_name: Tool name (if applicable)

        Returns:
            Formatted error message
        """
        output_lines = [
            f"⚠️  {server_name} Error: {type(error).__name__}",
            "",
            f"Details: {str(error)}",
            "",
        ]

        # Add generic suggestions
        output_lines.append("Suggestions:")
        output_lines.append(f"  • Check that {server_name} server is running")
        output_lines.append(f"  • Verify server configuration: aii mcp list")
        output_lines.append(f"  • Try restarting: aii mcp disable {server_name} && aii mcp enable {server_name}")
        output_lines.append("")

        output_lines.append(f"Need help? Try: aii \"troubleshoot {server_name} server\"")

        return "\n".join(output_lines)

    def is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if error is retryable.

        Args:
            error: The error exception

        Returns:
            True if error is retryable (temporary failure)
        """
        # Connection errors are retryable
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True

        # Some MCP errors are retryable
        if isinstance(error, MCPError) or (
            hasattr(error, "code") and hasattr(error, "message")
        ):
            code = error.code if isinstance(error, MCPError) else error.code

            # Internal errors might be temporary
            if code == -32603:
                return True

            # Parse/request errors are NOT retryable (client-side bugs)
            if code in [-32700, -32600, -32601, -32602]:
                return False

        # Unknown errors: assume not retryable (fail fast)
        return False

    def suggest_alternative_tools(
        self, server_name: str, tool_name: str, available_tools: list[str]
    ) -> Optional[str]:
        """
        Suggest alternative tools based on similarity.

        Args:
            server_name: Server name
            tool_name: Requested tool name
            available_tools: List of available tool names

        Returns:
            Suggestion message or None
        """
        if not available_tools:
            return None

        # Simple string similarity (Levenshtein distance would be better)
        # For now, just check for common substrings
        suggestions = []
        tool_name_lower = tool_name.lower()

        for available_tool in available_tools:
            available_lower = available_tool.lower()

            # Check for substring match
            if tool_name_lower in available_lower or available_lower in tool_name_lower:
                suggestions.append(available_tool)
                continue

            # Check for common words
            tool_words = set(tool_name_lower.split("_"))
            available_words = set(available_lower.split("_"))

            if len(tool_words & available_words) >= 2:
                suggestions.append(available_tool)

        if suggestions:
            msg = f"\nDid you mean one of these?\n"
            for suggestion in suggestions[:3]:  # Show top 3
                msg += f"  • {suggestion}\n"
            return msg

        return None


class MCPConnectionError(Exception):
    """Error connecting to MCP server"""

    def __init__(self, server_name: str, message: str):
        self.server_name = server_name
        self.message = message
        super().__init__(f"Failed to connect to {server_name}: {message}")


class MCPTimeoutError(Exception):
    """MCP operation timeout"""

    def __init__(self, server_name: str, operation: str, timeout: float):
        self.server_name = server_name
        self.operation = operation
        self.timeout = timeout
        super().__init__(
            f"{server_name} operation '{operation}' timed out after {timeout}s"
        )
