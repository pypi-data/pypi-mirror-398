# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Configuration persistence step for setup wizard.

Saves API key to shell config and AII config files.
"""


import os
from pathlib import Path
from typing import Any, Optional

from aii.cli.setup.steps.base import WizardStep, StepResult
from aii.config.manager import ConfigManager


class ConfigPersistenceStep(WizardStep):
    """
    Step 4: Save Configuration.

    Saves API key to:
    1. Shell config file (e.g., ~/.bashrc)
    2. AII config files (~/.aii/)
    """

    title = "Save Configuration"

    async def execute(self, context: Any) -> StepResult:
        """
        Save configuration to shell and AII config.

        Args:
            context: WizardContext with all configuration

        Returns:
            StepResult with success=True if saved successfully
        """
        if not context.provider or not context.api_key or not context.api_key_env_var:
            return StepResult(
                success=False,
                message="Missing configuration data",
                fix_suggestion="This is a bug - previous steps should have set these"
            )

        self.console.print("Where should I save the API key environment variable?\n", style="bold")
        self.console.print("(Note: AII config will be saved to ~/.aii/ automatically)\n", style="dim")

        # Detect shell and show options
        detected_shell = self._detect_shell()
        shell_options = self._get_save_options(detected_shell)

        # Display options
        for i, option in enumerate(shell_options, 1):
            recommended = " ← Recommended" if option["recommended"] else ""
            self.console.print(
                f"  {i}. {option['label']}{recommended}",
                style="cyan" if option["recommended"] else "dim"
            )

        # Get user choice
        choice_idx = self._prompt_choice(
            "\nEnter choice [1-4]",
            choices=["1", "2", "3", "4"],
            default="1"
        )

        selected_option = shell_options[int(choice_idx) - 1]

        # Save to shell config (unless temporary)
        if selected_option["path"] != "temporary":
            # Save LLM API key
            shell_result = self._save_to_shell_config(
                selected_option["path"],
                context.api_key_env_var,
                context.api_key
            )
            if not shell_result.success:
                return shell_result

            # Save web search API key if configured
            if context.web_search_api_key and context.web_search_env_var:
                web_result = self._save_to_shell_config(
                    selected_option["path"],
                    context.web_search_env_var,
                    context.web_search_api_key
                )
                if not web_result.success:
                    self.console.print(
                        "⚠️  Warning: Failed to save web search key to shell config",
                        style="yellow"
                    )

            context.shell_type = selected_option["shell_type"]
            context.shell_config_path = selected_option["path"]

            self.console.print(
                f"\n✓ Configuration saved to {selected_option['path']}",
                style="green"
            )
            self.console.print(
                f"\nTo activate now, run: source {selected_option['path']}",
                style="yellow"
            )
            self.console.print("(Or just start a new terminal)\n", style="dim")
        else:
            # Temporary: just set for current session
            os.environ[context.api_key_env_var] = context.api_key
            if context.web_search_api_key and context.web_search_env_var:
                os.environ[context.web_search_env_var] = context.web_search_api_key
            self.console.print(
                "\n✓ API keys set for this session only (not persistent)",
                style="yellow"
            )

        # Save to AII config files
        config_result = self._save_aii_config(context)
        if not config_result.success:
            return config_result

        return StepResult(
            success=True,
            message="Configuration saved successfully",
            data={
                "shell_config": context.shell_config_path,
                "aii_config": context.config_dir
            }
        )

    def _detect_shell(self) -> str:
        """
        Detect user's current shell.

        Returns:
            Shell name ("bash", "zsh", "fish", "unknown")
        """
        shell_path = os.environ.get("SHELL", "")
        if "bash" in shell_path:
            return "bash"
        elif "zsh" in shell_path:
            return "zsh"
        elif "fish" in shell_path:
            return "fish"
        else:
            return "unknown"

    def _get_save_options(self, detected_shell: str) -> list[dict]:
        """
        Get shell config save options.

        Args:
            detected_shell: Detected shell name

        Returns:
            List of option dicts with path, label, recommended flag
        """
        home = str(Path.home())

        options = [
            {
                "path": f"{home}/.bashrc",
                "label": "~/.bashrc (bash shell)",
                "shell_type": "bash",
                "recommended": detected_shell == "bash"
            },
            {
                "path": f"{home}/.zshrc",
                "label": "~/.zshrc (zsh shell)",
                "shell_type": "zsh",
                "recommended": detected_shell == "zsh"
            },
            {
                "path": f"{home}/.config/fish/config.fish",
                "label": "~/.config/fish/config.fish (fish shell)",
                "shell_type": "fish",
                "recommended": detected_shell == "fish"
            },
            {
                "path": "temporary",
                "label": "Just this session (temporary)",
                "shell_type": "temporary",
                "recommended": False
            }
        ]

        # If we detected a shell, move it to the top
        if detected_shell != "unknown":
            for option in options:
                if option["shell_type"] == detected_shell:
                    options.remove(option)
                    options.insert(0, option)
                    break

        return options

    def _save_to_shell_config(self, config_path: str, env_var: str, api_key: str) -> StepResult:
        """
        Append API key export to shell config file.

        Args:
            config_path: Path to shell config file
            env_var: Environment variable name
            api_key: API key value

        Returns:
            StepResult indicating success/failure
        """
        try:
            path = Path(config_path).expanduser()

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check if already configured
            if path.exists():
                content = path.read_text()
                if env_var in content:
                    # Already configured, skip
                    return StepResult(
                        success=True,
                        message=f"{env_var} already set in {config_path}"
                    )

            # Append export line
            export_line = f'\nexport {env_var}="{api_key}"\n'

            with path.open('a') as f:
                f.write(export_line)

            return StepResult(success=True)

        except PermissionError:
            return StepResult(
                success=False,
                message=f"Permission denied writing to {config_path}",
                fix_suggestion="Please check file permissions or choose a different location"
            )
        except Exception as e:
            return StepResult(
                success=False,
                message=f"Failed to write to shell config: {str(e)}",
                fix_suggestion="You can manually add the API key to your shell config"
            )

    def _save_aii_config(self, context: Any) -> StepResult:
        """
        Save configuration to AII config files.

        Args:
            context: WizardContext

        Returns:
            StepResult indicating success/failure
        """
        try:
            # Create config directory
            config_dir = Path(context.config_dir).expanduser()
            config_dir.mkdir(parents=True, exist_ok=True)

            # Use ConfigManager to save configuration
            config_manager = ConfigManager()

            # Set provider and model
            config_manager.set("llm.provider", context.provider, save=False)

            # Use selected model if available, otherwise use default
            model = context.selected_model or self._get_default_model(context.provider)
            config_manager.set("llm.model", model, save=False)

            # Configure web search if set up
            if context.web_search_provider:
                config_manager.set("web_search.enabled", True, save=False)
                config_manager.set("web_search.provider", context.web_search_provider, save=False)

            config_manager.save_config()

            # Save LLM API key to secrets
            config_manager.set_secret(context.api_key_env_var.lower(), context.api_key)

            # Save web search API key if provided
            if context.web_search_api_key and context.web_search_env_var:
                config_manager.set_secret(context.web_search_env_var.lower(), context.web_search_api_key)

            self.console.print(
                f"✓ Configuration saved to {config_dir}",
                style="green"
            )

            return StepResult(success=True)

        except Exception as e:
            return StepResult(
                success=False,
                message=f"Failed to save AII config: {str(e)}",
                fix_suggestion="You may need to configure AII manually"
            )

    def _get_default_model(self, provider: str) -> str:
        """
        Get default model for provider.

        Args:
            provider: Provider name

        Returns:
            Default model string
        """
        defaults = {
            "anthropic": "claude-sonnet-4-5-20250929",
            "openai": "gpt-5",
            "gemini": "gemini-2.5-flash"
        }
        return defaults.get(provider, "")
