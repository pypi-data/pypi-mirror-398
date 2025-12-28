# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Universal Content Function - Generate any type of content"""


from datetime import datetime
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)

# Note: LLMOrchestrator is used by the engine, not needed here


class UniversalContentFunction(FunctionPlugin):
    """Universal content generation function using orchestrated context gathering"""

    @property
    def name(self) -> str:
        return "universal_generate"

    @property
    def description(self) -> str:
        return "Generate any type of content using intelligent context gathering"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "request": ParameterSchema(
                name="request",
                type="string",
                required=True,
                description="Natural language description of what to generate",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Target format hint",
                choices=[
                    "auto",
                    "tweet",
                    "email",
                    "post",
                    "code",
                    "commit",
                    "explanation",
                ],
                default="auto",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                description="Writing tone/style for the content",
                choices=["professional", "casual", "technical", "friendly"],
                default="professional",
            ),
            "conversation_history": ParameterSchema(
                name="conversation_history",
                type="array",
                required=False,
                description="Previous conversation messages for context",
                default=[],
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: just the result"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for universal content generation"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute universal content generation using orchestrated approach"""

        request = parameters["request"]
        target_format = parameters.get("format", "auto")
        conversation_history = parameters.get("conversation_history", [])

        try:
            # If conversation history is provided, prepend it to the request
            enhanced_request = request
            if conversation_history and len(conversation_history) > 0:
                # Build conversation context from history
                history_text = "\n\n".join([
                    f"{'User' if msg.get('role') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                    for msg in conversation_history[-10:]  # Last 10 messages for context
                ])
                enhanced_request = f"""Previous conversation:
{history_text}

Current request: {request}

Please respond to the current request while considering the conversation history above."""

            # Import orchestrator dynamically to avoid circular imports
            from ...core.orchestrator import LLMOrchestrator

            # Create a dummy function registry since we're using basic orchestrator
            # The orchestrator only needs basic context functions
            from ...core.registry.function_registry import FunctionRegistry

            registry = FunctionRegistry()

            # Create orchestrator instance
            orchestrator = LLMOrchestrator(
                llm_provider=context.llm_provider, function_registry=registry
            )

            # Process request using universal architecture with conversation history
            result = await orchestrator.process_universal_request(enhanced_request, context)

            if result.success:
                # Extract the generated content for CLEAN mode
                generated_content = result.message or result.data.get("content", "")

                # Create reasoning for THINKING/VERBOSE modes
                context_note = " (with conversation context)" if len(conversation_history) > 0 else ""
                reasoning = f"Generated {target_format} content using universal orchestrated approach{context_note} based on the user's request"

                # Add metadata about the generation process
                result.data.update(
                    {
                        "clean_output": generated_content,  # For CLEAN mode
                        "reasoning": reasoning,  # For THINKING/VERBOSE modes
                        "generation_method": "universal_orchestrated",
                        "original_request": request,
                        "target_format": target_format,
                        "conversation_context_used": len(conversation_history) > 0,
                    }
                )

            return result

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Universal content generation failed: {str(e)}"
            )
