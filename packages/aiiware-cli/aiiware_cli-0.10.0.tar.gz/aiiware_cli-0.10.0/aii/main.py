# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Main AII CLI Entry Point (v0.6.0 - Unified WebSocket Architecture)"""


import asyncio
import sys
from pathlib import Path
from typing import Any

from .cli.command_parser import CommandParser
from .cli.command_router import CommandRouter
from .cli.client import AiiCLIClient
from .cli.confirmation import ConfirmationManager
from .config.manager import get_config, init_config
from .config.output_config import OutputConfig

# Import Tier 1 handlers
from .cli.handlers import (
    handle_config_command,
    handle_mcp_command,
    handle_serve_command,
    handle_prompt_command,
    handle_doctor_command,
    handle_completion_command,
    handle_help_command,
    handle_history_command,
    handle_stats_command,
)

# Import domain operations (v0.6.0)
from .domains import register_domain, get_domain, list_domains
from .domains.git import GitDomain


def register_all_domains():
    """Register all domain handlers at startup (v0.6.0)"""
    register_domain("git", GitDomain())
    # Note: MCP is handled via `aii mcp run` (not `aii run mcp`)
    # See: aii/cli/handlers/mcp_handler.py _handle_mcp_run()
    # Future domains:
    # register_domain("code", CodeDomain())
    # register_domain("content", ContentDomain())
    # register_domain("sys", SystemDomain())


def print_session_summary(metadata: dict[str, Any], output_mode: str = "STANDARD") -> None:
    """
    Print unified session summary for all functions.

    Args:
        metadata: Metadata dict from server response
        output_mode: Output mode (STANDARD, THINKING, VERBOSE)
    """
    if not metadata:
        return

    # Build compact single-line summary
    summary_parts = []

    # Function name with checkmark
    function_name = metadata.get("function_name", "unknown")
    summary_parts.append(f"✓ {function_name}")

    # Execution time
    execution_time = metadata.get("execution_time")
    if execution_time:
        summary_parts.append(f"⚡ Total time: {execution_time:.1f}s")

    # Tokens
    tokens_data = metadata.get("tokens", {})
    if tokens_data:
        input_tokens = tokens_data.get("input", 0)
        output_tokens = tokens_data.get("output", 0)
        total_tokens = input_tokens + output_tokens
        summary_parts.append(f"🔢 Tokens: {input_tokens}↗ {output_tokens}↘ ({total_tokens} total)")

    # Cost
    cost = metadata.get("cost")
    if cost and cost > 0:
        if cost < 0.001:
            cost_str = f"${cost:.6f}"
        elif cost < 0.01:
            cost_str = f"${cost:.4f}"
        else:
            cost_str = f"${cost:.2f}"
        summary_parts.append(f"💰 {cost_str}")

    # Model (strip openai: prefix for OpenAI-compatible providers like Moonshot/DeepSeek)
    model = metadata.get("model")
    if model:
        # Strip "openai:" prefix if present (used for OpenAI-compatible providers)
        display_model = model.replace("openai:", "") if model.startswith("openai:") else model
        summary_parts.append(f"🤖 {display_model}")

    # Print compact summary on single line (with blank line above for readability)
    print()  # Single blank line for readability
    print("📊 Execution Summary:")
    print(" • ".join(summary_parts))

    # VERBOSE mode: Add extended metrics
    if output_mode == "VERBOSE":
        # Quality and Confidence line
        quality_parts = []

        # Determine quality based on success_rate (default to 1.0 if not available)
        success_rate = metadata.get("success_rate")
        if success_rate is None:
            success_rate = 1.0  # Default to Excellent if no session data

        if success_rate == 1.0:
            quality_text = "Excellent"
        elif success_rate >= 0.8:
            quality_text = "Good"
        elif success_rate >= 0.5:
            quality_text = "Partial"
        else:
            quality_text = "Poor"
        quality_parts.append(f"🏆 Quality: {quality_text}")

        # Confidence
        confidence = metadata.get("confidence")
        if confidence is not None:
            # Normalize confidence to percentage (handle both 0-1 and 0-100 formats)
            if confidence <= 1.0:
                confidence_pct = confidence * 100
            else:
                confidence_pct = confidence
            quality_parts.append(f"🎯 Confidence: {confidence_pct:.1f}%")

        if quality_parts:
            print(" • ".join(quality_parts))

        # Performance line
        if execution_time and tokens_data:
            total_tokens = tokens_data.get("input", 0) + tokens_data.get("output", 0)
            tokens_per_sec = total_tokens / execution_time if execution_time > 0 else 0
            if tokens_per_sec > 100:
                efficiency = "excellent"
            elif tokens_per_sec > 50:
                efficiency = "good"
            elif tokens_per_sec > 20:
                efficiency = "moderate"
            else:
                efficiency = "wasteful"
            print(f"📈 Performance: Token efficiency: {efficiency}")

        # Pipeline status
        total_functions = metadata.get("total_functions")
        if total_functions is None:
            total_functions = 1  # Default to 1 if no session data

        if success_rate == 1.0:
            print(f"✅ Pipeline completed successfully ({total_functions} function{'s' if total_functions > 1 else ''})")
        elif success_rate > 0:
            print(f"⚠️  Pipeline partially completed ({total_functions} function{'s' if total_functions > 1 else ''})")
        else:
            print(f"❌ Pipeline failed ({total_functions} function{'s' if total_functions > 1 else ''})")


