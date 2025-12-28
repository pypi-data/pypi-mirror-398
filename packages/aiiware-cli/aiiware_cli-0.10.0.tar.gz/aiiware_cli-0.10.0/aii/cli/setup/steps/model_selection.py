# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Model selection step for setup wizard.

Allows users to choose which model to use for their selected provider.
"""


from typing import Any
from aii.cli.setup.steps.base import WizardStep, StepResult
from aii.data.providers.model_registry import (
    get_models_for_provider,
    get_model_metadata,
    MODEL_METADATA
)


class ModelSelectionStep(WizardStep):
    """
    Step 1.5: Choose Model (optional customization).

    Shows available models for the selected provider and lets
    user choose or accept the recommended default.

    v0.9.3: Refactored to use model_registry.py as single source of truth
    """

    title = "Choose Model (Optional)"

    # v0.9.3: Recommended defaults per provider (dynamically load rest from model_registry.py)
    RECOMMENDED_DEFAULTS = {
        "anthropic": "claude-sonnet-4-5",
        "openai": "gpt-5.1",
        "gemini": "gemini-2.5-flash",
        "moonshot": "kimi-k2-turbo-preview",
        "deepseek": "deepseek-chat"
    }

    async def execute(self, context: Any) -> StepResult:
        """
        Display model options and capture selection.

        v0.9.3: Dynamically loads models from model_registry.py

        Args:
            context: WizardContext with provider already selected

        Returns:
            StepResult with success=True if model selected
        """
        if not context.provider:
            return StepResult(
                success=False,
                message="No provider selected",
                fix_suggestion="This is a bug - provider should be selected first"
            )

        # v0.9.3: Get models dynamically from registry
        available_models = get_models_for_provider(context.provider)
        if not available_models:
            # Provider has no model options, use default
            return StepResult(
                success=True,
                message=f"Using default model for {context.provider}"
            )

        # Get default model for this provider
        default_model = self.RECOMMENDED_DEFAULTS.get(
            context.provider,
            available_models[0] if available_models else None
        )

        # Build choices for interactive menu
        menu_choices = []
        default_index = 0

        for idx, model_id in enumerate(available_models, start=1):
            # Get metadata from registry
            metadata = get_model_metadata(context.provider, model_id)
            display_name = metadata.get("display_name", model_id)
            description = metadata.get("description", "")

            # Mark recommended model
            is_recommended = (model_id == default_model)
            model_desc = display_name
            if is_recommended:
                model_desc += " (Recommended)"
                default_index = idx - 1
            model_desc += f" - {description}"

            menu_choices.append((str(idx), model_desc))

        # Add custom option
        max_choice = len(available_models)
        custom_choice = str(max_choice + 1)
        menu_choices.append((custom_choice, "Custom model ID - Enter your own model ID"))

        # Use interactive menu with arrow keys
        choice = self._interactive_menu(
            "Which model would you like to use?",
            menu_choices,
            default_index=default_index
        )

        # Use default if empty
        if not choice:
            selected_model = default_model
            metadata = get_model_metadata(context.provider, default_model)
            model_name = metadata.get("display_name", "Default")
        elif choice == custom_choice:
            # Custom model ID
            self.console.print("\n📝 Enter custom model ID:", style="yellow bold")
            self.console.print(
                f"   Examples for {context.provider}:",
                style="dim"
            )

            # Show provider-specific examples (from registry)
            # v0.9.3: Use actual models from registry as examples
            provider_models = get_models_for_provider(context.provider)
            if provider_models and len(provider_models) > 0:
                # Show first 3 models as examples
                examples = ", ".join(provider_models[:3])
                self.console.print(f"   {examples}", style="cyan dim")

            custom_model = input("\nModel ID: ").strip()

            if not custom_model:
                self.console.print("\n⚠️  No model ID provided, using default", style="yellow")
                selected_model = default_model
                model_name = "Default"
            else:
                selected_model = custom_model
                model_name = f"Custom ({custom_model})"
                self.console.print(
                    f"\n⚠️  Using custom model: {custom_model}",
                    style="yellow bold"
                )
                self.console.print(
                    "   Note: Ensure this model ID is valid for your provider",
                    style="dim"
                )
        else:
            # User selected a model from the list
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(available_models):
                selected_model = available_models[choice_idx]
                metadata = get_model_metadata(context.provider, selected_model)
                model_name = metadata.get("display_name", selected_model)
            else:
                # Invalid choice, use default
                selected_model = default_model
                metadata = get_model_metadata(context.provider, default_model)
                model_name = metadata.get("display_name", "Default")

        # Store in context
        context.selected_model = selected_model

        self.console.print(
            f"\n✓ Selected model: {model_name}",
            style="green bold"
        )

        return StepResult(
            success=True,
            message=f"Selected model: {selected_model}",
            data={"model": selected_model}
        )
