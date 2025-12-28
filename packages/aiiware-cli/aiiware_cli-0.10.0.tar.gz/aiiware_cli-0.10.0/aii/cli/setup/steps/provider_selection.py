# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Provider selection step for setup wizard.

Presents user with LLM provider choices (Anthropic, OpenAI, Gemini)
and captures their selection.
"""


from typing import Any
from rich.table import Table
from rich.text import Text

from aii.cli.setup.steps.base import WizardStep, StepResult


class ProviderSelectionStep(WizardStep):
    """
    Step 1: Choose AI Provider.

    Displays provider comparison and captures user choice.
    Updates context.provider and context.api_key_env_var.
    """

    title = "Choose AI Provider"

    # Common rating strings for consistency
    SPEED_FAST = "⚡⚡ Fast"
    SPEED_VERY_FAST = "⚡⚡⚡ Very fast"
    RELIABILITY_EXCELLENT = "⭐⭐⭐⭐⭐ Excellent"
    RELIABILITY_GREAT = "⭐⭐⭐⭐ Great"

    PROVIDERS = {
        "1": {
            "name": "Anthropic Claude",
            "key": "anthropic",
            "emoji": "🤖",
            "best_for": "Most use cases",
            "speed": SPEED_VERY_FAST,
            "pricing": "Free credits, then pay-as-you-go",
            "reliability": RELIABILITY_EXCELLENT,
            "env_var": "ANTHROPIC_API_KEY",
        },
        "2": {
            "name": "OpenAI GPT",
            "key": "openai",
            "emoji": "🧠",
            "best_for": "Familiar interface",
            "speed": SPEED_FAST,
            "pricing": "$5 free credits for new accounts",
            "reliability": RELIABILITY_GREAT,
            "env_var": "OPENAI_API_KEY",
        },
        "3": {
            "name": "Google Gemini",
            "key": "gemini",
            "emoji": "✨",
            "best_for": "Budget-conscious",
            "speed": SPEED_FAST,
            "pricing": "Very generous free tier",
            "reliability": RELIABILITY_GREAT,
            "env_var": "GEMINI_API_KEY",
        },
        "4": {
            "name": "Moonshot AI",
            "key": "moonshot",
            "emoji": "🌙",
            "best_for": "Long context (up to 256K with Kimi K2)",
            "speed": SPEED_FAST,
            "pricing": "$0.20-8.00 per 1M tokens",
            "reliability": RELIABILITY_GREAT,
            "env_var": "MOONSHOT_API_KEY",
        },
        "5": {
            "name": "DeepSeek AI",
            "key": "deepseek",
            "emoji": "🔍",
            "best_for": "Ultra low cost (10x cheaper than GPT-4)",
            "speed": SPEED_FAST,
            "pricing": "$0.14-0.56 per 1M tokens",
            "reliability": RELIABILITY_GREAT,
            "env_var": "DEEPSEEK_API_KEY",
        },
    }

    async def execute(self, context: Any) -> StepResult:
        """
        Display provider options and capture selection.

        Args:
            context: WizardContext

        Returns:
            StepResult with success=True if valid selection made
        """
        # Build choices for interactive menu with detailed descriptions
        menu_choices = []
        for choice_num, info in self.PROVIDERS.items():
            # Create multi-line description with all details
            provider_desc = (
                f"{info['emoji']} {info['name']} (Recommended)" if choice_num == "1"
                else f"{info['emoji']} {info['name']}"
            )
            provider_desc += f"\n     • Best for: {info['best_for']}"
            provider_desc += f"\n     • Speed: {info['speed']}"
            provider_desc += f"\n     • Pricing: {info['pricing']}"
            provider_desc += f"\n     • Reliability: {info['reliability']}"
            menu_choices.append((choice_num, provider_desc))

        # Use interactive menu with arrow keys (default to first option - Anthropic)
        choice = self._interactive_menu(
            "Which provider would you like to use?",
            menu_choices,
            default_index=0  # Anthropic is recommended
        )

        if choice == "q":
            return StepResult(
                success=False,
                message="Setup cancelled by user"
            )

        # Update context
        provider_info = self.PROVIDERS[choice]
        context.provider = provider_info["key"]
        context.api_key_env_var = provider_info["env_var"]

        self.console.print(
            f"\n✓ You chose: {provider_info['emoji']} {provider_info['name']}",
            style="green bold"
        )

        return StepResult(
            success=True,
            message=f"Selected {provider_info['name']}",
            data={"provider": context.provider}
        )

    def _display_providers(self):
        """Display provider comparison table."""
        for choice, info in self.PROVIDERS.items():
            self.console.print(f"\n  {choice}. {info['emoji']} {info['name']}", style="bold cyan")
            self.console.print(f"     • Best for: {info['best_for']}", style="dim")
            self.console.print(f"     • Speed: {info['speed']}", style="dim")
            self.console.print(f"     • Pricing: {info['pricing']}", style="dim")
            self.console.print(f"     • Reliability: {info['reliability']}", style="dim")
