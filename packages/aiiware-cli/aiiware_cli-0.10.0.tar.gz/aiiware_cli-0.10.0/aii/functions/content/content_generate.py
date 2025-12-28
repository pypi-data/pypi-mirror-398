# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Content Generate Function - General content generation"""


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


class ContentGenerateFunction(FunctionPlugin):
    """General content generation function for any type of content"""

    @property
    def name(self) -> str:
        return "content_generate"

    @property
    def description(self) -> str:
        return "Generate any type of content based on natural language requests"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content_type": ParameterSchema(
                name="content_type",
                type="string",
                required=False,
                description="Type of content to generate (auto-detected if not specified)",
                choices=[
                    "text",
                    "calendar",
                    "list",
                    "document",
                    "message",
                    "note",
                    "email",
                    "auto",
                ],
                default="auto",
            ),
            "specification": ParameterSchema(
                name="specification",
                type="string",
                required=True,
                description="Natural language description of what content to generate",
            ),
            "start_date": ParameterSchema(
                name="start_date",
                type="string",
                required=False,
                description="Start date for time-based content (YYYY-MM-DD format)",
            ),
            "duration": ParameterSchema(
                name="duration",
                type="string",
                required=False,
                description="Duration or time span for the content",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Output format preference",
                choices=["plain", "markdown", "structured", "auto"],
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
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for content generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute flexible content generation"""

        specification = parameters["specification"]
        content_type = parameters.get("content_type", "auto")
        start_date = parameters.get("start_date")
        duration = parameters.get("duration")
        format_pref = parameters.get("format", "auto")

        try:
            # Build context-aware prompt for content generation
            prompt_parts = [
                f"Generate content based on this request: {specification}",
                "",
            ]

            # Add specific parameters if provided
            if content_type != "auto":
                prompt_parts.append(f"Content type: {content_type}")

            if start_date:
                prompt_parts.append(f"Start date: {start_date}")

            if duration:
                prompt_parts.append(f"Duration/span: {duration}")

            # Add format instructions
            format_instructions = {
                "plain": "Return plain text format",
                "markdown": "Format using markdown syntax",
                "structured": "Use clear structure with headers and sections",
                "auto": "Use the most appropriate format for the content type",
            }

            prompt_parts.extend(
                [
                    "",
                    "Instructions:",
                    f"- {format_instructions.get(format_pref, 'Use appropriate formatting')}",
                    "- Be accurate and helpful",
                    "- Include all necessary details",
                    "- Make the content practical and usable",
                    "- Return only the requested content, no additional explanation",
                    "",
                    "Generate the content:",
                ]
            )

            prompt = "\n".join(prompt_parts)

            # Get streaming callback if available
            streaming_callback = getattr(context.llm_provider, '_streaming_callback', None)

            # Generate content using LLM
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                content = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                content = await context.llm_provider.complete(prompt)
                content = content.strip()
                usage = {}

            return ExecutionResult(
                success=True,
                message=content,
                data={
                    "content": content,
                    "content_type": content_type,
                    "specification": specification,
                    "start_date": start_date,
                    "duration": duration,
                    "format": format_pref,
                    "word_count": len(content.split()),
                    "character_count": len(content),
                    "input_tokens": usage.get("input_tokens"),
                    "output_tokens": usage.get("output_tokens"),
                    "timestamp": datetime.now().isoformat(),
                    "provider": (
                        context.llm_provider.provider_name
                        if hasattr(context.llm_provider, "provider_name")
                        else "Unknown"
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Content generation failed: {str(e)}"
            )

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming content generation

        Args:
            parameters: Function parameters

        Returns:
            str: Formatted prompt for LLM
        """
        specification = parameters.get("specification", "")
        content_type = parameters.get("content_type", "auto")
        output_format = parameters.get("format", "auto")
        start_date = parameters.get("start_date")
        duration = parameters.get("duration")

        # Build comprehensive prompt
        prompt_parts = []

        # Content type instruction
        if content_type and content_type != "auto":
            prompt_parts.append(f"Generate {content_type} content based on the following specification:")
        else:
            prompt_parts.append("Generate content based on the following specification:")

        # Main specification
        prompt_parts.append(f"\n{specification}")

        # Time-based instructions
        if start_date:
            prompt_parts.append(f"\nStart date: {start_date}")
        if duration:
            prompt_parts.append(f"\nDuration: {duration}")

        # Format instruction
        if output_format == "markdown":
            prompt_parts.append("\nFormat the output using markdown.")
        elif output_format == "structured":
            prompt_parts.append("\nProvide a well-structured, organized output.")
        elif output_format == "plain":
            prompt_parts.append("\nProvide plain text output without special formatting.")

        prompt_parts.append("\nProvide the complete content now:")

        return "\n".join(prompt_parts)
