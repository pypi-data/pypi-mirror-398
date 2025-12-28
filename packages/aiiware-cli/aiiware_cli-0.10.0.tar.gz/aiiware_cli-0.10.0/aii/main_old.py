# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Main AII Beta CLI Entry Point"""


import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from .cli.command_parser import CommandParser
from .core.models import OutputMode
from .cli.interactive import InteractiveShell
from .cli.status_display import StatusDisplay
from .config.manager import get_config, init_config
from .config.output_config import OutputConfig
from .core.engine import AIIEngine
from .data.integrations.mcp.client_manager import MCPClientManager
from .data.integrations.mcp.config_loader import MCPConfigLoader
from .data.integrations.web_search import (
    BraveSearchProvider,
    DuckDuckGoSearchProvider,
    GoogleSearchProvider,
    WebSearchClient,
    create_web_search_client_from_config,
)
from .data.providers.llm_provider import create_llm_provider
from .functions import register_all_functions
from .functions.system.system_functions import (
    ClarificationFunction,
    HelpFunction,
)

# Git commit signature - configurable footer for AI-generated commits (v0.4.10: unified markdown format)
GIT_COMMIT_SIGNATURE = "🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)"


async def main() -> int:
    """Main entry point for AII Beta"""
    try:
        # Parse command line arguments
        parser = CommandParser()
        parsed_cmd = parser.parse_args()

        # Initialize output configuration with CLI args and config files
        # Create a simple object from the parsed args dict to mimic argparse.Namespace
        class Args:
            def __init__(self, args_dict):
                for key, value in args_dict.items():
                    setattr(self, key, value)

        args_obj = Args(parsed_cmd.args) if parsed_cmd.args else None
        output_config = OutputConfig.load(cli_args=args_obj)

        # Initialize configuration
        config_manager = init_config(Path.home() / ".aii")
        config = config_manager.get_all_config()

        # Initialize engine with output configuration
        storage_path = Path.home() / ".aii"
        engine = AIIEngine(config=config, storage_path=storage_path, output_config=output_config, config_manager=config_manager)

        # Register all built-in functions (universal system)
        register_all_functions(engine.function_registry)
        engine.register_function(HelpFunction())
        engine.register_function(ClarificationFunction())

        # Configure integrations from config
        try:
            # Configure LLM provider
            llm_provider_name = config_manager.get("llm.provider")
            llm_model = config_manager.get("llm.model")

            # Try Pydantic AI first, fallback to custom providers
            use_pydantic_ai = True  # Enable Pydantic AI by default for testing

            # Check if provider is configured
            if not llm_provider_name:
                print("⚠️  Warning: No LLM provider configured.")
                print("    Run 'aii config init' to set up your LLM provider.")
                print("    Features requiring LLM will not be available.\n")
            elif llm_provider_name == "gemini":
                api_key = config_manager.get_secret("gemini_api_key")
                if api_key:
                    llm_provider = create_llm_provider(
                        "gemini", api_key, llm_model, use_pydantic_ai
                    )
                    engine.configure(llm_provider=llm_provider)
            elif llm_provider_name == "openai":
                api_key = config_manager.get_secret("openai_api_key")
                if api_key:
                    llm_provider = create_llm_provider(
                        "openai", api_key, llm_model, use_pydantic_ai
                    )
                    engine.configure(llm_provider=llm_provider)
            elif llm_provider_name == "anthropic":
                # ALWAYS use API key authentication for reliable operation
                # Subscription authentication is experimental only via oauth command
                api_key = config_manager.get_secret("anthropic_api_key")
                # Using API key authentication for reliable operation

                if api_key:
                    # Use API key authentication
                    llm_provider = create_llm_provider(
                        "anthropic", api_key, llm_model, use_pydantic_ai
                    )
                    engine.configure(llm_provider=llm_provider)

            # Configure web search using factory function
            if config_manager.get("web_search.enabled"):
                try:
                    web_client = create_web_search_client_from_config(config_manager)
                    engine.configure(web_client=web_client)
                except Exception as e:
                    # Log but don't fail - web search is optional
                    print(f"Warning: Failed to initialize web search: {e}")

            # Configure MCP Client Manager (v0.4.8)
            # MCP is enabled by default with built-in filesystem server
            # User can disable via config or customize servers via ~/.aii/mcp_servers.json
            mcp_enabled = config_manager.get("mcp.enabled", True)
            if mcp_enabled:
                try:
                    # Create MCP config loader (uses priority: user > Claude Desktop > defaults)
                    mcp_config_loader = MCPConfigLoader(config_dir=storage_path)

                    # Check if health monitoring is enabled (v0.4.11)
                    # Note: Disabled by default to enable clean lazy connection behavior
                    # Users can enable via: export AII_HEALTH_MONITORING=true
                    enable_health = os.getenv("AII_HEALTH_MONITORING", "false").lower() not in ("false", "0", "no")

                    # Create and initialize MCP client manager
                    mcp_manager = MCPClientManager(
                        config_loader=mcp_config_loader,
                        enable_health_monitoring=enable_health
                    )

                    # Initialize asynchronously in the background
                    # Note: We'll initialize during first use to avoid blocking startup
                    engine.configure(mcp_client=mcp_manager)

                except Exception as e:
                    print(f"Warning: Failed to initialize MCP: {e}")
                    print("MCP features will be unavailable.")

        except Exception as e:
            print(f"Warning: Could not initialize all integrations: {e}")
            print("Some features may not be available.")

        # Handle different command modes
        if parsed_cmd.interactive or (
            not parsed_cmd.input_text and not parsed_cmd.command
        ):
            # Interactive mode
            shell = InteractiveShell(engine, engine.output_formatter)
            await shell.start(parsed_cmd.continue_chat)
            return 0

        elif parsed_cmd.command == "history":
            # Chat history commands
            return await handle_history_command(parsed_cmd, engine)

        elif parsed_cmd.command == "config":
            # Configuration commands
            return await handle_config_command(parsed_cmd, engine)

        elif parsed_cmd.command == "doctor":
            # Health check commands
            return await handle_doctor_command(parsed_cmd, engine)

        elif parsed_cmd.command == "template":
            # Template commands (v0.4.7)
            return await handle_template_command(parsed_cmd, engine)

        elif parsed_cmd.command == "stats":
            # Stats commands (v0.4.7)
            return await handle_stats_command(parsed_cmd, engine)

        elif parsed_cmd.command == "mcp":
            # MCP commands (v0.4.8)
            return await handle_mcp_command(parsed_cmd, engine)

        elif parsed_cmd.command == "serve":
            # API server command (v0.4.12)
            return await handle_serve_command(parsed_cmd, engine)

        elif parsed_cmd.command == "install-completion":
            # Install shell completion
            return await handle_install_completion_command(parsed_cmd)

        elif parsed_cmd.command == "uninstall-completion":
            # Uninstall shell completion
            return await handle_uninstall_completion_command(parsed_cmd)

        elif parsed_cmd.input_text:
            # Process single input
            try:
                context = None
                if parsed_cmd.continue_chat:
                    context = await engine.continue_chat(parsed_cmd.continue_chat)
                elif parsed_cmd.new_chat:
                    context = await engine.start_new_chat()
                else:
                    # Default: start new chat for single commands
                    context = await engine.start_new_chat()

                # Create status display for CLI mode
                status_display = StatusDisplay(
                    use_emojis=output_config.use_emojis,
                    use_animations=output_config.use_animations
                )

                try:
                    # Git commit requests now use proper GitCommitFunction with LLM-based generation

                    # Determine output mode from CLI flags
                    output_mode_override = None
                    if parsed_cmd.args:
                        if parsed_cmd.args.get('clean'):
                            output_mode_override = OutputMode.CLEAN
                        elif parsed_cmd.args.get('standard'):
                            output_mode_override = OutputMode.STANDARD
                        elif parsed_cmd.args.get('thinking'):
                            output_mode_override = OutputMode.THINKING
                        # Legacy flags (for compatibility)
                        elif parsed_cmd.args.get('minimal'):
                            output_mode_override = OutputMode.CLEAN
                        elif parsed_cmd.args.get('verbose'):
                            output_mode_override = OutputMode.THINKING

                    # Process input and handle confirmations
                    session_id = getattr(parsed_cmd, "session_id", None)
                    result = await engine.process_input(
                        parsed_cmd.input_text,
                        context=context,
                        offline_mode=parsed_cmd.offline,
                        session_id=session_id,
                        status_display=status_display,
                        output_mode_override=output_mode_override,
                    )

                except Exception:
                    raise

                # Check if this is a confirmation request - look for the confirmation text anywhere in segments
                has_confirmation = any(
                    (
                        "Confirm? (y/n):" in segment.content
                        or "Proceed with this commit? (y/n):" in segment.content
                        or "Create this PR? (y/n):" in segment.content
                        or "Create and switch to this branch? (y/n):" in segment.content
                        or "Execute this command? [y/N]:" in segment.content
                        or "Execute this command? (y/n):" in segment.content  # Safety analyzer format
                        or "ABSOLUTELY SURE" in segment.content  # Dangerous command confirmation
                    )
                    for segment in result.segments
                )

                # Handle confirmation (single level - function handles execution)
                if has_confirmation:
                    # This is a confirmation request, display it and get user response
                    engine.output_formatter.display(result)
                    sys.stdout.flush()  # Ensure prompt is displayed immediately
                    try:
                        response = input().strip().lower()
                    except EOFError:
                        print("\n❌ No input available")
                        response = "n"
                    except KeyboardInterrupt:
                        print("\n❌ Cancelled by user")
                        response = "n"

                    if response in ("y", "yes"):
                        # User confirmed, proceed with execution
                        # Show loading animation during execution
                        exec_status_display = StatusDisplay(
                            use_emojis=output_config.use_emojis,
                            use_animations=output_config.use_animations
                        )
                        exec_status_display.start_loading("Executing command...", "spinner")

                        try:
                            # Execute via engine (function will handle the actual execution)
                            result = await engine.confirm_and_execute_last_recognition(
                                confirmed=True,
                                status_display=exec_status_display
                            )
                            exec_status_display.stop_loading()

                            # Display final result (footer is already included by engine)
                            engine.output_formatter.display(result)

                        except Exception:
                            exec_status_display.stop_loading()
                            raise
                    else:
                        # User cancelled
                        cancel_result = engine.output_formatter.format_error(
                            "Operation cancelled by user"
                        )
                        engine.output_formatter.display(cancel_result)
                else:
                    # Regular result, just display
                    engine.output_formatter.display(result)

                return 0

            except Exception as e:
                error_output = engine.output_formatter.format_error(
                    f"Processing failed: {str(e)}"
                )
                engine.output_formatter.display(error_output)
                return 1

        else:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        print("\\nInterrupted by user")
        return 130

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        return 1

    finally:
        # Cleanup
        try:
            if "engine" in locals():
                await engine.shutdown()
        except Exception:
            pass