async def main() -> int:
    """Main entry point for AII CLI (v0.6.0)"""
    try:
        # Register domains at startup
        register_all_domains()

        # Parse command line arguments
        parser = CommandParser()
        parsed_cmd = parser.parse_args()

        # Initialize output configuration with CLI args
        class Args:
            def __init__(self, args_dict):
                if args_dict:
                    for key, value in args_dict.items():
                        setattr(self, key, value)

        args_obj = Args(parsed_cmd.args) if parsed_cmd.args else None
        output_config = OutputConfig.load(cli_args=args_obj)

        # Initialize config manager
        config_manager = init_config(Path.home() / ".aii")

        # Route command using CommandRouter
        command_router = CommandRouter()

        # Convert parsed_cmd to dict for routing
        # Extract subcommand from action fields (e.g., template_action, mcp_action, etc.)
        subcommand = getattr(parsed_cmd, "subcommand", None)
        if not subcommand and parsed_cmd.args:
            # Check for *_action fields in args
            for key in parsed_cmd.args:
                if key.endswith("_action") and parsed_cmd.args[key]:
                    subcommand = parsed_cmd.args[key]
                    break

        parsed_dict = {
            "command": parsed_cmd.command,
            "subcommand": subcommand,
            "input_text": parsed_cmd.input_text,
            "args": parsed_cmd.args,
            "interactive": parsed_cmd.interactive,
            "continue_chat": parsed_cmd.continue_chat,
            "new_chat": parsed_cmd.new_chat,
            "offline": parsed_cmd.offline,
        }

        route = command_router.route(parsed_dict)

        if route.tier == 1:
            # Tier 1: Local command (no server needed)
            return await handle_local_command(route, config_manager, output_config)

        elif route.tier == 2:
            # Tier 2: AI command (requires server + WebSocket)
            return await handle_ai_command(route, config_manager, output_config, parsed_cmd)

        else:
            print(f"❌ Unknown command tier: {route.tier}")
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


async def handle_removed_template_command(route: Any, config_manager: Any, output_config: Any) -> int:
    """
    Show migration message for removed 'aii template' command (v0.6.2).

    The template command has been replaced by 'aii prompt' for clarity.
    """
    print("❌ Command 'template' has been removed in v0.6.2\n")
    print("The 'aii template' command has been replaced by 'aii prompt'.\n")
    print("Migration:")
    print("  Old: aii template list")
    print("  New: aii prompt list\n")
    print("  Old: aii template show my-prompt")
    print("  New: aii prompt show my-prompt\n")
    print("  Old: aii template use my-prompt")
    print("  New: aii prompt use my-prompt\n")
    print("  Old: aii template validate my-prompt")
    print("  New: aii prompt validate my-prompt\n")
    print("See CHANGELOG: https://pypi.org/project/aiiware-cli/#history")
    return 1


