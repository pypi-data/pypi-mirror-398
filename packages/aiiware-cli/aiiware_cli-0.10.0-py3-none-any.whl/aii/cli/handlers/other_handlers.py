# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Miscellaneous command handlers for AII CLI (v0.6.0).

Note: In v0.6.0, these commands may be deprecated or moved to Tier 2 (AI commands via WebSocket).
For now, they remain as Tier 1 local commands for backward compatibility.

Handles:
- history (chat history management)
- template (template operations)
- stats (usage statistics)
- doctor (health checks)
- install-completion/uninstall-completion (shell completion)
"""


from typing import Any

from ...cli.command_router import CommandRoute


async def handle_history_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle chat history commands.

    Note: This may be deprecated in v0.6.0 as history operations
    will be handled via WebSocket API in the future.
    """
    print("❌ History command not yet implemented in v0.6.0")
    print("💡 This feature will be available through the WebSocket API")
    return 1


async def handle_template_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle template commands - routes to AI functions via WebSocket.

    v0.6.0: Templates are Tier 2 AI commands, executed via server.
    """
    from aii.cli.client import AiiCLIClient

    try:
        # Parse template subcommand
        if not route.subcommand:
            print("❌ Missing template subcommand")
            print("\nUsage:")
            print("  aii template list                    # List available templates")
            print("  aii template show <name>             # Show template details")
            print("  aii template use <name> --var value  # Use template")
            return 1

        subcommand = route.subcommand
        args = route.args or {}

        # Create WebSocket client
        client = AiiCLIClient(config_manager)

        if subcommand == "list":
            # Execute natural language command to list templates
            result = await client.execute_command(
                user_input="list all available templates",
                output_mode="CLEAN"
            )
            return 0 if result.get("success") else 1

        elif subcommand == "show":
            # Get template name from args (argparse stores it as template_name)
            template_name = args.get("template_name")
            if not template_name:
                print("❌ Missing template name")
                print("\nUsage: aii template show <name>")
                return 1

            # Execute natural language command to show template
            result = await client.execute_command(
                user_input=f"show template {template_name}",
                output_mode="CLEAN"
            )
            return 0 if result.get("success") else 1

        elif subcommand == "use":
            # Get template name from args (argparse stores it as template_name)
            template_name = args.get("template_name")
            if not template_name:
                print("❌ Missing template name")
                print("\nUsage: aii template use <name> --var1 value1 --var2 value2")
                return 1

            # Collect template variables from args (skip internal argparse keys)
            skip_keys = {"template_name", "template_action", "command", "var"}
            variables = {k: v for k, v in args.items() if k not in skip_keys and v is not None}

            # Build natural language command with variables
            vars_str = " ".join([f"--{k} \"{v}\"" for k, v in variables.items()])
            user_input = f"use template {template_name} {vars_str}"

            # Execute template generation
            result = await client.execute_command(
                user_input=user_input,
                output_mode="CLEAN"
            )
            return 0 if result.get("success") else 1

        else:
            print(f"❌ Unknown template subcommand: {subcommand}")
            print("\nAvailable subcommands: list, show, use")
            return 1

    except Exception as e:
        print(f"❌ Template command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_stats_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle stats commands (v0.4.7, v0.9.0).

    Subcommands:
    - stats models: Model performance analytics (v0.9.0)
    - stats cost: Cost breakdowns and trends (v0.9.0)
    - stats: Legacy usage statistics (v0.4.7)
    """
    from aii.data.storage.analytics import SessionAnalytics
    from aii.functions.system.stats_models_function import StatsModelsFunction
    from aii.functions.system.stats_cost_function import StatsCostFunction
    from aii.core.models import ExecutionContext

    try:
        args = route.args if route.args else {}
        stats_action = args.get("stats_action")

        # v0.9.0: stats models
        if stats_action == "models":
            function = StatsModelsFunction()
            parameters = {
                "period": args.get("period", "30d"),
                "format": args.get("format", "table"),
            }
            if args.get("category"):
                parameters["category"] = args["category"]

            context = ExecutionContext(
                user_input=f"stats models --period {parameters['period']}",
                function_name="stats_models",
                parameters=parameters,
                chat_context=None,
            )

            result = await function.execute(parameters, context)
            # Print the formatted output (table or JSON), not the summary message
            output = result.data.get("clean_output", result.message) if result.data else result.message
            print(output)
            return 0

        # v0.9.0: stats cost
        elif stats_action == "cost":
            function = StatsCostFunction()
            parameters = {
                "period": args.get("period", "30d"),
                "breakdown_by": args.get("breakdown_by", "model"),
                "show_trends": args.get("show_trends", False),
                "show_top_spenders": args.get("show_top_spenders", False),
                "top_limit": args.get("top_limit", 10),
                "format": args.get("format", "table"),
            }

            context = ExecutionContext(
                user_input=f"stats cost --period {parameters['period']}",
                function_name="stats_cost",
                parameters=parameters,
                chat_context=None,
            )

            result = await function.execute(parameters, context)
            # Print the formatted output (table or JSON), not the summary message
            output = result.data.get("clean_output", result.message) if result.data else result.message
            print(output)
            return 0

        # Legacy v0.4.7: stats (no subcommand)
        else:
            # Get period from args (default to 30d)
            period = args.get("period", "30d")

            # Create analytics instance
            analytics = SessionAnalytics()

            # Query analytics
            stats = await analytics.get_usage_stats(period, "all")

            # Format output
            output = _format_stats_output(stats, period)
            print(output)

            return 0

    except Exception as e:
        print(f"❌ Error generating statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def _format_stats_output(stats: dict, period: str) -> str:
    """Format statistics for display."""
    output = [f"📊 AII Usage Statistics (Last {period})\n"]

    # Session summary
    total_sessions = stats.get("total_sessions", 0)
    output.append(f"Total Executions: {total_sessions}")

    if total_sessions == 0:
        output.append("\nNo usage data available for this period.")
        return "\n".join(output)

    output.append("")  # Blank line

    # Function breakdown
    if "functions" in stats:
        functions = stats["functions"]
        output.append("📈 Top Functions:")

        total_executions = functions.get("total_executions", 0)
        for func_name, count in functions.get("by_function", [])[:5]:
            percentage = (count / total_executions * 100) if total_executions > 0 else 0
            output.append(f"  {count:3d}× {func_name:20s} ({percentage:.1f}%)")

        if len(functions.get("by_function", [])) > 5:
            remaining = len(functions.get("by_function", [])) - 5
            output.append(f"  ... and {remaining} more")

        output.append("")

    # Token breakdown
    if "tokens" in stats:
        tokens = stats["tokens"]
        total_tokens = tokens.get("total_tokens", 0)

        if total_tokens > 0:
            output.append("🔢 Token Usage:")
            output.append(f"  Total: {total_tokens:,} tokens")
            output.append(f"  Input: {tokens.get('total_input', 0):,} tokens")
            output.append(f"  Output: {tokens.get('total_output', 0):,} tokens")
            output.append("")

    # Cost breakdown
    if "costs" in stats:
        costs = stats["costs"]
        total_cost = costs.get("total_cost", 0.0)

        if total_cost > 0:
            output.append("💰 Cost Breakdown:")
            output.append(f"  Total: ${total_cost:.4f}\n")

            by_function = costs.get("by_function", [])
            if by_function:
                output.append("  Top 5 by cost:")
                for func_name, cost in by_function[:5]:
                    percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                    output.append(f"    {func_name:20s} ${cost:.4f} ({percentage:.1f}%)")

                if len(by_function) > 5:
                    remaining = len(by_function) - 5
                    output.append(f"  ... and {remaining} more")

    return "\n".join(output)


async def handle_doctor_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """Handle doctor/health check commands."""
    from aii.cli.health_check import HealthCheckRunner

    try:
        # Create health check runner
        runner = HealthCheckRunner(
            use_colors=output_config.use_colors if output_config else True,
            use_emojis=output_config.use_emojis if output_config else True,
        )

        # Register all default checks
        runner.register_default_checks()

        # Build context for health checks (simplified for v0.6.0)
        context = {
            "config_manager": config_manager,
            "output_config": output_config,
        }

        # Run all health checks
        results = await runner.run_all(context)

        # Format and display results
        output = runner.format_results(results)
        print(output)

        # Return exit code based on results
        failed_count = sum(1 for r in results if r.status.value == "failed")
        return 1 if failed_count > 0 else 0

    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_completion_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """Handle install-completion/uninstall-completion commands."""
    from aii.cli.completion import CompletionGenerator, CompletionInstaller
    from aii.core.registry.function_registry import FunctionRegistry
    from aii.functions import register_all_functions

    try:
        # Create function registry and register all functions
        registry = FunctionRegistry()
        register_all_functions(registry)

        # Create generator and installer
        generator = CompletionGenerator(registry)
        installer = CompletionInstaller(generator)

        # Get shell from args
        args = route.args
        shell = args.get("shell") if args else None

        # Determine action (install or uninstall)
        command = route.command

        if command == "install-completion":
            # Install completion
            success, message = installer.install(shell)
            print(message)

            if success:
                print("\n🎉 Tab completion is now available!")
                print("   Try: aii tr<TAB>")
                return 0
            else:
                return 1

        elif command == "uninstall-completion":
            # Uninstall completion
            success, message = installer.uninstall(shell)
            print(message)

            return 0 if success else 1

        else:
            print(f"❌ Unknown completion command: {command}")
            return 1

    except Exception as e:
        print(f"❌ Completion command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_help_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """Handle help command."""
    from aii.cli.command_parser import CommandParser

    parser = CommandParser()
    parser.print_help()
    return 0
