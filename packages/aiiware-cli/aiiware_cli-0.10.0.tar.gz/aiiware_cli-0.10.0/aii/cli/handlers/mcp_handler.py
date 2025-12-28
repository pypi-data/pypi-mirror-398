# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP (Model Context Protocol) command handler for AII CLI (v0.6.0).

Handles all MCP-related commands:
- mcp add/remove/list/enable/disable
- mcp catalog/install
- mcp status/test/update
- mcp list-tools
- mcp invoke (tool execution)
"""


import json
from typing import Any
from unittest.mock import MagicMock

from ...cli.command_router import CommandRoute


async def handle_mcp_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle MCP commands.

    Args:
        route: CommandRoute with command/subcommand/args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from aii.data.integrations.mcp.client_manager import MCPClientManager
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader

    args = route.args
    mcp_action = args.get("mcp_action")

    # Handle server management commands (v0.4.9) - direct function calls (no MCP client needed)
    if mcp_action in ["add", "remove", "list", "enable", "disable", "catalog", "install"]:
        from aii.functions.mcp.mcp_management_functions import (
            MCPAddFunction,
            MCPRemoveFunction,
            MCPListFunction,
            MCPEnableFunction,
            MCPDisableFunction,
            MCPCatalogFunction,
            MCPInstallFunction,
        )
        from aii.core.models import ExecutionContext

        try:
            # Create mock context (management functions don't need real context)
            context = MagicMock(spec=ExecutionContext)

            # Call appropriate function
            if mcp_action == "add":
                func = MCPAddFunction()
                params = {
                    "server_name": args.get("server_name"),
                    "command": args.get("server_command"),
                    "args": args.get("server_args", []),
                    "transport": args.get("transport", "stdio"),
                }
                if args.get("env"):
                    params["env"] = json.loads(args["env"])

            elif mcp_action == "remove":
                func = MCPRemoveFunction()
                params = {"server_name": args.get("server_name")}

            elif mcp_action == "list":
                func = MCPListFunction()
                params = {}

            elif mcp_action == "enable":
                func = MCPEnableFunction()
                params = {"server_name": args.get("server_name")}

            elif mcp_action == "disable":
                func = MCPDisableFunction()
                params = {"server_name": args.get("server_name")}

            elif mcp_action == "catalog":
                func = MCPCatalogFunction()
                params = {}

            elif mcp_action == "install":
                func = MCPInstallFunction()
                params = {"server_name": args.get("server_name")}
                if args.get("env"):
                    params["env_vars"] = json.loads(args["env"])

            # Execute function
            result = await func.execute(params, context)

            # Print output
            print(result.message)

            return 0 if result.success else 1

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return 1

    # Handle list-tools subcommand
    if mcp_action == "list-tools":
        return await _handle_mcp_list_tools(args)

    # Handle status subcommand (v0.4.10)
    if mcp_action == "status":
        return await _handle_mcp_status(args)

    # Handle test subcommand (v0.4.10)
    if mcp_action == "test":
        return await _handle_mcp_test(args)

    # Handle update subcommand (v0.4.10)
    if mcp_action == "update":
        return await _handle_mcp_update(args)

    # Handle run subcommand (v0.6.0) - Client-Owned Workflow with positional args
    if mcp_action == "run" or mcp_action is None:
        return await _handle_mcp_run(args)

    # Unknown action
    print(f"❌ Unknown MCP action: {mcp_action}")
    print("\nAvailable MCP commands:")
    print("  add/remove/list/enable/disable - Server management")
    print("  catalog/install - Browse and install MCP servers")
    print("  status/test/update - Server diagnostics")
    print("  list-tools - List available MCP tools")
    print("  run - Execute MCP tool")
    return 1


async def _handle_mcp_status(args: dict) -> int:
    """Handle 'aii mcp status' command (v0.4.10)."""
    from aii.data.integrations.mcp.client_manager import MCPClientManager
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader
    from aii.functions.mcp.mcp_management_functions import MCPStatusFunction
    from aii.core.models import ExecutionContext

    server_name = args.get("server_name")
    show_all = args.get("all", False)

    try:
        import os
        debug = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")

        # Always create a fresh MCP client with health monitoring for status command
        # (v0.4.10: Create health monitor WITHOUT full MCP initialization)
        # This avoids connecting to all servers just to check one server's health
        if debug:
            print("🔍 DEBUG: Creating health monitor without full server initialization")

        config_loader = MCPConfigLoader()
        config_loader.load_configurations()  # v0.4.10: Load servers from config files
        mcp_client = MCPClientManager(config_loader=config_loader, enable_health_monitoring=False)

        # Manually create health monitor (doesn't require initialized connections)
        from aii.data.integrations.mcp_health_monitor import MCPHealthMonitor
        health_monitor = MCPHealthMonitor(
            mcp_client=mcp_client,
            verbose=debug,
            check_interval=60.0,
            health_check_timeout=5.0
        )

        # Attach health monitor to client for function access
        mcp_client.health_monitor = health_monitor

        # Check if any servers are configured
        if not config_loader.servers:
            print("⚠️  No MCP servers configured")
            print("\nTo set up MCP servers:")
            print("  aii mcp catalog        # Browse available servers")
            print("  aii mcp add <server>   # Add a server")
            print("  aii mcp list           # List configured servers")
            return 1

        # Trigger immediate health check(s) - creates temporary sessions
        if debug:
            print("🔍 DEBUG: Triggering immediate health check (temporary sessions)...")

        if server_name:
            # Check specific server only
            await health_monitor._check_server(server_name)
        else:
            # Check all configured servers
            servers = health_monitor._get_enabled_servers()
            if debug:
                print(f"🔍 DEBUG: Checking {len(servers)} servers: {servers}")
            for srv in servers:
                try:
                    await health_monitor._check_server(srv)
                except Exception as e:
                    if debug:
                        print(f"⚠️ DEBUG: Health check failed for {srv}: {e}")

        # Create execution context with MCP client
        context = ExecutionContext(
            user_input=f"mcp status {server_name if server_name else ''}",
            function_name="mcp_status",
            parameters={},
            chat_context=None,
            mcp_client=mcp_client
        )

        # Execute status function
        func = MCPStatusFunction()
        params = {}
        if server_name:
            params["server_name"] = server_name
        if show_all:
            params["show_all"] = show_all

        result = await func.execute(params, context)

        # Print output
        print(result.message)

        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Error checking server status: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_mcp_test(args: dict) -> int:
    """Handle 'aii mcp test' command (v0.4.10)."""
    from aii.data.integrations.mcp.client_manager import MCPClientManager
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader
    from aii.functions.mcp.mcp_management_functions import MCPTestFunction
    from aii.core.models import ExecutionContext

    server_name = args.get("server_name")
    verbose = args.get("verbose", False)

    try:
        import os
        debug = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")

        # Create MCP client manager (without initialization for testing)
        # (v0.4.10: Test function creates temporary connections)
        if debug:
            print("🔍 DEBUG: Creating MCP client for connection testing")

        config_loader = MCPConfigLoader()
        config_loader.load_configurations()  # v0.4.10: Load servers from config files
        mcp_client = MCPClientManager(config_loader=config_loader, enable_health_monitoring=False)

        # Check if any servers are configured
        if not config_loader.servers:
            print("⚠️  No MCP servers configured")
            print("\nTo set up MCP servers:")
            print("  aii mcp catalog        # Browse available servers")
            print("  aii mcp add <server>   # Add a server")
            print("  aii mcp list           # List configured servers")
            return 1

        # If specific server requested, verify it exists
        if server_name and server_name not in config_loader.servers:
            print(f"❌ Server '{server_name}' not found")
            print(f"\nConfigured servers: {', '.join(config_loader.servers.keys())}")
            return 1

        # Create execution context with MCP client
        context = ExecutionContext(
            user_input=f"mcp test {server_name if server_name else ''}",
            function_name="mcp_test",
            parameters={},
            chat_context=None,
            mcp_client=mcp_client
        )

        # Execute test function
        func = MCPTestFunction()
        params = {}
        if server_name:
            params["server_name"] = server_name
        if verbose:
            params["verbose"] = verbose

        result = await func.execute(params, context)

        # Print output
        print(result.message)

        return 0 if result.success else 1

    except Exception as e:
        print(f"❌ Error testing MCP connection: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_mcp_update(args: dict) -> int:
    """Handle 'aii mcp update' command (v0.4.10) - supports batch updates."""
    from aii.functions.mcp.mcp_management_functions import MCPUpdateFunction
    from aii.core.models import ExecutionContext
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader

    server_names_input = args.get("server_names")
    auto_confirm = args.get("auto_confirm", False)

    try:
        # Parse server names (comma-separated or "all")
        if server_names_input == "all":
            # Get all configured servers
            config_loader = MCPConfigLoader()
            config_loader.load_configurations()
            server_names = list(config_loader.servers.keys())
            print(f"📦 Updating all {len(server_names)} servers: {', '.join(server_names)}\n")
        else:
            # Parse comma-separated list
            server_names = [s.strip() for s in server_names_input.split(",")]

        # Track results
        total_servers = len(server_names)
        updated_servers = []
        failed_servers = []
        up_to_date_servers = []

        # Process each server
        for i, server_name in enumerate(server_names, 1):
            if total_servers > 1:
                print(f"\n[{i}/{total_servers}] Checking {server_name}...")
                print("─" * 50)

            # Create execution context
            context = ExecutionContext(
                user_input=f"mcp update {server_name}",
                function_name="mcp_update",
                parameters={},
                chat_context=None,
                mcp_client=None
            )

            # Execute update function (check for updates)
            func = MCPUpdateFunction()
            params = {"server_name": server_name, "auto_confirm": False}

            result = await func.execute(params, context)

            # Print update information
            print(result.message)

            # Handle the result
            if not result.success:
                failed_servers.append(server_name)
                continue

            # If already up to date
            if result.data.get("up_to_date"):
                up_to_date_servers.append(server_name)
                continue

            # If update available
            if result.data.get("requires_confirmation"):
                should_update = auto_confirm

                # For batch updates without auto_confirm, ask once per server
                if not auto_confirm:
                    response = input(f"\nUpdate {server_name}? (y/n/all): ").strip().lower()
                    if response == "all":
                        auto_confirm = True  # Auto-confirm remaining servers
                        should_update = True
                    elif response == "y":
                        should_update = True
                    else:
                        print(f"⏭️  Skipped {server_name}")
                        continue

                if should_update:
                    # Perform the actual update
                    update_params = {"server_name": server_name, "auto_confirm": True}
                    update_result = await func.execute(update_params, context)
                    print(update_result.message)

                    if update_result.success:
                        updated_servers.append(server_name)
                    else:
                        failed_servers.append(server_name)

        # Print summary for batch updates
        if total_servers > 1:
            print("\n" + "=" * 50)
            print("📊 Update Summary:")
            print("=" * 50)

            if updated_servers:
                print(f"✅ Updated ({len(updated_servers)}): {', '.join(updated_servers)}")
            if up_to_date_servers:
                print(f"✓  Up to date ({len(up_to_date_servers)}): {', '.join(up_to_date_servers)}")
            if failed_servers:
                print(f"❌ Failed ({len(failed_servers)}): {', '.join(failed_servers)}")

            print(f"\nTotal: {total_servers} servers")

        return 0 if not failed_servers else 1

    except Exception as e:
        print(f"❌ Error updating MCP server(s): {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_mcp_list_tools(args: dict) -> int:
    """Handle 'aii mcp list-tools' command."""
    from aii.data.integrations.mcp.client_manager import MCPClientManager
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader

    server_filter = args.get("server_name")
    detailed = args.get("detailed", False)

    try:
        # Create MCP client (no engine available in v0.6.0 local commands)
        config_loader = MCPConfigLoader()
        mcp_client = MCPClientManager(config_loader=config_loader)
        await mcp_client.initialize()

        # Discover all tools
        all_tools = await mcp_client.discover_all_tools()

        # Group by server
        tools_by_server = {}
        for tool in all_tools:
            if tool.server_name not in tools_by_server:
                tools_by_server[tool.server_name] = []
            tools_by_server[tool.server_name].append(tool)

        # Filter by server if specified
        if server_filter:
            if server_filter not in tools_by_server:
                print(f"❌ Server '{server_filter}' not found")
                print(f"\nAvailable servers: {', '.join(tools_by_server.keys())}")
                return 1
            tools_by_server = {server_filter: tools_by_server[server_filter]}

        # Display
        for server_name, tools in tools_by_server.items():
            print(f"\n{'='*60}")
            print(f"📦 Server: {server_name}")
            print(f"{'='*60}")
            print(f"🔧 Total tools: {len(tools)}\n")

            for tool in tools:
                print(f"  • {tool.name}")
                if tool.description:
                    # Truncate long descriptions
                    desc = tool.description[:100] + "..." if len(tool.description) > 100 else tool.description
                    print(f"    {desc}")

                if detailed and tool.input_schema and 'properties' in tool.input_schema:
                    print(f"    Parameters:")
                    for param_name, param_info in tool.input_schema['properties'].items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', 'No description')
                        required = '(required)' if param_name in tool.input_schema.get('required', []) else '(optional)'
                        print(f"      - {param_name} ({param_type}) {required}")
                        if param_desc and detailed:
                            print(f"        {param_desc[:80]}")
                print()

        print(f"\n📊 Summary:")
        print(f"  Servers: {len(tools_by_server)}")
        print(f"  Total tools: {sum(len(tools) for tools in tools_by_server.values())}")
        print()

        return 0

    except Exception as e:
        print(f"❌ Failed to list MCP tools: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_mcp_run(args: dict) -> int:
    """Handle 'aii mcp run' command - Execute MCP tool directly.

    Usage: aii mcp run <server> <tool> [args...]

    Examples:
    - aii mcp run filesystem read_file README.md
    - aii mcp run chrome-devtools new_page https://github.com
    - aii mcp run github search_repos "python ML"

    Note: For listing servers/tools, use:
    - aii mcp list                     # List configured servers
    - aii mcp list-tools <server>      # List tools for server
    """
    from ...domains.mcp.operations import MCPToolOperation
    from ...config.manager import get_config
    from ...cli.client import AiiCLIClient

    # Parse operation from extra_args
    extra_args = args.get("extra_args", [])

    if not extra_args:
        print("❌ Usage: aii mcp run <server> <tool> [args...]")
        print()
        print("Examples:")
        print("  aii mcp run filesystem read_file README.md")
        print("  aii mcp run chrome-devtools new_page https://github.com")
        print("  aii mcp run github search_repos 'python ML'")
        print()
        print("To list servers/tools:")
        print("  aii mcp list                     # List configured servers")
        print("  aii mcp list-tools <server>      # List tools for server")
        return 1

    # Execute MCP tool
    # extra_args = [server_name, tool_name, *tool_args]
    config_manager = get_config()
    client = AiiCLIClient(config_manager)

    try:
        op = MCPToolOperation(config_manager, client)
        return await op.execute(extra_args)
    finally:
        await client.close()


async def _handle_mcp_invoke(args: dict) -> int:
    """Handle 'aii mcp invoke' command - execute MCP tool (DEPRECATED - use 'aii mcp run' instead)."""
    from aii.data.integrations.mcp.client_manager import MCPClientManager
    from aii.data.integrations.mcp.config_loader import MCPConfigLoader

    tool_name = args.get("tool_name")

    if not tool_name:
        print("❌ Error: tool_name is required")
        print("\nUsage:")
        print("  aii mcp invoke <tool_name> --path <path> [--content <content>] [--args <json>]")
        print("  aii mcp list-tools [server_name] [--detailed]")
        print("\nExamples:")
        print("  aii mcp invoke read_text_file --path /path/to/file.txt")
        print("  aii mcp list-tools github")
        print("  aii mcp list-tools --detailed")
        return 1

    try:
        # Build arguments dictionary
        tool_args = {}

        if args.get("path"):
            import os
            # Resolve symlinks to real paths (e.g., /tmp -> /private/tmp on macOS)
            # This ensures paths match MCP server's allowed directories
            tool_args["path"] = os.path.realpath(args["path"])

        if args.get("content"):
            tool_args["content"] = args["content"]

        # Parse additional JSON args if provided
        if args.get("args"):
            try:
                additional_args = json.loads(args["args"])
                tool_args.update(additional_args)
            except json.JSONDecodeError as e:
                print(f"❌ Error: Invalid JSON in --args: {e}")
                return 1

        # Create MCP client
        config_loader = MCPConfigLoader()
        mcp_client = MCPClientManager(config_loader=config_loader)
        await mcp_client.initialize()

        # Call the tool
        print(f"🔧 Calling MCP tool: {tool_name}")
        if tool_args:
            print(f"📋 Arguments: {tool_args}")

        result = await mcp_client.call_tool(tool_name, tool_args)

        if result.success:
            print(f"\n✅ Success!")
            print()

            # Display result content
            for item in result.content:
                if hasattr(item, 'text'):
                    print(item.text)
                elif hasattr(item, 'data'):
                    print(json.dumps(item.data, indent=2))
                else:
                    print(str(item))

            return 0
        else:
            error_msg = result.error or "Operation failed"
            print(f"\n❌ Error: {error_msg}")

            # Provide helpful hint for path access issues
            if "path" in tool_args and not result.success:
                print("\n💡 Hint: The MCP filesystem server may not have access to this path.")
                print("   Check your MCP configuration in ~/.aii/mcp_servers.json")
                print("   Current allowed directories can be seen in the server startup messages above.")

            return 1

    except Exception as e:
        print(f"❌ MCP command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