async def handle_local_command(route: Any, config_manager: Any, output_config: Any) -> int:
    """
    Handle Tier 1 (local) commands that don't require server.

    Args:
        route: CommandRoute with command/subcommand/args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    command = route.command

    # Map commands to handlers
    handlers = {
        "config": handle_config_command,
        "mcp": handle_mcp_command,
        "serve": handle_serve_command,
        "doctor": handle_doctor_command,
        "template": handle_removed_template_command,  # Removed in v0.6.2 - show migration message
        "prompt": handle_prompt_command,  # Prompt Library (v0.6.1)
        "stats": handle_stats_command,
        "history": handle_history_command,
        "help": handle_help_command,
        "run": handle_run_command,  # Domain operations (v0.6.0)
        "install-completion": handle_completion_command,
        "uninstall-completion": handle_completion_command,
    }

    handler = handlers.get(command)
    if not handler:
        print(f"❌ Unknown local command: {command}")
        print("Run 'aii help' for available commands")
        return 1

    # Call handler
    return await handler(route, config_manager, output_config)


async def handle_ai_command(route: Any, config_manager: Any, output_config: Any, parsed_cmd: Any) -> int:
    """
    Handle Tier 2 (AI) commands via WebSocket streaming.

    Args:
        route: CommandRoute with command/subcommand/args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance
        parsed_cmd: Original parsed command (for interactive mode)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Override API URL if --host provided (v0.6.0)
    host_override = route.args.get("host")
    if host_override:
        # Parse host:port format
        if ":" in host_override:
            # User provided host:port (e.g., "localhost:16170")
            host_part, port_part = host_override.split(":", 1)
            api_url = f"http://{host_override}"
            api_host = host_part
            api_port = int(port_part)
        else:
            # User provided just host (e.g., "localhost"), use default port
            api_url = f"http://{host_override}:16169"
            api_host = host_override
            api_port = 16169

        # Override both api.url (for client) and api.host/api.port (for server_manager)
        # Use save=False to avoid persisting temporary --host override to config file
        config_manager.set("api.url", api_url, save=False)
        config_manager.set("api.host", api_host, save=False)
        config_manager.set("api.port", api_port, save=False)

    # Check for interactive mode
    if parsed_cmd.interactive or (not parsed_cmd.input_text and not parsed_cmd.command):
        # v0.6.0: Interactive mode via WebSocket
        from .cli.interactive_websocket import InteractiveChatSession

        session = InteractiveChatSession(config_manager)
        return await session.start()

    # Extract parameters from route
    user_input = route.args.get("user_input", "")
    if not user_input:
        print("❌ No input provided")
        print("Usage: aii \"your request\"")
        return 1

    # Determine output mode from args
    # v0.6.0: Default to STANDARD mode to ensure Session Summary is always shown
    output_mode = "STANDARD"  # Default to STANDARD
    args = route.args
    if args.get('clean'):
        output_mode = "CLEAN"
    elif args.get('standard'):
        output_mode = "STANDARD"
    elif args.get('thinking'):
        output_mode = "THINKING"
    elif args.get('minimal'):
        output_mode = "CLEAN"
    elif args.get('verbose'):
        output_mode = "VERBOSE"
    # else: Keep STANDARD as default

    offline = args.get("offline", False)

    # v0.8.0: Extract model override if provided
    model = args.get("model")

    # Create WebSocket client (already configured with --host override above)
    client = AiiCLIClient(config_manager)

    try:
        # Phase 0: Show immediate feedback that command is being processed
        import sys
        import asyncio
        from aii.cli.debug import debug_print
        from aii.cli.spinner import Spinner

        # Start universal processing spinner (animated for better UX)
        # IMPORTANT: Use sys.stdout to coordinate with token streaming
        processing_spinner = Spinner("Processing...", stream=sys.stdout)
        await processing_spinner.start()

        # v0.6.0 UNIFIED FLOW: Single request with intent recognition + execution
        # Server performs intent recognition, executes function, and returns complete metadata
        # Client checks metadata after response to see if confirmation/local execution needed

        debug_print("MAIN: Executing unified request (intent recognition + execution)...")

        # Pass the spinner to execute_command so it can be stopped when streaming starts
        result = await client.execute_command(
            user_input=user_input,
            output_mode=output_mode,
            offline=offline,
            model=model,  # v0.8.0: Pass model override
            spinner=processing_spinner  # Pass spinner so it can be stopped on first token
        )

        # Ensure spinner is stopped (in case streaming didn't occur)
        # If streaming occurred, this will be a no-op since spinner is already stopped
        await processing_spinner.stop(clear=True)

        debug_print(f"MAIN: Result received - checking for confirmation requirements...")

        # Check if result requires confirmation and local execution (shell commands)
        # v0.6.0: Check both data and metadata for requires_execution_confirmation
        data = result.get("data", {})
        metadata = result.get("metadata", {})

        requires_execution_confirmation = (
            data.get("requires_execution_confirmation", False) or
            metadata.get("requires_execution_confirmation", False)
        )

        if requires_execution_confirmation:
            debug_print("MAIN: Shell command requires confirmation and local execution")
            debug_print(f"MAIN: Metadata received: {metadata}")
            debug_print(f"MAIN: Data received: {data}")

            # Extract command details from data (primary source) or metadata (fallback)
            command = data.get("command") or metadata.get("command")
            explanation = data.get("explanation") or metadata.get("explanation", "Execute shell command")
            risks = data.get("risks") or data.get("safety_notes") or metadata.get("risks", [])

            if not command:
                print("\n❌ Error: No command found in response")
                return 1

            # Display the result message if it wasn't already streamed
            if not result.get("_streaming_occurred", False):
                result_message = result.get("result", "")
                if result_message:
                    print(result_message)

            # Display risks prominently if any
            if risks:
                print("⚠️  POTENTIAL RISKS:")
                for risk in risks:
                    print(f"   • {risk}")
                print()  # Extra newline for readability

            # Display Session Summary BEFORE confirmation (v0.6.0 improvement)
            # This allows users to see token/cost info before deciding to execute
            metadata = result.get("metadata", {})
            print_session_summary(metadata, output_mode="STANDARD")
            print()  # Extra newline before confirmation prompt

            # Prompt user for confirmation
            import sys
            try:
                response = input("⚡ Execute this command? [y/N]: ").strip().lower()
                confirmed = response in ['y', 'yes']
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Operation cancelled")
                return 1

            if not confirmed:
                print("\n❌ Operation cancelled by user")
                return 1

            debug_print(f"MAIN: User confirmed - executing locally: {command}")

            # Execute command locally using subprocess
            import subprocess
            try:
                proc_result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Display output
                if proc_result.stdout:
                    print(proc_result.stdout)
                if proc_result.stderr:
                    print(proc_result.stderr, file=sys.stderr)

                if proc_result.returncode != 0:
                    print(f"⚠️  Command exited with code {proc_result.returncode}")
                    return proc_result.returncode
                else:
                    print(f"✅ Command executed successfully")
                    return 0

            except subprocess.TimeoutExpired:
                print(f"\n❌ Command timed out after 60 seconds")
                return 1
            except Exception as e:
                print(f"\n❌ Command execution failed: {e}")
                return 1

        debug_print(f"MAIN: Result: {result}")

        # Display result
        if result.get("success"):

            # Special handling for git_commit - requires custom formatting and confirmation
            metadata = result.get("metadata", {})
            if metadata.get("function_name") == "git_commit":
                requires_commit_confirmation = metadata.get("requires_commit_confirmation", False)
                # For backward compatibility, also check data field
                if not requires_commit_confirmation:
                    result_data = result.get("data", {})
                    requires_commit_confirmation = result_data.get("requires_commit_confirmation", False)

                if requires_commit_confirmation:
                    # Extract git_commit data from metadata or result data
                    result_data = result.get("data", metadata)

                    # Display git diff
                    git_diff = result_data.get("git_diff", "")
                    if git_diff:
                        print("\n📋 Git Diff:")
                        # Truncate very long diffs
                        if len(git_diff) > 2000:
                            print(git_diff[:2000])
                            print("\n... (diff truncated, showing first 2000 chars)")
                        else:
                            print(git_diff)

                    # Display thinking/reasoning
                    reasoning = result_data.get("reasoning", metadata.get("reasoning", ""))
                    if reasoning:
                        print(f"\n🧠 Thinking: {reasoning}")

                    # Display generated commit message
                    commit_message = result_data.get("commit_message", "")
                    if commit_message:
                        print(f"\n💻 Generated Commit Message:")
                        print(commit_message)
                        print()  # Blank line

                    # Display confidence and tokens
                    confidence = result_data.get("confidence", metadata.get("confidence"))
                    if confidence:
                        print(f"🎯 Confidence: {confidence}%")

                    tokens_data = metadata.get("tokens", {})
                    if tokens_data:
                        input_tokens = tokens_data.get("input", 0)
                        output_tokens = tokens_data.get("output", 0)
                        print(f"🔢 Tokens: Input: {input_tokens} • Output: {output_tokens}")

                    # Prompt for confirmation to proceed with commit
                    print()
                    user_response = input("Proceed with this commit? (y/n): ").strip().lower()

                    if user_response in ['y', 'yes']:
                        # Execute the actual git commit
                        import subprocess
                        try:
                            # Write commit message to temp file
                            import tempfile
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                                f.write(commit_message)
                                commit_msg_file = f.name

                            # Execute git commit with the message file
                            commit_result = subprocess.run(
                                ["git", "commit", "-F", commit_msg_file],
                                capture_output=True,
                                text=True,
                                cwd=config_manager.get("git.repository_path", None)
                            )

                            # Clean up temp file
                            import os
                            os.unlink(commit_msg_file)

                            if commit_result.returncode == 0:
                                print("\n✅ Commit successful!")
                                if commit_result.stdout:
                                    print(commit_result.stdout)
                                return 0
                            else:
                                print(f"\n❌ Commit failed: {commit_result.stderr}")
                                return 1

                        except Exception as e:
                            print(f"\n❌ Failed to execute commit: {e}")
                            return 1
                    else:
                        print("\n❌ Commit cancelled")
                        return 1

            # Display the result ONLY if streaming didn't already print it
            # WebSocket streaming prints tokens in real-time via on_token callback
            # The result field contains the assembled output, but it was already displayed
            # So we should NOT print it again to avoid duplication
            #
            # Check if streaming occurred (at least one token was printed)
            if not result.get("_streaming_occurred", False):
                # No streaming occurred, print the result now
                output = result.get("result", "")
                if output:
                    print(output)
            # else: streaming already displayed the output token-by-token

            # For THINKING and VERBOSE modes, display reasoning first
            if output_mode in ["THINKING", "VERBOSE"]:
                metadata = result.get("metadata", {})
                reasoning = metadata.get("reasoning")
                if reasoning:
                    print()
                    print(f"💭 Reasoning: {reasoning}")

            # For STANDARD, THINKING, and VERBOSE modes, print session summary (even if streaming occurred)
            # The metadata contains tokens, cost, model, execution_time from the server
            if output_mode in ["STANDARD", "THINKING", "VERBOSE"]:
                metadata = result.get("metadata", {})
                print_session_summary(metadata, output_mode=output_mode)

            return 0
        else:
            # Clear loading line
            sys.stderr.write("\r\033[K")
            sys.stderr.flush()

            # Try both 'result' and 'message' fields for error message
            error_msg = result.get("result") or result.get("message", "Unknown error")
            print(f"❌ Error: {error_msg}")
            return 1

    except ConnectionRefusedError:
        print("\n❌ Failed to connect to Aii server")
        print("💡 Try starting the server manually: aii serve")
        return 1

    except RuntimeError as e:
        # RuntimeError from client already has formatted error message
        # Just print it without duplication
        error_msg = str(e)
        if not error_msg.startswith("❌"):
            print(f"\n❌ {error_msg}")
        else:
            print(f"\n{error_msg}")
        return 1

    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        await client.close()


