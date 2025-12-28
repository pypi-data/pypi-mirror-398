# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Configuration Manager for AII CLI"""


import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from aii.data.providers.model_migration import migrate_model_if_needed


class ConfigManager:
    """Manage AII configuration files and settings"""

    def __init__(self, config_dir: Path | None = None):
        """Initialize configuration manager"""
        if config_dir is None:
            config_dir = Path.home() / ".aii"

        self.config_dir = config_dir
        self.config_file = config_dir / "config.yaml"
        self.secrets_file = config_dir / "secrets.yaml"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._default_config = {
            "llm": {
                "provider": None,  # User must choose: anthropic, openai, or gemini
                "model": None,  # Set during config init based on chosen provider
                "temperature": 0.7,
                "max_tokens": 2000,
                "use_subscription": False,  # EXPERIMENTAL: OAuth subscription authentication (not used in main flow)
            },
            "web_search": {
                "enabled": True,
                "provider": "duckduckgo",  # Free provider, no API key required
                "max_results": 5,
                "cache_enabled": True,
                "cache_size": 100,
                "cache_ttl_seconds": 3600,  # 1 hour
                "rate_limit_seconds": 1.0,
            },
            "mcp": {
                "servers": [],
                "timeout": 30,
                "retries": 3,
                "signature": {  # v0.4.10: AII signature for generated content
                    "enabled": True,
                    "style": "full",  # full, minimal, or none
                    "overrides": {},  # Per-function overrides
                },
            },
            "chat": {
                "default_context_limit": 20,
                "auto_save": True,
                "auto_archive_after_days": 30,
            },
            "functions": {
                "git": {"enabled": True, "auto_stage": False},
                "translation": {"enabled": True, "default_target": "auto"},
                "code": {"enabled": True, "max_file_size_kb": 100},
                "analysis": {"enabled": True, "web_research": True},
            },
            "security": {
                "confirm_dangerous_operations": True,
                "sanitize_inputs": True,
                "max_input_length": 10000,
            },
            "ui": {
                "color": True,
                "emoji": True,
                "progress_bars": True,
            },
            "streaming": {
                "enabled": True,
                "buffer_size": 10,
                "flush_interval": 0.05,  # 50ms
                "show_cursor": True,
                "enable_markdown": True,
            },
            "output_modes": {
                "default": "standard",  # Global default: clean, standard, thinking
                "overrides": {
                    # Per-function output mode overrides
                    # Examples:
                    # "translate": "clean",
                    # "explain": "clean",
                    # "git_commit": "thinking",
                },
            },
            "video_extraction": {
                "enabled": True,
                "mode": "adaptive",  # adaptive (adjust FPS to maintain cost) or fixed_rate (fixed FPS, limit frames)
                "fps": 1.0,  # Target frames per second (adaptive mode may adjust this)
                "max_frames": 300,  # Hard limit on total frames
                "hard_cost_limit": 1.00,  # Maximum cost in USD ($1.00 default)
                "tokens_per_frame": 1000,  # Estimated tokens per frame (high-detail images)
            },
        }

        self._config: dict[str, Any] = {}
        self._secrets: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from files"""
        # Load main config
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                self._config = {}
        else:
            self._config = {}

        # Merge with defaults (deep copy to avoid modifying defaults)
        import copy

        self._config = self._deep_merge(
            copy.deepcopy(self._default_config), self._config
        )

        # Load secrets
        if self.secrets_file.exists():
            try:
                with open(self.secrets_file, encoding="utf-8") as f:
                    self._secrets = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load secrets: {e}")
                self._secrets = {}

        # Set restrictive permissions on secrets file
        if self.secrets_file.exists():
            os.chmod(self.secrets_file, 0o600)

        # v0.9.3: Check for deprecated models and auto-migrate
        self._migrate_deprecated_model()

    def _deep_merge(self, default: dict, override: dict) -> dict:
        """Deep merge two dictionaries"""
        result = default.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path"""
        keys = path.split(".")
        value = self._config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, path: str, value: Any, save: bool = True) -> None:
        """Set configuration value by dot-separated path"""
        keys = path.split(".")
        config = self._config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

        if save:
            self.save_config()

    def get_secret(self, key: str, default: Any = None) -> Any:
        """Get secret value (API keys, tokens, etc.)"""
        # First try environment variable with AII_ prefix
        env_key = f"AII_{key.upper().replace('.', '_')}"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value

        # Also try standard env var names without AII_ prefix (for compatibility)
        # e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
        standard_env_key = key.upper().replace('.', '_')
        env_value = os.getenv(standard_env_key)
        if env_value:
            return env_value

        # Finally try secrets file
        return self._secrets.get(key, default)

    def set_secret(self, key: str, value: str, save: bool = True) -> None:
        """Set secret value"""
        self._secrets[key] = value

        if save:
            self.save_secrets()

    def _migrate_deprecated_model(self) -> None:
        """
        Check if configured model is deprecated and auto-migrate to replacement.

        v0.9.3: Auto-migration for deprecated models (gpt-3.5-turbo, claude-3-*, etc.)
        """
        configured_model = self.get("llm.model")

        if not configured_model:
            # No model configured yet, nothing to migrate
            return

        # Check if migration is needed
        migrated_model = migrate_model_if_needed(configured_model, warn=True)

        if migrated_model != configured_model:
            # Model was migrated, update config
            self.set("llm.model", migrated_model, save=True)
            print(f"✅ Configuration updated: {configured_model} → {migrated_model}\n")

    def get_output_mode(self, function_name: str) -> str | None:
        """
        Get configured output mode for a function.

        Returns:
            Output mode string ("clean", "standard", "thinking") or None if not configured

        Priority: function override > global default > None (let function default work)
        """
        # Check function-specific override
        overrides = self.get("output_modes.overrides", {})
        if function_name in overrides:
            return overrides[function_name]

        # Check global default (but return None to let function defaults work)
        # Only return global default if explicitly set to non-"standard"
        global_default = self.get("output_modes.default", "standard")
        if global_default != "standard":
            return global_default

        # Return None to let function default take precedence
        return None

    def get_video_extraction_config(self) -> dict[str, Any]:
        """
        Get video extraction configuration.

        Returns:
            Dictionary with video extraction settings (mode, fps, max_frames, etc.)
        """
        return {
            "enabled": self.get("video_extraction.enabled", True),
            "mode": self.get("video_extraction.mode", "adaptive"),
            "fps": self.get("video_extraction.fps", 1.0),
            "max_frames": self.get("video_extraction.max_frames", 300),
            "hard_cost_limit": self.get("video_extraction.hard_cost_limit", 1.00),
            "tokens_per_frame": self.get("video_extraction.tokens_per_frame", 1000),
        }

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._config,
                    f,
                    default_flow_style=False,
                    sort_keys=True,
                    indent=2,
                )
        except Exception as e:
            raise RuntimeError(f"Failed to save config: {e}") from e

    def save_secrets(self) -> None:
        """Save secrets to file with secure permissions"""
        try:
            with open(self.secrets_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._secrets,
                    f,
                    default_flow_style=False,
                    sort_keys=True,
                    indent=2,
                )
            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)
        except Exception as e:
            raise RuntimeError(f"Failed to save secrets: {e}") from e

    def init_config(self, interactive: bool = True) -> None:
        """Initialize configuration interactively"""
        print("🚀 Setting up AII CLI configuration...\n")

        if interactive:
            self._setup_llm_provider()
            self._setup_web_search()
            self._setup_preferences()
        else:
            # Create default config
            self._config = self._default_config.copy()

        self.save_config()
        self.save_secrets()  # Save secrets to file
        print(f"✅ Configuration saved to {self.config_file}")

    def _setup_llm_provider(self) -> None:
        """Interactively setup LLM provider"""
        print("1. LLM Provider Configuration")
        print("   Available providers: gemini, openai, anthropic, local")

        provider = input("   Choose provider (gemini): ").strip() or "gemini"
        self.set("llm.provider", provider, save=False)

        if provider == "gemini":
            model = input("   Model (gemini-2.0-flash): ").strip() or "gemini-2.0-flash"
            self.set("llm.model", model, save=False)

            api_key = input(
                "   Gemini API key (leave empty to use environment): "
            ).strip()
            if api_key:
                self.set_secret("gemini_api_key", api_key, save=False)

        elif provider == "openai":
            model = input("   Model (gpt-4): ").strip() or "gpt-4"
            self.set("llm.model", model, save=False)

            api_key = input(
                "   OpenAI API key (leave empty to use environment): "
            ).strip()
            if api_key:
                self.set_secret("openai_api_key", api_key, save=False)

        elif provider == "anthropic":
            model = (
                input("   Model (claude-sonnet-4-5-20250929): ").strip()
                or "claude-sonnet-4-5-20250929"
            )
            self.set("llm.model", model, save=False)

            # Ask about authentication method
            print("   Authentication options:")
            print("   1. API key (pay-per-token)")
            print("   2. Subscription (Pro/Max plans)")
            auth_choice = input("   Choose authentication (1): ").strip() or "1"

            if auth_choice == "2":
                self.set("llm.use_subscription", True, save=False)
                print("   ✓ Subscription authentication enabled")
                print("   To complete setup, run: aii config oauth login")
                print("   This will authenticate you with your Claude Pro/Max account.")
            else:
                self.set("llm.use_subscription", False, save=False)
                api_key = input(
                    "   Anthropic API key (leave empty to use environment): "
                ).strip()
                if api_key:
                    self.set_secret("anthropic_api_key", api_key, save=False)

        elif provider == "local":
            model_path = input("   Local model path: ").strip()
            if model_path:
                self.set("llm.model", model_path, save=False)

        print("   ✓ LLM provider configured\n")

    def _setup_web_search(self) -> None:
        """Interactively setup web search"""
        print("2. Web Search Configuration")
        enabled = input("   Enable web search? (y/n): ").strip().lower()
        self.set("web_search.enabled", enabled in ("y", "yes", "true"), save=False)

        if enabled in ("y", "yes", "true"):
            provider = input("   Search provider (brave): ").strip() or "brave"
            self.set("web_search.provider", provider, save=False)

            if provider == "brave":
                api_key = input(
                    "   Brave Search API key (leave empty to skip): "
                ).strip()
                if api_key:
                    self.set_secret("brave_api_key", api_key, save=False)

            elif provider == "google":
                api_key = input("   Google API key: ").strip()
                search_engine_id = input("   Search Engine ID: ").strip()
                if api_key and search_engine_id:
                    self.set_secret("google_api_key", api_key, save=False)
                    self.set_secret(
                        "google_search_engine_id", search_engine_id, save=False
                    )

        print("   ✓ Web search configured\n")

    def _setup_preferences(self) -> None:
        """Setup user preferences"""
        print("3. User Preferences")

        # Chat settings
        auto_save = input("   Auto-save chat sessions? (y): ").strip() or "y"
        self.set(
            "chat.auto_save", auto_save.lower() in ("y", "yes", "true"), save=False
        )

        context_limit = input("   Chat context limit (20): ").strip()
        if context_limit.isdigit():
            self.set("chat.default_context_limit", int(context_limit), save=False)

        # UI preferences
        use_color = input("   Use colored output? (y): ").strip() or "y"
        self.set("ui.color", use_color.lower() in ("y", "yes", "true"), save=False)

        use_emoji = input("   Use emoji in output? (y): ").strip() or "y"
        self.set("ui.emoji", use_emoji.lower() in ("y", "yes", "true"), save=False)

        print("   ✓ Preferences configured\n")

    def validate_config(self) -> list[str]:
        """Validate current configuration and return any issues"""
        issues = []

        # Check LLM provider
        provider = self.get("llm.provider")
        if provider == "gemini" and not self.get_secret("gemini_api_key"):
            issues.append("Gemini API key not configured")
        elif provider == "openai" and not self.get_secret("openai_api_key"):
            issues.append("OpenAI API key not configured")
        elif provider == "anthropic":
            use_subscription = self.get("llm.use_subscription", False)
            if use_subscription:
                # Check for aii OAuth credentials
                auth_creds = Path.home() / ".aii" / "auth" / "claude_oauth_credentials.json"
                if not auth_creds.exists():
                    issues.append("Subscription authentication enabled but no OAuth credentials found. Run 'aii config oauth login' to authenticate.")
            elif not self.get_secret("anthropic_api_key"):
                issues.append("Anthropic API key not configured")

        # Check web search
        if self.get("web_search.enabled"):
            search_provider = self.get("web_search.provider")
            if search_provider == "brave" and not self.get_secret("brave_api_key"):
                issues.append(
                    "Brave Search API key not configured (web search disabled)"
                )
            elif search_provider == "google":
                if not self.get_secret("google_api_key"):
                    issues.append("Google API key not configured")
                if not self.get_secret("google_search_engine_id"):
                    issues.append("Google Search Engine ID not configured")

        return issues

    def get_all_config(self) -> dict[str, Any]:
        """Get all configuration (excluding secrets)"""
        return self._config.copy()

    def export_config(self, include_secrets: bool = False) -> dict[str, Any]:
        """Export configuration for backup/sharing"""
        config = self._config.copy()

        if include_secrets:
            config["secrets"] = self._secrets.copy()

        return config

    def import_config(self, config_data: dict[str, Any], merge: bool = True) -> None:
        """Import configuration from data"""
        secrets = config_data.pop("secrets", {})

        if merge:
            self._config = self._deep_merge(self._config, config_data)
            self._secrets.update(secrets)
        else:
            self._config = config_data
            self._secrets = secrets

        self.save_config()
        if secrets:
            self.save_secrets()

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        import copy

        self._config = copy.deepcopy(self._default_config)
        self.save_config()

    def backup_config(self, backup_path: Path | None = None) -> Path:
        """Create a backup of current configuration"""
        if backup_path is None:
            backup_path = (
                self.config_dir / f"backup_{int(datetime.now().timestamp())}.yaml"
            )

        backup_data = self.export_config(include_secrets=True)

        with open(backup_path, "w", encoding="utf-8") as f:
            yaml.dump(backup_data, f, default_flow_style=False, indent=2)

        # Set restrictive permissions if secrets are included
        os.chmod(backup_path, 0o600)

        return backup_path


# Global configuration instance
_config_manager: ConfigManager | None = None


def get_config() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config_dir: Path | None = None) -> ConfigManager:
    """Initialize global configuration manager"""
    global _config_manager
    _config_manager = ConfigManager(config_dir)
    return _config_manager
