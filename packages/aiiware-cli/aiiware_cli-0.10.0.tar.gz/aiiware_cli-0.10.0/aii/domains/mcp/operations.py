# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Operations - Client-Owned MCP Tool Execution

This module implements MCP operation handlers that follow the Client-Owned Workflow pattern.
Similar to git operations (commit, pr), MCP operations:
1. Execute locally on client (call MCP servers)
2. Get raw results
3. Optionally send to server for LLM formatting
4. Display formatted output

Commands:
- aii run mcp <server> <tool> [args...]     # Execute MCP tool (default)
- aii run mcp list                          # List configured servers
- aii run mcp tools <server>                # List tools for server
"""


import json
from typing import Any, Dict, List, Optional

from ...data.integrations.mcp.client_manager import MCPClientManager
from ...data.integrations.mcp.config_loader import MCPConfigLoader


class MCPToolOperation:
    """
    Execute MCP tool operation.

    Usage: aii run mcp <server> <tool> [args...]
    Example: aii run mcp chrome-devtools new_page https://github.com

    Flow:
    1. Initialize local MCP client manager
    2. Parse arguments (server, tool, tool_args)
    3. Call MCP tool locally
    4. Format and display result
    """

    def __init__(self, config_manager, api_client):
        """
        Initialize MCP tool operation.

        Args:
            config_manager: ConfigManager instance
            api_client: AiiCLIClient instance for server communication
        """
        self.config = config_manager
        self.client = api_client
        self.config_loader = MCPConfigLoader()
        self.mcp_client: Optional[MCPClientManager] = None

    async def execute(self, args: Optional[list] = None) -> int:
        """
        Execute MCP tool.

        Args:
            args: [server_name, tool_name, *tool_args]

        Returns:
            Exit code (0 = success, 1 = error)
        """
        if not args:
            print("❌ Usage: aii run mcp <server> <tool> [args...]")
            print()
            print("Examples:")
            print("  aii run mcp chrome-devtools new_page https://github.com")
            print("  aii run mcp github list-repos")
            print("  aii run mcp filesystem read README.md")
            print()
            print("To list configured servers: aii run mcp list")
            print("To list tools for a server: aii run mcp tools <server>")
            return 1

        # Parse arguments
        server_name = args[0]
        tool_args = args[1:]  # [tool_name, *tool_args]

        if not tool_args:
            print(f"❌ No tool specified for server '{server_name}'")
            print(f"💡 To list available tools: aii run mcp tools {server_name}")
            return 1

        tool_name = tool_args[0]
        tool_params = tool_args[1:]

        # Initialize MCP client
        await self._initialize_mcp_client()

        # Execute MCP tool (client-side execution)
        result = await self._call_mcp_tool(server_name, tool_name, tool_params)

        if not result["success"]:
            print(f"❌ MCP tool execution failed:")
            print(result["error"])
            return 1

        # Format and display the result
        self._display_result(result)
        return 0

    async def _initialize_mcp_client(self):
        """Initialize MCP client manager (lazy initialization)"""
        if not self.mcp_client:
            self.mcp_client = MCPClientManager(self.config_loader)
            await self.mcp_client.initialize()

    async def _call_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        tool_args: List[str]
    ) -> Dict[str, Any]:
        """Call MCP tool and return result

        Args:
            server_name: MCP server name (e.g., "chrome-devtools")
            tool_name: Tool to execute (e.g., "new_page")
            tool_args: Tool arguments

        Returns:
            dict: Execution result with success, result, error fields
        """
        try:
            # Build tool arguments as dict (MCP expects dict, not list)
            tool_arguments = self._parse_tool_arguments(tool_name, tool_args)

            # Execute MCP tool
            # Note: call_tool auto-discovers which server has the tool
            # But we specify server_name for error messages
            mcp_result = await self.mcp_client.call_tool(
                tool_name=tool_name,
                arguments=tool_arguments
            )

            # Check if call was successful
            if mcp_result.is_error:
                return {
                    "success": False,
                    "result": None,
                    "error": mcp_result.error or "Tool execution failed",
                    "server": server_name,
                    "tool": tool_name
                }

            return {
                "success": True,
                "result": mcp_result.content,
                "error": None,
                "server": server_name,
                "tool": tool_name
            }

        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "server": server_name,
                "tool": tool_name
            }

    def _parse_tool_arguments(self, tool_name: str, tool_args: List[str]) -> Dict[str, Any]:
        """Parse positional arguments into dict format for MCP

        Args:
            tool_name: Name of the tool
            tool_args: Positional arguments

        Returns:
            dict: Parsed arguments
        """
        if not tool_args:
            return {}

        # Try to parse as JSON first (for complex arguments)
        if len(tool_args) == 1 and tool_args[0].startswith('{'):
            try:
                return json.loads(tool_args[0])
            except json.JSONDecodeError:
                pass

        # Map common tool argument patterns
        if tool_name == "new_page":
            return {"url": tool_args[0] if tool_args else "about:blank"}
        elif tool_name in ["navigate", "goto"]:
            return {"url": tool_args[0]}
        elif tool_name in ["read_file", "read"]:
            return {"path": tool_args[0]}
        elif tool_name in ["write_file", "write"]:
            return {
                "path": tool_args[0],
                "content": tool_args[1] if len(tool_args) > 1 else ""
            }
        else:
            # Generic: use args array or first arg as value
            if len(tool_args) == 1:
                return {"value": tool_args[0]}
            else:
                return {"args": tool_args}

    def _display_result(self, result: Dict[str, Any]):
        """Display MCP tool result

        Args:
            result: MCP execution result
        """
        server = result["server"]
        tool = result["tool"]
        mcp_result = result["result"]

        # Display success indicator
        print(f"✓ MCP Tool: {server}.{tool}")
        print()

        # Format result based on type
        if isinstance(mcp_result, dict):
            # Pretty-print dict
            print(json.dumps(mcp_result, indent=2))
        elif isinstance(mcp_result, list):
            # Format list
            for i, item in enumerate(mcp_result):
                if isinstance(item, dict):
                    print(f"{i}: {json.dumps(item, indent=2)}")
                else:
                    print(f"{i}: {item}")
        else:
            # Simple value
            print(str(mcp_result))


class MCPListOperation:
    """
    List configured MCP servers.

    Usage: aii run mcp list
    """

    def __init__(self, config_manager, api_client):
        """
        Initialize MCP list operation.

        Args:
            config_manager: ConfigManager instance
            api_client: AiiCLIClient instance
        """
        self.config = config_manager
        self.client = api_client
        self.config_loader = MCPConfigLoader()

    async def execute(self, args: Optional[list] = None) -> int:
        """
        List MCP servers.

        Args:
            args: Not used

        Returns:
            Exit code (0 = success, 1 = error)
        """
        # Load MCP configuration
        server_configs = self.config_loader.load_configurations()
        servers = list(server_configs.keys())

        if not servers:
            print("No MCP servers configured.")
            print()
            print("To configure MCP servers:")
            print("  aii mcp add <server-name> <command> [args...]")
            print()
            print("Examples:")
            print("  aii mcp add chrome-devtools npx chrome-devtools-mcp@latest")
            print("  aii mcp add github npx -y @modelcontextprotocol/server-github")
            return 0

        print("📋 Configured MCP Servers:")
        print()
        for server in servers:
            print(f"  • {server}")

        print()
        print("To list tools for a server: aii mcp run tools <server>")

        return 0


class MCPToolsOperation:
    """
    List available tools for an MCP server.

    Usage: aii run mcp tools <server>
    Example: aii run mcp tools chrome-devtools
    """

    def __init__(self, config_manager, api_client):
        """
        Initialize MCP tools operation.

        Args:
            config_manager: ConfigManager instance
            api_client: AiiCLIClient instance
        """
        self.config = config_manager
        self.client = api_client
        self.config_loader = MCPConfigLoader()
        self.mcp_client: Optional[MCPClientManager] = None

    async def execute(self, args: Optional[list] = None) -> int:
        """
        List MCP tools for a server.

        Args:
            args: [server_name]

        Returns:
            Exit code (0 = success, 1 = error)
        """
        if not args:
            print("❌ Usage: aii run mcp tools <server>")
            print()
            print("To list configured servers: aii run mcp list")
            return 1

        server_name = args[0]

        # Initialize MCP client
        if not self.mcp_client:
            self.mcp_client = MCPClientManager(self.config_loader)
            await self.mcp_client.initialize()

        try:
            tools = await self.mcp_client.list_tools(server_name)

            if not tools:
                print(f"No tools available for server '{server_name}'")
                return 0

            print(f"🛠️  Available Tools for '{server_name}':")
            print()

            for tool in tools:
                print(f"  • {tool.name}")
                if tool.description:
                    print(f"    {tool.description}")
                print()

            return 0

        except Exception as e:
            print(f"❌ Failed to list tools for '{server_name}':")
            print(str(e))
            return 1


__all__ = ["MCPToolOperation", "MCPListOperation", "MCPToolsOperation"]
