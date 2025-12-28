# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
API key acquisition step for setup wizard.

Opens browser to provider's API key page and captures the key securely.
"""


import getpass
from typing import Any

from aii.cli.setup.steps.base import WizardStep, StepResult
from aii.cli.setup.ui.browser import BrowserHelper


class APIKeyAcquisitionStep(WizardStep):
    """
    Step 2: Get API Key.

    Opens browser to provider's API key page and prompts user to
    enter their API key securely (hidden input).
    """

    title = "Get API Key"

    async def execute(self, context: Any) -> StepResult:
        """
        Open browser and capture API key.

        Args:
            context: WizardContext with provider already selected

        Returns:
            StepResult with success=True if API key captured
        """
        if not context.provider:
            return StepResult(
                success=False,
                message="No provider selected",
                fix_suggestion="This is a bug - provider should be selected in previous step"
            )

        # Try to open browser
        success, url = BrowserHelper.open_provider_page(context.provider)

        if success:
            self.console.print(f"Opening browser to: {url}\n", style="cyan")
        else:
            self.console.print(
                f"⚠️  Could not open browser automatically.\n"
                f"Please visit: {url}\n",
                style="yellow"
            )

        # Show instructions
        self.console.print("Instructions:", style="bold")
        instructions = BrowserHelper.get_instructions(context.provider)
        for line in instructions.split('\n'):
            self.console.print(f"  {line}", style="dim")

        self.console.print()

        # Prompt for API key (hidden input)
        api_key = self._prompt_api_key()

        if not api_key:
            return StepResult(
                success=False,
                message="No API key provided",
                fix_suggestion="You need an API key to use AII. Press 'y' to retry."
            )

        # Basic validation (not empty, reasonable length)
        if len(api_key) < 10:
            return StepResult(
                success=False,
                message="API key seems too short (< 10 characters)",
                fix_suggestion="Please check and re-enter your API key"
            )

        # Update context
        context.api_key = api_key

        return StepResult(
            success=True,
            message="API key captured",
            data={"key_length": len(api_key)}
        )

    def _prompt_api_key(self) -> str:
        """
        Prompt for API key with hidden input.

        Returns:
            API key string (or empty if cancelled)
        """
        try:
            self.console.print("Once you have your key, paste it here:", style="bold")
            api_key = getpass.getpass("API Key: ").strip()
            return api_key
        except KeyboardInterrupt:
            raise  # Let wizard handle cancellation
        except Exception:
            # Fallback to visible input if getpass fails
            self.console.print("(Hidden input failed, using visible input)", style="yellow")
            return input("API Key: ").strip()