async def handle_history_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle chat history commands"""
    args = parsed_cmd.args
    history_action = args.get("history_action")

    try:
        if history_action == "list":
            output = await engine.list_chat_history(limit=50, archived=False)
            engine.output_formatter.display(output)

        elif history_action == "search":
            query = args.get("query", "")
            if not query:
                print("Error: Search query required")
                return 1

            output = await engine.search_chats(
                query=query,
                search_content=args.get("content", False),
                tag_filter=args.get("tag"),
            )
            engine.output_formatter.display(output)

        elif history_action == "continue":
            chat_id = args.get("chat_id")
            if not chat_id:
                print("Error: Chat ID required")
                return 1

            # Start interactive session with specific chat
            shell = InteractiveShell(engine, engine.output_formatter)
            await shell.start(chat_id)

        elif history_action == "export":
            chat_id = args.get("chat_id")
            if not chat_id:
                print("Error: Chat ID required")
                return 1

            format_type = args.get("format", "json")
            exported_data = await engine.export_chat(chat_id, format_type)

            if exported_data:
                output_file = f"{chat_id}.{format_type}"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(exported_data)
                print(f"Chat exported to {output_file}")
            else:
                print("Export failed")
                return 1

        elif history_action == "delete":
            chat_id = args.get("chat_id")
            if not chat_id:
                print("Error: Chat ID required")
                return 1

            success = await engine.delete_chat(chat_id)
            if success:
                print(f"Chat {chat_id} deleted successfully")
            else:
                print("Delete failed")
                return 1

        else:
            print("Available history commands: list, search, continue, export, delete")
            return 1

        return 0

    except Exception as e:
        print(f"History command failed: {e}")
        return 1


async def handle_config_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle configuration commands"""
    args = parsed_cmd.args
    config_action = args.get("config_action")

    try:
        config_manager = get_config()

        if config_action == "init":
            # Use interactive setup wizard
            from aii.cli.setup import SetupWizard

            wizard = SetupWizard()
            success = await wizard.run()

            if not success:
                print("\n❌ Setup was not completed.")
                print("You can run 'aii config init' again anytime.")
                sys.exit(1)

            # Wizard handles all configuration, no need for additional validation
            sys.exit(0)

        elif config_action == "show":
            print("📋 Current AII Configuration:")
            print(f"- Config file: {config_manager.config_file}")
            print(f"- Storage path: {engine.storage_path}")

            # LLM provider
            llm_provider = config_manager.get("llm.provider")
            llm_model = config_manager.get("llm.model")
            llm_configured = bool(config_manager.get_secret(f"{llm_provider}_api_key"))
            print(
                f"- LLM provider: {llm_provider} ({llm_model}) - {'✓' if llm_configured else '✗'}"
            )

            # Web search
            web_enabled = config_manager.get("web_search.enabled")
            web_provider = config_manager.get("web_search.provider")
            web_configured = (
                bool(config_manager.get_secret(f"{web_provider}_api_key"))
                if web_enabled
                else False
            )
            print(
                f"- Web search: {web_provider} - {'✓' if web_configured else '✗' if web_enabled else 'disabled'}"
            )

            # Functions
            print(f"- Registered functions: {len(engine.function_registry.functions)}")

            # Validation
            issues = config_manager.validate_config()
            if issues:
                print(f"- Configuration issues: {len(issues)}")

        elif config_action == "validate":
            issues = config_manager.validate_config()
            if issues:
                print("❌ Configuration issues found:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
            else:
                print("✅ Configuration is valid!")

        elif config_action == "reset":
            confirm = input(
                "Are you sure you want to reset configuration to defaults? (y/N): "
            )
            if confirm.lower() in ("y", "yes"):
                config_manager.reset_to_defaults()
                print("✅ Configuration reset to defaults")
            else:
                print("Reset cancelled")

        elif config_action == "backup":
            backup_path = config_manager.backup_config()
            print(f"✅ Configuration backed up to: {backup_path}")

        elif config_action == "set":
            # Set configuration value
            key = args.get("key")
            value = args.get("value")

            if not key or not value:
                print("❌ Error: Both key and value are required")
                print("Usage: aii config set <key> <value>")
                print("\nExamples:")
                print("  aii config set llm.model claude-sonnet-4-5-20250929")
                print("  aii config set llm.provider anthropic")
                print("  aii config set web_search.enabled true")
                return 1

            # Validate and set the configuration
            try:
                # Handle boolean values
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'

                # Validate specific keys
                if key == "llm.model":
                    # Get available models for validation
                    from aii.cli.setup.steps.model_selection import ModelSelectionStep
                    provider = config_manager.get("llm.provider", "anthropic")
                    step = ModelSelectionStep()
                    provider_models = step.MODELS.get(provider, {})

                    if provider_models:
                        valid_model_ids = [m["id"] for m in provider_models.get("models", {}).values()]
                        if value not in valid_model_ids:
                            print(f"⚠️  Warning: '{value}' is not in the list of recommended models for {provider}")
                            print(f"\n📋 Available {provider} models:")
                            for m in provider_models.get("models", {}).values():
                                marker = " ✓" if m.get("recommended") else ""
                                print(f"  - {m['id']}{marker}")

                            # Ask for confirmation
                            confirm = input("\n❓ Continue anyway? (y/N): ").strip().lower()
                            if confirm not in ['y', 'yes']:
                                print("❌ Model change cancelled")
                                return 1

                elif key == "llm.provider":
                    valid_providers = ["anthropic", "openai", "gemini"]
                    if value not in valid_providers:
                        print(f"❌ Error: Invalid provider '{value}'")
                        print(f"Valid providers: {', '.join(valid_providers)}")
                        return 1

                # Set the value
                config_manager.set(key, value, save=True)
                print(f"✅ Configuration updated: {key} = {value}")

                # Show relevant info after update
                if key.startswith("llm."):
                    provider = config_manager.get("llm.provider")
                    model = config_manager.get("llm.model")
                    print(f"\n📋 Current LLM config: {provider} ({model})")
                    print("\n💡 Tip: Restart any running interactive sessions for changes to take effect")

            except Exception as e:
                print(f"❌ Failed to set configuration: {e}")
                return 1

        elif config_action == "model":
            # Change LLM model
            model_id = args.get("model_id")

            if not model_id:
                # Show current model and available options
                from aii.cli.setup.steps.model_selection import ModelSelectionStep
                provider = config_manager.get("llm.provider", "anthropic")
                current_model = config_manager.get("llm.model")

                print(f"📋 Current model: {current_model}")
                print(f"\n✨ Available {provider} models:")

                step = ModelSelectionStep()
                provider_models = step.MODELS.get(provider, {})
                if provider_models:
                    for num, info in provider_models.get("models", {}).items():
                        marker = " ✓ (recommended)" if info.get("recommended") else ""
                        current = " ← current" if info["id"] == current_model else ""
                        print(f"  {info['name']}{marker}{current}")
                        print(f"    {info['description']}")
                        print(f"    ID: {info['id']}\n")

                print("Usage: aii config model <model_id>")
                print("\n💡 Tip: You can also use custom model IDs not listed above")
                return 0

            # Set the model using the existing set logic
            try:
                from aii.cli.setup.steps.model_selection import ModelSelectionStep
                provider = config_manager.get("llm.provider", "anthropic")
                step = ModelSelectionStep()
                provider_models = step.MODELS.get(provider, {})

                if provider_models:
                    valid_model_ids = [m["id"] for m in provider_models.get("models", {}).values()]
                    if model_id not in valid_model_ids:
                        # Custom model ID - ask for confirmation
                        print(f"⚠️  '{model_id}' is not in the list of recommended models for {provider}")
                        print(f"\nThis appears to be a custom model ID.")
                        print(f"Available models: {', '.join(valid_model_ids[:3])}...")
                        print(f"\nRun 'aii config model' to see all available models")

                        # Ask for confirmation
                        confirm = input(f"\nProceed with custom model '{model_id}'? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("❌ Model change cancelled")
                            return 1

                        print(f"\n💡 Note: Ensure '{model_id}' is a valid model ID for {provider}")

                config_manager.set("llm.model", model_id, save=True)
                print(f"✅ Model updated to: {model_id}")
                print(f"\n📋 Current LLM config: {provider} ({model_id})")
                return 0

            except Exception as e:
                print(f"❌ Failed to set model: {e}")
                return 1

        elif config_action == "provider":
            # Change LLM provider
            provider_name = args.get("provider_name")

            if not provider_name:
                # Show current provider and available options
                current_provider = config_manager.get("llm.provider")
                current_model = config_manager.get("llm.model")

                print(f"📋 Current provider: {current_provider} ({current_model})")
                print(f"\n✨ Available providers:")
                print("  1. anthropic - Claude models (Sonnet, Opus, Haiku)")
                print("  2. openai    - GPT models (GPT-4o, GPT-4 Turbo)")
                print("  3. gemini    - Google Gemini models (2.5 Flash, 1.5 Pro)")
                print("\nUsage: aii config provider <provider_name>")
                print("\n⚠️  Note: Changing provider may require setting a new model")
                return 0

            # Validate provider
            valid_providers = ["anthropic", "openai", "gemini"]
            if provider_name not in valid_providers:
                print(f"❌ Error: Invalid provider '{provider_name}'")
                print(f"Valid providers: {', '.join(valid_providers)}")
                return 1

            # Get default model for new provider
            from aii.cli.setup.steps.model_selection import ModelSelectionStep
            step = ModelSelectionStep()
            provider_models = step.MODELS.get(provider_name, {})
            default_model = provider_models.get("default", "")

            if not default_model:
                print(f"❌ Error: No default model found for {provider_name}")
                return 1

            # Set provider and default model together to avoid mismatch
            config_manager.set("llm.provider", provider_name, save=False)
            config_manager.set("llm.model", default_model, save=True)

            print(f"✅ Provider updated to: {provider_name}")
            print(f"✅ Model set to default: {default_model}")

            # Show recommendation to customize if desired
            print(f"\n💡 To use a different {provider_name} model:")
            print(f"   aii config model")
            return 0

        elif config_action == "web-search":
            # Configure web search
            action = args.get("action")
            provider = args.get("provider")

            if not action:
                # Show current web search config
                enabled = config_manager.get("web_search.enabled", False)
                current_provider = config_manager.get("web_search.provider", "duckduckgo")

                print(f"📋 Web search: {'enabled' if enabled else 'disabled'}")
                if enabled:
                    print(f"   Provider: {current_provider}")

                print(f"\n✨ Available actions:")
                print("  enable        - Enable web search")
                print("  disable       - Disable web search")
                print("  set-provider  - Change search provider")

                print(f"\n✨ Available providers:")
                print("  brave       - Fast, privacy-focused (requires API key)")
                print("  google      - Comprehensive results (requires API key)")
                print("  duckduckgo  - Free, no API key needed")

                print("\nUsage:")
                print("  aii config web-search enable")
                print("  aii config web-search set-provider brave")
                return 0

            if action == "enable":
                config_manager.set("web_search.enabled", True, save=True)
                print("✅ Web search enabled")
                provider = config_manager.get("web_search.provider", "duckduckgo")
                print(f"   Using provider: {provider}")
                return 0

            elif action == "disable":
                config_manager.set("web_search.enabled", False, save=True)
                print("✅ Web search disabled")
                return 0

            elif action == "set-provider":
                if not provider:
                    print("❌ Error: Provider name required")
                    print("Usage: aii config web-search set-provider <brave|google|duckduckgo>")
                    return 1

                valid_providers = ["brave", "google", "duckduckgo"]
                if provider not in valid_providers:
                    print(f"❌ Error: Invalid provider '{provider}'")
                    print(f"Valid providers: {', '.join(valid_providers)}")
                    return 1

                config_manager.set("web_search.provider", provider, save=True)
                config_manager.set("web_search.enabled", True, save=True)
                print(f"✅ Web search provider set to: {provider}")

                # Remind about API key if needed
                if provider in ["brave", "google"]:
                    api_key_var = f"{provider.upper()}_SEARCH_API_KEY"
                    print(f"\n💡 Remember to set your API key:")
                    print(f"   export {api_key_var}='your-api-key'")
                return 0

        elif config_action == "oauth":
            return await handle_oauth_command(parsed_cmd, engine)

        else:
            print("Available config commands:")
            print("  init        - Initialize configuration interactively")
            print("  show        - Show current configuration")
            print("  model       - Change LLM model")
            print("  provider    - Change LLM provider")
            print("  web-search  - Configure web search")
            print("  set         - Set configuration value")
            print("  validate    - Validate configuration")
            print("  reset       - Reset to default configuration")
            print("  backup      - Create configuration backup")
            print("  oauth       - OAuth subscription authentication")
            return 1

        return 0

    except Exception as e:
        print(f"Config command failed: {e}")
        return 1


async def handle_oauth_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle OAuth authentication commands"""
    args = parsed_cmd.args
    oauth_action = args.get("oauth_action")

    try:
        from .auth.claude_oauth import ClaudeOAuthClient

        config_dir = Path.home() / ".aii"
        oauth_client = ClaudeOAuthClient(config_dir)

        if oauth_action == "login":
            # Display prominent experimental notice
            print("\n" + "="*70)
            print("🧪 EXPERIMENTAL FEATURE - SUBSCRIPTION AUTHENTICATION")
            print("="*70)
            print("⚠️  WARNING: This is an EXPERIMENTAL feature that may not work reliably.")
            print("📋 NOTICE: OAuth tokens obtained through this flow are not compatible")
            print("          with Claude's programmatic API endpoints.")
            print("🔧 STATUS: Successfully implemented but limited by Claude's API architecture.")
            print("💡 RECOMMEND: Use API key authentication for reliable operation.")
            print("\n📖 For production use, set up API key authentication instead:")
            print("   export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'")
            print("="*70)

            # Ask for explicit confirmation
            try:
                confirm = input("\n❓ Continue with experimental OAuth authentication? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("👋 OAuth authentication cancelled. Use API key for reliable access.")
                    return 0
            except (KeyboardInterrupt, EOFError):
                print("\n👋 OAuth authentication cancelled.")
                return 0

            print("\n🔄 Proceeding with experimental OAuth authentication...")
            success = await oauth_client.authenticate()
            if success:
                print("\n✅ Successfully authenticated with your Claude subscription!")
                print("⚠️  Note: This authentication is experimental and may not work for API calls.")

                # DO NOT update configuration to use subscription automatically
                # Keep this as experimental only
                config_manager = get_config()
                config_manager.set("llm.provider", "anthropic")
                # Do NOT set use_subscription to True - keep it experimental only
                print("✅ OAuth credentials stored for experimental use.")
                print("💡 Main authentication still uses API key for reliability.")

                return 0
            else:
                print("\n❌ Authentication failed. Please try again.")
                return 1

        elif oauth_action == "logout":
            print("🔓 Logging out and clearing experimental OAuth credentials...")
            success = await oauth_client.logout()
            if success:
                print("✅ Successfully logged out. Experimental OAuth credentials cleared.")
                print("💡 Your main API key authentication remains unchanged.")

                # Ensure subscription is disabled
                config_manager = get_config()
                config_manager.set("llm.use_subscription", False)
                print("✅ Configuration updated to disable subscription authentication.")

                return 0
            else:
                print("❌ Logout failed.")
                return 1

        elif oauth_action == "status":
            print("📊 Experimental OAuth Authentication Status:")
            print("⚠️  Note: OAuth authentication is experimental and not used in main flow.")

            # Load credentials and check status
            await oauth_client.load_credentials()
            status_info = oauth_client.get_status_info()

            if status_info["authenticated"]:
                print("✅ Status: Authenticated")
                print(f"🔑 Token: {status_info['access_token']}")
                print(f"🆔 Client ID: {status_info['client_id']}")
                if status_info["expires_at"]:
                    from datetime import datetime
                    expires = datetime.fromisoformat(status_info["expires_at"])
                    print(f"⏰ Token expires: {expires.strftime('%Y-%m-%d %H:%M:%S')}")
                if status_info["user_info"]:
                    user_info = status_info["user_info"]
                    if "email" in user_info:
                        print(f"👤 User: {user_info['email']}")
                    if "plan" in user_info:
                        print(f"📋 Plan: Claude {user_info['plan'].title()}")
            else:
                print("❌ Status: Not authenticated")
                print("Run 'aii config oauth login' to authenticate with your subscription.")

            # Show configuration status
            config_manager = get_config()
            use_subscription = config_manager.get("llm.use_subscription", False)
            print(f"⚙️  Subscription mode: {'Enabled' if use_subscription else 'Disabled'}")

            return 0

        else:
            print("Available OAuth commands:")
            print("  login  - Login with your Claude Pro/Max subscription")
            print("  logout - Logout and clear credentials")
            print("  status - Show authentication status")
            return 1

    except Exception as e:
        print(f"OAuth command failed: {e}")
        return 1


async def handle_doctor_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle doctor/health check commands"""
    from .cli.health_check import HealthCheckRunner
    from .config.manager import get_config

    try:
        # Create health check runner
        output_config = engine.output_config if hasattr(engine, 'output_config') else None
        runner = HealthCheckRunner(
            use_colors=output_config.use_colors if output_config else True,
            use_emojis=output_config.use_emojis if output_config else True,
        )

        # Register all default checks
        runner.register_default_checks()

        # Build context for health checks
        config_manager = get_config()
        context = {
            "config_manager": config_manager,
            "llm_provider": engine.llm_provider,
            "web_client": engine.web_client,
            "storage_path": engine.storage_path,
            "function_registry": engine.function_registry,
            "cost_calculator": engine.cost_calculator if hasattr(engine, 'cost_calculator') else None,
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


async def handle_install_completion_command(parsed_cmd: Any) -> int:
    """Handle install-completion command"""
    from .cli.completion import CompletionGenerator, CompletionInstaller
    from .core.registry.function_registry import FunctionRegistry
    from .functions import register_all_functions

    try:
        # Create function registry and register all functions
        registry = FunctionRegistry()
        register_all_functions(registry)

        # Create generator and installer
        generator = CompletionGenerator(registry)
        installer = CompletionInstaller(generator)

        # Get shell from args
        shell = parsed_cmd.args.get("shell") if parsed_cmd.args else None

        # Install completion
        success, message = installer.install(shell)
        print(message)

        if success:
            print("\n🎉 Tab completion is now available!")
            print("   Try: aii tr<TAB>")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"❌ Installation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_uninstall_completion_command(parsed_cmd: Any) -> int:
    """Handle uninstall-completion command"""
    from .cli.completion import CompletionGenerator, CompletionInstaller
    from .core.registry.function_registry import FunctionRegistry
    from .functions import register_all_functions

    try:
        # Create function registry and register all functions
        registry = FunctionRegistry()
        register_all_functions(registry)

        # Create generator and installer
        generator = CompletionGenerator(registry)
        installer = CompletionInstaller(generator)

        # Get shell from args
        shell = parsed_cmd.args.get("shell") if parsed_cmd.args else None

        # Uninstall completion
        success, message = installer.uninstall(shell)
        print(message)

        return 0 if success else 1

    except Exception as e:
        print(f"❌ Uninstallation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_template_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle template commands (v0.4.7)"""
    args = parsed_cmd.args
    template_action = args.get("template_action", "help")

    try:
        from .functions.content.template_functions import TemplateFunction, TemplateListFunction
        from .core.models import ExecutionContext
        from unittest.mock import MagicMock

        # Create execution context
        ctx = MagicMock(spec=ExecutionContext)
        ctx.llm_provider = engine.llm_provider

        if template_action == "list" or template_action == "help":
            # List all templates
            func = TemplateListFunction()
            result = await func.execute({}, ctx)

            if result.success:
                print(result.data["clean_output"])

                if template_action == "help":
                    print("\n📖 Usage Examples:")
                    print("  aii template list                              # List all templates")
                    print("  aii template show product-announcement         # Show template details")
                    print("  aii template use product-announcement \\")
                    print("    --product 'AII' --version 'v0.4.7'          # Generate content")
                    print("\n  Or use natural language:")
                    print('  aii "generate a product announcement for AII v0.4.7"')
                    print('  aii "create a tweet about launching our new feature"')
                return 0
            else:
                print(f"❌ Error: {result.message}")
                return 1

        elif template_action == "show":
            # Show template details
            template_name = args.get("template_name")
            if not template_name:
                print("❌ Error: template name required")
                print("Usage: aii template show <template-name>")
                return 1

            func = TemplateFunction()
            try:
                template = func._load_template(template_name)
                print(f"📝 Template: {template['name']}")
                print(f"Category: {template.get('category', 'general')}")
                print(f"Description: {template['description']}\n")

                variables = template.get('variables', [])
                if variables:
                    print("Required Variables:")
                    for var in variables:
                        req = "✓ required" if var.get('required', False) else "  optional"
                        print(f"  {req}  {var['name']:20s} - {var.get('description', '')}")
                else:
                    print("No variables required")

                print("\n💡 Example Usage:")
                print(f"  aii template use {template_name} \\")
                if variables:
                    # Show example with first variable
                    first_var = variables[0]
                    print(f"    --{first_var['name']} 'your-value-here'")

                return 0
            except FileNotFoundError:
                print(f"❌ Template not found: {template_name}")
                print("\n📋 Available templates:")
                list_func = TemplateListFunction()
                list_result = await list_func.execute({}, ctx)
                if list_result.success:
                    for t in list_result.data['templates']:
                        print(f"  - {t['name']}")
                return 1

        elif template_action == "use":
            # Generate content from template
            template_name = args.get("template_name")
            if not template_name:
                print("❌ Error: template name required")
                print("Usage: aii template use <template-name> [--var key=value]")
                return 1

            # Collect variables from args
            variables = {}

            # Common variables (mapped from argparse names to template variable names)
            arg_to_var_map = {
                "product": "product",
                "version": "version",
                "date": "date",
                "topic": "topic",
                "subject": "subject",
                "recipient": "recipient",
                "title": "title",
                "meeting_title": "meeting_title",
                "key_benefit": "key_benefit",
                "key_features": "key_features",
                "hook": "hook",
                "platform": "platform",
                "cta": "cta",
                "context": "context",
                "hashtags": "hashtags",
            }

            for arg_name, var_name in arg_to_var_map.items():
                if args.get(arg_name):
                    variables[var_name] = args[arg_name]

            # Custom variables from --var
            if args.get("var"):
                for var_pair in args["var"]:
                    if "=" in var_pair:
                        key, value = var_pair.split("=", 1)
                        variables[key.strip()] = value.strip()

            # Execute template function
            result = await engine.execute_function(
                function_name="template",
                parameters={
                    "template_name": template_name,
                    "variables": variables
                }
            )

            # Log execution to database (v0.4.7)
            if engine.chat_storage:
                try:
                    await engine._log_execution(
                        chat_id=engine.context_manager.current_session.chat_id if engine.context_manager.current_session else "cli",
                        function_name="template",
                        parameters={"template_name": template_name, "variables": variables},
                        result=result,
                        success=result.success
                    )
                except Exception as e:
                    # Silent failure to avoid disrupting user experience
                    pass

            if result.success:
                print(result.data["clean_output"])
                return 0
            else:
                print(f"❌ Error: {result.message}")
                return 1

        else:
            print(f"❌ Unknown template action: {template_action}")
            return 1

    except Exception as e:
        print(f"❌ Template command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_stats_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle stats commands (v0.4.7)"""
    args = parsed_cmd.args

    try:
        from .functions.system.stats_functions import StatsFunction
        from .core.models import ExecutionContext
        from unittest.mock import MagicMock

        # Create execution context
        ctx = MagicMock(spec=ExecutionContext)

        # Get parameters from args
        period = args.get("period", "30d")
        breakdown = args.get("breakdown", "all")
        exclude_stats = args.get("exclude_stats", False)

        # Execute stats function
        result = await engine.execute_function(
            function_name="stats",
            parameters={
                "period": period,
                "breakdown": breakdown,
                "exclude_stats": exclude_stats
            }
        )

        # Log execution to database (v0.4.7)
        if engine.chat_storage:
            try:
                await engine._log_execution(
                    chat_id=engine.context_manager.current_session.chat_id if engine.context_manager.current_session else "cli",
                    function_name="stats",
                    parameters={"period": period, "breakdown": breakdown, "exclude_stats": exclude_stats},
                    result=result,
                    success=result.success
                )
            except Exception as e:
                # Silent failure to avoid disrupting user experience
                pass

        if result.success:
            print(result.data["clean_output"])
            return 0
        else:
            print(f"❌ Error: {result.message}")
            return 1

    except Exception as e:
        print(f"❌ Stats command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def handle_mcp_status(args: dict, engine: AIIEngine) -> int:
    """Handle 'aii mcp status' command (v0.4.10)"""
    from .data.integrations.mcp.client_manager import MCPClientManager
    from .data.integrations.mcp.config_loader import MCPConfigLoader
    from .functions.mcp.mcp_management_functions import MCPStatusFunction
    from .core.models import ExecutionContext

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


async def handle_mcp_test(args: dict, engine: AIIEngine) -> int:
    """Handle 'aii mcp test' command (v0.4.10)"""
    from .data.integrations.mcp.client_manager import MCPClientManager
    from .data.integrations.mcp.config_loader import MCPConfigLoader
    from .functions.mcp.mcp_management_functions import MCPTestFunction
    from .core.models import ExecutionContext

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


async def handle_mcp_update(args: dict, engine: AIIEngine) -> int:
    """Handle 'aii mcp update' command (v0.4.10) - supports batch updates"""
    from .functions.mcp.mcp_management_functions import MCPUpdateFunction
    from .core.models import ExecutionContext
    from .data.integrations.mcp.config_loader import MCPConfigLoader

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


async def handle_mcp_list_tools(args: dict, engine: AIIEngine) -> int:
    """Handle 'aii mcp list-tools' command"""
    import json
    from .data.integrations.mcp.client_manager import MCPClientManager
    from .data.integrations.mcp.config_loader import MCPConfigLoader

    server_filter = args.get("server_name")
    detailed = args.get("detailed", False)

    try:
        # Get or create MCP client
        if hasattr(engine, 'mcp_client') and engine.mcp_client:
            mcp_client = engine.mcp_client
        else:
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


async def handle_mcp_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """Handle MCP commands (v0.4.8) - MCP tool operations"""
    import json
    from .data.integrations.mcp.client_manager import MCPClientManager
    from .data.integrations.mcp.config_loader import MCPConfigLoader

    args = parsed_cmd.args
    mcp_action = args.get("mcp_action")

    # Handle server management commands (v0.4.9) - direct function calls (no MCP client needed)
    if mcp_action in ["add", "remove", "list", "enable", "disable", "catalog", "install"]:
        from .functions.mcp.mcp_management_functions import (
            MCPAddFunction,
            MCPRemoveFunction,
            MCPListFunction,
            MCPEnableFunction,
            MCPDisableFunction,
            MCPCatalogFunction,
            MCPInstallFunction,
        )
        from .core.models import ExecutionContext
        from unittest.mock import MagicMock

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
        return await handle_mcp_list_tools(args, engine)

    # Handle status subcommand (v0.4.10)
    if mcp_action == "status":
        return await handle_mcp_status(args, engine)

    # Handle test subcommand (v0.4.10)
    if mcp_action == "test":
        return await handle_mcp_test(args, engine)

    # Handle update subcommand (v0.4.10)
    if mcp_action == "update":
        return await handle_mcp_update(args, engine)

    # Handle invoke subcommand or legacy direct invocation
    if mcp_action == "invoke" or mcp_action is None:
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

        # Get MCP client from engine or create one
        if hasattr(engine, 'mcp_client') and engine.mcp_client:
            mcp_client = engine.mcp_client
        else:
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


async def handle_serve_command(parsed_cmd: Any, engine: AIIEngine) -> int:
    """
    Handle 'serve' command - start API server.

    Args:
        parsed_cmd: Parsed command with args
        engine: AIIEngine instance (not used for serve, creates its own)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from aii.cli.serve import start_api_server

    args = parsed_cmd.args
    host = args.get("host", "0.0.0.0")
    port = args.get("port", 16169)
    api_keys = args.get("api_keys") or []
    verbose = args.get("verbose", False) or args.get("debug", False)

    # Run serve command (async, already in event loop)
    try:
        await start_api_server(host, port, api_keys, verbose)
        return 0
    except KeyboardInterrupt:
        # Graceful shutdown already handled
        return 0
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cli_main() -> int:
    """CLI entry point (synchronous wrapper)"""
    return asyncio.run(main())


if __name__ == "__main__":
    sys.exit(cli_main())
