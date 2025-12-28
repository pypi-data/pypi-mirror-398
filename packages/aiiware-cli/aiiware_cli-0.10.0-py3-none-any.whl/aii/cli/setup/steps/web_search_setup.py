# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Web search setup step for setup wizard.

Optionally configures web search provider for research functionality.
"""


import getpass
from typing import Any
from aii.cli.setup.steps.base import WizardStep, StepResult


class WebSearchSetupStep(WizardStep):
    """
    Optional Step: Configure Web Search.

    Allows users to optionally set up web search for the research function.
    """

    title = "Configure Web Search (Optional)"

    WEB_PROVIDERS = {
        "1": {
            "name": "Brave Search",
            "key": "brave",
            "description": "Fast, privacy-focused (Requires API key)",
            "signup_url": "https://brave.com/search/api/",
            "env_var": "BRAVE_SEARCH_API_KEY"
        },
        "2": {
            "name": "Google Search",
            "key": "google",
            "description": "Comprehensive results (Requires API key + Custom Search Engine)",
            "signup_url": "https://developers.google.com/custom-search/v1/overview",
            "env_var": "GOOGLE_SEARCH_API_KEY"
        },
        "3": {
            "name": "DuckDuckGo",
            "key": "duckduckgo",
            "description": "Free, no API key needed (Limited results)",
            "signup_url": None,
            "env_var": None
        }
    }

    async def execute(self, context: Any) -> StepResult:
        """
        Optionally configure web search.

        Args:
            context: WizardContext

        Returns:
            StepResult with success=True (always succeeds, even if skipped)
        """
        self.console.print(
            "Web search enables the 'research' function to fetch real-time information.\n",
            style="bold"
        )
        self.console.print(
            "This is optional - you can skip and configure later.\n",
            style="dim"
        )

        # Ask if user wants to configure
        configure = self._confirm(
            "Would you like to configure web search now?",
            default=False
        )

        if not configure:
            self.console.print("\n⏭️  Skipping web search setup", style="yellow")
            self.console.print("You can configure later with: aii config set web-search.enabled true", style="dim")
            return StepResult(
                success=True,
                message="Web search setup skipped"
            )

        # Build choices for interactive menu
        menu_choices = []
        for choice_num, info in self.WEB_PROVIDERS.items():
            search_desc = f"{info['name']}"
            if info['key'] == 'brave':
                search_desc += " (Recommended)"
            search_desc += f" - {info['description']}"
            menu_choices.append((choice_num, search_desc))

        # Use interactive menu with arrow keys (default to Brave)
        choice = self._interactive_menu(
            "Which web search provider would you like to use?",
            menu_choices,
            default_index=0  # Brave is recommended
        )

        provider_info = self.WEB_PROVIDERS[choice]
        context.web_search_provider = provider_info["key"]

        self.console.print(
            f"\n✓ Selected: {provider_info['name']}",
            style="green bold"
        )

        # If DuckDuckGo (no API key needed)
        if provider_info["key"] == "duckduckgo":
            context.web_search_api_key = None
            context.web_search_env_var = None
            return StepResult(
                success=True,
                message="DuckDuckGo configured (no API key needed)",
                data={"provider": "duckduckgo"}
            )

        # For Brave/Google, get API key
        self.console.print(f"\n{provider_info['name']} requires an API key.\n", style="yellow")

        if provider_info["signup_url"]:
            self.console.print(f"Sign up at: {provider_info['signup_url']}\n", style="cyan")

        # Prompt for API key
        try:
            api_key = getpass.getpass(f"{provider_info['name']} API Key (or press Enter to skip): ")
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception:
            api_key = input(f"{provider_info['name']} API Key (or press Enter to skip): ")

        if not api_key:
            self.console.print("\n⏭️  Skipping API key - using DuckDuckGo instead", style="yellow")
            context.web_search_provider = "duckduckgo"
            context.web_search_api_key = None
            context.web_search_env_var = None
            return StepResult(
                success=True,
                message="Falling back to DuckDuckGo"
            )

        # Store API key
        context.web_search_api_key = api_key
        context.web_search_env_var = provider_info["env_var"]

        self.console.print(f"\n✓ API key captured", style="green")

        return StepResult(
            success=True,
            message=f"{provider_info['name']} configured",
            data={
                "provider": provider_info["key"],
                "has_api_key": True
            }
        )

    def _display_providers(self):
        """Display web search provider options."""
        for choice, info in self.WEB_PROVIDERS.items():
            # Highlight Brave as recommended
            is_recommended = info['key'] == 'brave'
            name_display = f"{info['name']} (Recommended)" if is_recommended else info['name']

            self.console.print(
                f"\n  {choice}. {name_display}",
                style="cyan bold" if is_recommended else "cyan"
            )
            self.console.print(f"     {info['description']}", style="dim")
