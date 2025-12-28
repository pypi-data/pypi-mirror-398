# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Interactive setup wizard for AII first-run configuration.

The setup wizard guides users through:
1. Choosing an LLM provider (Anthropic, OpenAI, Gemini)
2. Acquiring and validating an API key
3. Persisting configuration to shell and config files
4. Verifying the setup works

Target: <2 minutes to first successful command.
"""


import asyncio
from dataclasses import dataclass, field
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from aii.cli.setup.steps.base import WizardStep, StepResult


@dataclass
class WizardContext:
    """
    Shared context across wizard steps.

    This context is passed between steps and accumulates configuration
    choices made by the user.
    """
    # Provider selection
    provider: Optional[str] = None  # "anthropic", "openai", "gemini"

    # API key
    api_key: Optional[str] = None
    api_key_env_var: Optional[str] = None  # e.g., "ANTHROPIC_API_KEY"

    # Model selection
    selected_model: Optional[str] = None  # User's chosen model

    # Validation results
    validation_latency_ms: Optional[float] = None
    validation_model: Optional[str] = None

    # Web search configuration
    web_search_provider: Optional[str] = None  # "brave", "google", "duckduckgo"
    web_search_api_key: Optional[str] = None
    web_search_env_var: Optional[str] = None  # e.g., "BRAVE_SEARCH_API_KEY"

    # Persistence
    shell_type: Optional[str] = None  # "bash", "zsh", "fish"
    shell_config_path: Optional[str] = None  # e.g., "~/.bashrc"
    config_dir: str = "~/.aii"

    # State
    cancelled: bool = False
    errors: List[str] = field(default_factory=list)


class SetupWizard:
    """
    Interactive setup wizard for first-run configuration.

    Orchestrates multiple wizard steps to guide the user through
    complete AII setup in <2 minutes.

    Example:
        wizard = SetupWizard()
        success = await wizard.run()
        if success:
            print("Setup complete!")
    """

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the setup wizard.

        Args:
            console: Rich console for output (creates new if None)
        """
        self.console = console or Console()
        self.context = WizardContext()
        self.steps: List[WizardStep] = []
        self._load_steps()

    def _load_steps(self):
        """Load wizard steps in order."""
        from aii.cli.setup.steps.provider_selection import ProviderSelectionStep
        from aii.cli.setup.steps.model_selection import ModelSelectionStep
        from aii.cli.setup.steps.api_key_acquisition import APIKeyAcquisitionStep
        from aii.cli.setup.steps.validation import ValidationStep
        from aii.cli.setup.steps.web_search_setup import WebSearchSetupStep
        from aii.cli.setup.steps.persistence import ConfigPersistenceStep

        self.steps = [
            ProviderSelectionStep(self.console),
            ModelSelectionStep(self.console),
            APIKeyAcquisitionStep(self.console),
            ValidationStep(self.console),
            WebSearchSetupStep(self.console),
            ConfigPersistenceStep(self.console),
        ]

    async def run(self) -> bool:
        """
        Run the setup wizard.

        Returns:
            True if setup completed successfully, False if cancelled or failed
        """
        self._show_welcome()

        try:
            for i, step in enumerate(self.steps, 1):
                self._show_step_header(i, len(self.steps), step.title)

                try:
                    result = await step.execute(self.context)

                    if not result.success:
                        return await self._handle_error(step, result)

                    # Optional: show step completion
                    if result.message:
                        self.console.print(f"✓ {result.message}", style="green")

                except KeyboardInterrupt:
                    return await self._handle_cancel()
                except Exception as e:
                    self.console.print(f"\n❌ Unexpected error: {str(e)}", style="red")
                    self.context.errors.append(str(e))
                    return False

            self._show_success()
            return True

        except KeyboardInterrupt:
            return await self._handle_cancel()

    def _show_welcome(self):
        """Display welcome message."""
        welcome_text = Text()
        welcome_text.append("🚀 Welcome to AII Setup Wizard!\n\n", style="bold cyan")
        welcome_text.append("This will take about 2 minutes. ", style="white")
        welcome_text.append("Press Ctrl+C to cancel anytime.\n", style="dim")

        self.console.print(Panel(welcome_text, border_style="cyan"))
        self.console.print()

    def _show_step_header(self, current: int, total: int, title: str):
        """Display step header box."""
        step_text = f"Step {current} of {total}: {title}"
        self.console.print()
        self.console.print("╭" + "─" * 57 + "╮")
        self.console.print(f"│ {step_text:<55} │")
        self.console.print("╰" + "─" * 57 + "╯")
        self.console.print()

    async def _handle_error(self, step: WizardStep, result: StepResult) -> bool:
        """
        Handle step failure.

        Args:
            step: The step that failed
            result: The step result with error details

        Returns:
            False (setup failed)
        """
        self.console.print(f"\n❌ {result.message}", style="red")

        if result.fix_suggestion:
            self.console.print(f"\n💡 {result.fix_suggestion}", style="yellow")

        self.context.errors.append(result.message)

        # Ask if user wants to retry or cancel
        try:
            retry = input("\nRetry this step? (y/n): ").lower().strip()
            if retry == 'y':
                return await self._retry_step(step)
        except (EOFError, KeyboardInterrupt):
            # User cancelled during retry prompt or EOF
            return await self._handle_cancel()

        return False

    async def _retry_step(self, step: WizardStep) -> bool:
        """
        Retry a failed step.

        Args:
            step: The step to retry

        Returns:
            True if retry succeeded, False otherwise
        """
        try:
            result = await step.execute(self.context)
            if result.success:
                if result.message:
                    self.console.print(f"✓ {result.message}", style="green")
                return True
            else:
                self.console.print(f"\n❌ Retry failed: {result.message}", style="red")
                return False
        except Exception as e:
            self.console.print(f"\n❌ Retry failed: {str(e)}", style="red")
            return False

    async def _handle_cancel(self) -> bool:
        """
        Handle user cancellation.

        Returns:
            False (setup cancelled)
        """
        self.console.print("\n\n⏸️  Setup cancelled.", style="yellow")
        self.console.print("\nYou can run this wizard again anytime with:", style="dim")
        self.console.print("  aii config init", style="cyan")
        self.console.print("\nFor manual setup instructions:", style="dim")
        self.console.print("  https://docs.aii.dev/setup\n", style="cyan")

        self.context.cancelled = True
        return False

    def _show_success(self):
        """Display success message with next steps."""
        success_text = Text()
        success_text.append("🎉 Setup complete!\n\n", style="bold green")

        # Show configuration summary
        success_text.append("Configuration saved to:\n", style="bold")

        # Shell config
        if self.context.shell_config_path:
            success_text.append(f"  • Shell: ", style="dim")
            success_text.append(f"{self.context.shell_config_path}\n", style="cyan")

        # AII config
        success_text.append(f"  • AII Config: ", style="dim")
        success_text.append(f"{self.context.config_dir}/config.yaml\n", style="cyan")
        success_text.append(f"  • API Key: ", style="dim")
        success_text.append(f"{self.context.config_dir}/secrets.yaml ✓\n", style="green")

        # Provider info
        success_text.append(f"\n  • Provider: ", style="dim")
        success_text.append(f"{self.context.provider}\n", style="cyan")
        success_text.append(f"  • Model: ", style="dim")
        success_text.append(f"{self.context.validation_model or 'default'}\n", style="cyan")

        if self.context.validation_latency_ms:
            success_text.append(f"  • Latency: ", style="dim")
            success_text.append(f"{self.context.validation_latency_ms:.0f}ms\n", style="cyan")

        self.console.print(Panel(success_text, border_style="green", title="Success"))

        # v0.6.0: Restart server if running to pick up new config
        self.console.print("\n⚠️  Important:", style="bold yellow")
        self.console.print("  If Aii server is running, restart it to apply changes:", style="yellow")
        self.console.print("  aii serve restart", style="cyan bold")

        # Next steps
        self.console.print("\n📚 Try your first command:", style="bold")
        self.console.print("  aii translate \"Hello world\" --to spanish", style="cyan")

        self.console.print("\n💡 Other commands to try:", style="bold")
        self.console.print("  aii research \"latest AI trends\"", style="dim")
        self.console.print("  aii commit", style="dim")
        self.console.print("  aii explain \"how LLMs work\"", style="dim")

        self.console.print("\n🔧 Need help?", style="bold")
        self.console.print("  aii doctor     — Health check", style="dim")
        self.console.print("  aii --help     — Show all commands", style="dim")
        self.console.print("  aii            — Interactive mode", style="dim")
        self.console.print()
