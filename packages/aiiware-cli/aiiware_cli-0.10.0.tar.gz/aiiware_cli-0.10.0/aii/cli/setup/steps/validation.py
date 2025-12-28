# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
API key validation step for setup wizard.

Tests the API key by making a real LLM call to verify it works.
"""


import time
from typing import Any

from aii.cli.setup.steps.base import WizardStep, StepResult
from aii.data.providers.llm_provider import create_llm_provider


class ValidationStep(WizardStep):
    """
    Step 3: Validate API Key.

    Makes a test LLM call to verify the API key works and
    measure connection latency.
    """

    title = "Validate API Key"

    async def execute(self, context: Any) -> StepResult:
        """
        Validate API key with test call.

        Args:
            context: WizardContext with provider and api_key

        Returns:
            StepResult with success=True if key is valid
        """
        if not context.provider or not context.api_key:
            return StepResult(
                success=False,
                message="Missing provider or API key",
                fix_suggestion="This is a bug - previous steps should have set these"
            )

        self.console.print("✓ Validating API key...", style="green")

        # Show spinner while testing
        with self.console.status(
            f"⠋ Testing connection to {context.provider}...",
            spinner="dots"
        ):
            result = await self._test_api_key(context)

        if result.success:
            self.console.print(
                f"✅ API key is valid! (latency: {result.data['latency_ms']:.0f}ms)",
                style="green bold"
            )

            # Update context with validation results
            context.validation_latency_ms = result.data['latency_ms']
            context.validation_model = result.data.get('model')

        return result

    async def _test_api_key(self, context: Any) -> StepResult:
        """
        Make a minimal test LLM call.

        Args:
            context: WizardContext

        Returns:
            StepResult with validation outcome
        """
        try:
            # Use selected model if available, otherwise use default
            if context.selected_model:
                model = context.selected_model
            else:
                default_models = {
                    "anthropic": "claude-sonnet-4-5-20250929",
                    "openai": "gpt-5",
                    "gemini": "gemini-2.5-flash"
                }
                model = default_models.get(context.provider, "")

            # Create temporary provider instance
            provider = create_llm_provider(
                provider_name=context.provider,
                api_key=context.api_key,
                model=model,
                use_pydantic_ai=True
            )

            # Make minimal test call
            start = time.time()
            response = await provider.complete("Hello")
            latency_ms = (time.time() - start) * 1000

            # Check response is not empty
            if not response or len(response.strip()) < 1:
                return StepResult(
                    success=False,
                    message="API call returned empty response",
                    fix_suggestion="The API key may be invalid or the service is down"
                )

            return StepResult(
                success=True,
                message="API key validated successfully",
                data={
                    "latency_ms": latency_ms,
                    "model": model or getattr(provider, 'model', 'unknown'),
                    "response_length": len(response)
                }
            )

        except Exception as e:
            error_msg = str(e).lower()

            # Provide specific fix suggestions based on error
            if "authentication" in error_msg or "api key" in error_msg or "unauthorized" in error_msg:
                fix_suggestion = (
                    "The API key appears to be invalid. Please check:\n"
                    "  • You copied the entire key (no spaces or newlines)\n"
                    "  • The key hasn't been revoked\n"
                    "  • You're using the correct provider"
                )
            elif "timeout" in error_msg or "connection" in error_msg:
                fix_suggestion = (
                    "Network connection failed. Please check:\n"
                    "  • Your internet connection is working\n"
                    "  • The provider's service is available\n"
                    "  • No firewall is blocking the request"
                )
            elif "rate limit" in error_msg:
                fix_suggestion = "Rate limit exceeded. Please wait a moment and retry."
            else:
                fix_suggestion = (
                    f"Validation failed with error: {str(e)}\n"
                    "Please check your API key and try again."
                )

            return StepResult(
                success=False,
                message=f"API key validation failed: {str(e)}",
                fix_suggestion=fix_suggestion
            )
