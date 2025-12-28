# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Domain - Client-Owned MCP Tool Execution

This module implements the Client-Owned MCP Workflow (Pattern 2) where:
1. Client initializes and calls local MCP servers
2. Client gets tool execution results
3. Client optionally sends results to server for LLM formatting
4. Client displays formatted output

This pattern ensures MCP works with:
- Remote Aii server deployments (cloud/remote hosts)
- Chrome extension (future)
- VSCode extension (current)

See: system-dev-docs/aii-cli/issues/issue-006-mcp-unified-architecture-integration.md

Operations:
- tool: Execute MCP tool (default operation)
- list: List configured MCP servers
- tools: List available tools for a server
"""

from typing import Dict, Optional

from .operations import MCPToolOperation, MCPListOperation, MCPToolsOperation


class MCPDomain:
    """
    MCP domain handler.

    Manages MCP-related operations that execute on the client side.
    Follows the Client-Owned Workflow pattern (same as GitDomain).
    """

    def __init__(self):
        """Initialize MCP domain with available operations."""
        self.operations: Dict[str, type] = {
            "tool": MCPToolOperation,      # Execute MCP tool (default)
            "list": MCPListOperation,      # List configured servers
            "tools": MCPToolsOperation,    # List tools for a server
        }

    def get_operation(self, name: str) -> Optional[type]:
        """
        Get operation class by name.

        Args:
            name: Operation name (e.g., "tool", "list", "tools")
                  If name looks like a server name (not in operations),
                  default to "tool" operation.

        Returns:
            Operation class or None if not found
        """
        # Check if this is a known operation
        if name in self.operations:
            return self.operations[name]

        # Default to "tool" operation (for direct server execution)
        # This allows: aii run mcp chrome-devtools new_page https://github.com
        # Instead of: aii run mcp tool chrome-devtools new_page https://github.com
        return self.operations.get("tool")

    def list_operations(self) -> list[str]:
        """
        List all available operations in this domain.

        Returns:
            List of operation names
        """
        return list(self.operations.keys())

    def get_help(self) -> str:
        """
        Get help text for MCP domain.

        Returns:
            Help text string
        """
        return """Usage: aii run mcp <operation> [args]

MCP domain operations (Client-Owned Workflow).

Available Operations:
  tool <server> <tool> [args...]    Execute MCP tool (default operation)
  list                               List configured MCP servers
  tools <server>                     List available tools for a server

Examples:
  # Execute MCP tool (default operation - 'tool' can be omitted)
  aii run mcp chrome-devtools new_page https://github.com
  aii run mcp github list-repos
  aii run mcp filesystem read README.md

  # List configured servers
  aii run mcp list

  # List tools for a server
  aii run mcp tools chrome-devtools

For MCP server management (install, add, remove, etc.), use:
  aii mcp --help

See: system-dev-docs/aii-cli/issues/issue-006-mcp-unified-architecture-integration.md"""


__all__ = ["MCPDomain", "MCPToolOperation", "MCPListOperation", "MCPToolsOperation"]