async def handle_run_command(route: Any, config_manager: Any, output_config: Any) -> int:
    """
    Handle 'aii run <domain> <operation>' commands (v0.6.0).

    Routes domain operations to their respective handlers.
    Domain operations execute on the client side and may call the server for LLM generation.

    Args:
        route: CommandRoute with domain/operation args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Extract domain and operation from args
    domain_name = route.args.get("domain")
    operation_name = route.args.get("operation")
    extra_args = route.args.get("extra_args", [])

    # Validate domain and operation were provided
    if not domain_name:
        print("❌ No domain specified")
        print("💡 Usage: aii run <domain> <operation>")
        print(f"💡 Available domains: {', '.join(list_domains())}")
        return 1

    if not operation_name:
        print(f"❌ No operation specified for domain '{domain_name}'")
        print(f"💡 Usage: aii run {domain_name} <operation>")
        return 1

    # Get domain handler
    domain = get_domain(domain_name)
    if not domain:
        print(f"❌ Unknown domain: '{domain_name}'")
        print(f"💡 Available domains: {', '.join(list_domains())}")
        return 1

    # Get operation from domain
    operation_class = domain.get_operation(operation_name)
    if not operation_class:
        print(f"❌ Unknown operation: '{operation_name}' in domain '{domain_name}'")
        print(f"💡 Available operations in '{domain_name}':")
        for op in domain.list_operations():
            print(f"   - {op}")
        return 1

    # Create API client for server communication
    client = AiiCLIClient(config_manager)

    # Instantiate and execute operation
    try:
        operation = operation_class(config_manager, client)
        return await operation.execute(extra_args if extra_args else None)
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await client.close()


def cli_main() -> int:
    """CLI entry point (synchronous wrapper)"""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        # User cancelled - handler already displayed message
        # Return error code without showing traceback
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())
