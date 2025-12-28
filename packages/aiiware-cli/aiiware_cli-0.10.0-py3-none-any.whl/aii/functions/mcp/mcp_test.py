# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""MCP Test Function - Test MCP server connectivity and diagnose issues."""


import asyncio
import logging
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

logger = logging.getLogger(__name__)


class MCPTestFunction(FunctionPlugin):
    """
    Test MCP server connectivity and diagnose issues (v0.4.10).

    Features:
    - Test connection to specific server or all servers
    - Measure response time
    - List available tools
    - Provide troubleshooting tips
    - No persistent connection (uses temporary connection)
    """

    @property
    def name(self) -> str:
        return "mcp_test"

    @property
    def description(self) -> str:
        return "Test MCP server connectivity and diagnose issues"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> List[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    def get_parameters_schema(self) -> ParameterSchema:
        return {
            "type": "object",
            "properties": {
                "server_name": {
                    "type": "string",
                    "description": "Server name to test (optional, tests all if not specified)"
                },
                "verbose": {
                    "type": "boolean",
                    "description": "Show detailed diagnostic information",
                    "default": False
                }
            },
            "required": []
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Test MCP server connectivity."""
        try:
            server_name = parameters.get("server_name")
            verbose = parameters.get("verbose", False)

            from ...data.integrations.mcp.config_loader import MCPConfigLoader

            config_loader = MCPConfigLoader()
            config_loader.load_configurations()

            if not config_loader.servers:
                return ExecutionResult(
                    success=False,
                    message="⚠️  No MCP servers configured",
                    data={"error": "no_servers"}
                )

            if server_name:
                # Test specific server
                if server_name not in config_loader.servers:
                    available = ", ".join(config_loader.servers.keys())
                    return ExecutionResult(
                        success=False,
                        message=f"❌ Server '{server_name}' not found\n\n"
                                f"Available servers: {available}",
                        data={"error": "server_not_found", "available": list(config_loader.servers.keys())}
                    )

                result = await self._test_server(
                    server_name,
                    config_loader.servers[server_name],
                    verbose
                )
                output = self._format_test_result(server_name, result, verbose)

                return ExecutionResult(
                    success=result["success"],
                    message=output,
                    data={
                        "clean_output": "✅ Connected" if result["success"] else "❌ Failed",
                        "server_name": server_name,
                        **result
                    }
                )
            else:
                # Test all servers
                results = {}
                for name, config in config_loader.servers.items():
                    results[name] = await self._test_server(name, config, verbose)

                output = self._format_all_results(results, verbose)
                success_count = sum(1 for r in results.values() if r["success"])
                total = len(results)

                return ExecutionResult(
                    success=success_count == total,
                    message=output,
                    data={
                        "clean_output": f"{success_count}/{total} servers connected",
                        "results": results,
                        "success_count": success_count,
                        "total": total
                    }
                )

        except Exception as e:
            logger.error(f"Error testing MCP servers: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Error testing MCP servers: {str(e)}",
                data={"error": str(e)}
            )

    async def _test_server(
        self, server_name: str, config: Any, verbose: bool
    ) -> Dict[str, Any]:
        """
        Test connection to a single server.

        Returns:
            Dictionary with test results
        """
        import time
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        result = {
            "success": False,
            "response_time_ms": None,
            "tools_count": 0,
            "tools": [],
            "error": None,
            "error_type": None
        }

        start_time = time.time()

        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=config.command,
                args=config.args,
                env=config.env or {}
            )

            # Test connection with timeout
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize
                    await session.initialize()

                    # List tools
                    tools_response = await session.list_tools()
                    tools = tools_response.tools

                    response_time = (time.time() - start_time) * 1000

                    result["success"] = True
                    result["response_time_ms"] = response_time
                    result["tools_count"] = len(tools)
                    if verbose:
                        result["tools"] = [
                            {"name": t.name, "description": t.description}
                            for t in tools
                        ]

        except asyncio.TimeoutError:
            result["error"] = "Connection timeout (>30s)"
            result["error_type"] = "timeout"
        except FileNotFoundError as e:
            result["error"] = f"Command not found: {config.command}"
            result["error_type"] = "command_not_found"
        except PermissionError:
            result["error"] = f"Permission denied: {config.command}"
            result["error_type"] = "permission_denied"
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            result["error_type"] = "unknown"

            # Categorize common errors
            if "not found" in error_msg.lower():
                result["error_type"] = "not_found"
            elif "permission" in error_msg.lower():
                result["error_type"] = "permission"
            elif "connection" in error_msg.lower():
                result["error_type"] = "connection"

        return result

    def _format_test_result(
        self, server_name: str, result: Dict[str, Any], verbose: bool
    ) -> str:
        """Format test result for single server."""
        lines = [f"🔧 Testing: {server_name}"]
        lines.append("=" * 60)

        if result["success"]:
            lines.append(f"\n✅ Status: Connected")
            lines.append(f"⚡ Response time: {result['response_time_ms']:.0f}ms")
            lines.append(f"🔧 Tools available: {result['tools_count']}")

            if verbose and result.get("tools"):
                lines.append("\n📋 Available Tools:")
                for tool in result["tools"][:10]:  # Show first 10
                    desc = tool["description"] or "No description"
                    lines.append(f"  • {tool['name']}: {desc[:80]}")
                if result["tools_count"] > 10:
                    lines.append(f"  ... and {result['tools_count'] - 10} more")

        else:
            lines.append(f"\n❌ Status: Failed")
            lines.append(f"🔴 Error: {result['error']}")
            lines.append("")
            lines.append(self._get_troubleshooting_tips(result["error_type"]))

        return "\n".join(lines)

    def _format_all_results(
        self, results: Dict[str, Dict[str, Any]], verbose: bool
    ) -> str:
        """Format test results for all servers."""
        lines = ["🔧 MCP Server Connection Test"]
        lines.append("=" * 60)

        success = []
        failed = []

        for server_name, result in results.items():
            if result["success"]:
                time_ms = result["response_time_ms"]
                tools = result["tools_count"]
                success.append(f"  ✅ {server_name}: {time_ms:.0f}ms ({tools} tools)")
            else:
                error = result["error"]
                failed.append(f"  ❌ {server_name}: {error}")

        if success:
            lines.append("\n✅ Connected:")
            lines.extend(success)

        if failed:
            lines.append("\n❌ Failed:")
            lines.extend(failed)
            lines.append("\n💡 Tip: Run 'aii mcp test <server_name>' for detailed diagnostics")

        lines.append(f"\n📊 Summary: {len(success)}/{len(results)} servers connected")

        return "\n".join(lines)

    def _get_troubleshooting_tips(self, error_type: str) -> str:
        """Get troubleshooting tips based on error type."""
        tips = {
            "timeout": """💡 Troubleshooting Tips:
  1. Check if the server command is valid
  2. Verify the server is not hanging
  3. Try increasing timeout in config
  4. Check server logs for errors""",

            "command_not_found": """💡 Troubleshooting Tips:
  1. Install the MCP server: npm install -g <package>
  2. Check if npm/npx is in your PATH
  3. Verify the command spelling in config
  4. Run: aii mcp catalog (to see available servers)""",

            "permission_denied": """💡 Troubleshooting Tips:
  1. Check file permissions: ls -la <command>
  2. Make the command executable: chmod +x <command>
  3. Verify you have necessary access rights
  4. Try running with elevated permissions (if needed)""",

            "not_found": """💡 Troubleshooting Tips:
  1. Verify the server is installed
  2. Check npm global packages: npm list -g
  3. Reinstall the server: npm install -g <package>
  4. Check configuration: aii mcp list""",

            "connection": """💡 Troubleshooting Tips:
  1. Check if server is running
  2. Verify network connectivity
  3. Review server configuration
  4. Check firewall settings""",

            "unknown": """💡 Troubleshooting Tips:
  1. Check server logs for details
  2. Verify configuration: aii mcp list
  3. Try reinstalling the server
  4. Run with debug: AII_DEBUG=1 aii mcp test <server>"""
        }

        return tips.get(error_type, tips["unknown"])
