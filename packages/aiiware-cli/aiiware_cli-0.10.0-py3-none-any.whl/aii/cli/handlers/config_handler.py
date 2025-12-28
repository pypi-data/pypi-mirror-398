# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Configuration command handler for AII CLI (v0.6.0).

Handles all configuration-related commands:
- config init
- config show
- config model
- config provider
- config web-search
- config set
- config validate
- config reset
- config backup
- config oauth (login, logout, status)
"""


import sys
from pathlib import Path
from typing import Any

from ...config.manager import get_config
from ...cli.command_router import CommandRoute


async def handle_config_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle configuration commands.

    Args:
        route: CommandRoute with command/subcommand/args
        config_manager: ConfigManager instance
        output_config: OutputConfig instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = route.args
    config_action = args.get("config_action")

    try:
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
            return await _handle_config_show(config_manager)

        elif config_action == "validate":
            return await _handle_config_validate(config_manager)

        elif config_action == "reset":
            return await _handle_config_reset(config_manager)

        elif config_action == "backup":
            return await _handle_config_backup(config_manager)

        elif config_action == "set":
            return await _handle_config_set(args, config_manager)

        elif config_action == "model":
            return await _handle_config_model(args, config_manager)

        elif config_action == "provider":
            return await _handle_config_provider(args, config_manager)

        elif config_action == "web-search":
            return await _handle_config_web_search(args, config_manager)

        elif config_action == "oauth":
            return await handle_oauth_command(args, config_manager)

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


async def _handle_config_show(config_manager: Any) -> int:
    """Show current configuration."""
    print("📋 Current AII Configuration:")
    print(f"- Config file: {config_manager.config_file}")

    # Get storage path from config
    storage_path = Path.home() / ".aii"
    print(f"- Storage path: {storage_path}")

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

    # Validation
    issues = config_manager.validate_config()
    if issues:
        print(f"- Configuration issues: {len(issues)}")

    return 0


async def _handle_config_validate(config_manager: Any) -> int:
    """Validate configuration."""
    issues = config_manager.validate_config()
    if issues:
        print("❌ Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    else:
        print("✅ Configuration is valid!")
        return 0


async def _handle_config_reset(config_manager: Any) -> int:
    """Reset configuration to defaults."""
    confirm = input(
        "Are you sure you want to reset configuration to defaults? (y/N): "
    )
    if confirm.lower() in ("y", "yes"):
        config_manager.reset_to_defaults()
        print("✅ Configuration reset to defaults")
        return 0
    else:
        print("Reset cancelled")
        return 0


async def _handle_config_backup(config_manager: Any) -> int:
    """Create configuration backup."""
    backup_path = config_manager.backup_config()
    print(f"✅ Configuration backed up to: {backup_path}")
    return 0


async def _handle_config_set(args: dict, config_manager: Any) -> int:
    """Set configuration value."""
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
            # Get available models for validation (v0.9.3: use model_registry)
            from aii.data.providers.model_registry import get_models_for_provider, get_model_metadata
            provider = config_manager.get("llm.provider", "anthropic")
            valid_model_ids = get_models_for_provider(provider)

            if valid_model_ids and value not in valid_model_ids:
                print(f"⚠️  Warning: '{value}' is not in the list of recommended models for {provider}")
                print(f"\n📋 Available {provider} models:")
                for model_id in valid_model_ids:
                    metadata = get_model_metadata(provider, model_id)
                    display_name = metadata.get("display_name", model_id)
                    print(f"  - {model_id} ({display_name})")

                # Ask for confirmation
                confirm = input("\n❓ Continue anyway? (y/N): ").strip().lower()
                if confirm not in ['y', 'yes']:
                    print("❌ Model change cancelled")
                    return 1

        elif key == "llm.provider":
            valid_providers = ["anthropic", "openai", "gemini", "moonshot", "deepseek"]
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

        return 0

    except Exception as e:
        print(f"❌ Failed to set configuration: {e}")
        return 1


async def _handle_config_model(args: dict, config_manager: Any) -> int:
    """Change LLM model."""
    model_id = args.get("model_id")

    if not model_id:
        # Show current model and available options (v0.9.3: use model_registry)
        from aii.data.providers.model_registry import get_models_for_provider, get_model_metadata
        from aii.cli.setup.steps.model_selection import ModelSelectionStep
        provider = config_manager.get("llm.provider", "anthropic")
        current_model = config_manager.get("llm.model")

        print(f"📋 Current model: {current_model}")
        print(f"\n✨ Available {provider} models:")

        step = ModelSelectionStep()
        available_models = get_models_for_provider(provider)
        recommended_default = step.RECOMMENDED_DEFAULTS.get(provider)

        if available_models:
            for model_id in available_models:
                metadata = get_model_metadata(provider, model_id)
                display_name = metadata.get("display_name", model_id)
                description = metadata.get("description", "")

                marker = " ✓ (recommended)" if model_id == recommended_default else ""
                current = " ← current" if model_id == current_model else ""
                print(f"  {display_name}{marker}{current}")
                print(f"    {description}")
                print(f"    ID: {model_id}\n")

        print("Usage: aii config model <model_id>")
        print("\n💡 Tip: You can also use custom model IDs not listed above")
        return 0

    # Set the model using the existing set logic (v0.9.3: use model_registry)
    try:
        from aii.data.providers.model_registry import get_models_for_provider
        provider = config_manager.get("llm.provider", "anthropic")
        valid_model_ids = get_models_for_provider(provider)

        if valid_model_ids and model_id not in valid_model_ids:
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


async def _handle_config_provider(args: dict, config_manager: Any) -> int:
    """Change LLM provider."""
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
        print("  4. moonshot  - Moonshot AI (Long context up to 256K)")
        print("  5. deepseek  - DeepSeek AI (Ultra low cost)")
        print("\nUsage: aii config provider <provider_name>")
        print("\n⚠️  Note: Changing provider may require setting a new model")
        return 0

    # Validate provider
    valid_providers = ["anthropic", "openai", "gemini", "moonshot", "deepseek"]
    if provider_name not in valid_providers:
        print(f"❌ Error: Invalid provider '{provider_name}'")
        print(f"Valid providers: {', '.join(valid_providers)}")
        return 1

    # Get default model for new provider (v0.9.3: use model_registry)
    from aii.cli.setup.steps.model_selection import ModelSelectionStep
    step = ModelSelectionStep()
    default_model = step.RECOMMENDED_DEFAULTS.get(provider_name, "")

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


async def _handle_config_web_search(args: dict, config_manager: Any) -> int:
    """Configure web search."""
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

    else:
        print(f"❌ Unknown action: {action}")
        return 1


async def handle_oauth_command(args: dict, config_manager: Any) -> int:
    """Handle OAuth authentication commands."""
    oauth_action = args.get("oauth_action")

    try:
        from aii.auth.claude_oauth import ClaudeOAuthClient

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
