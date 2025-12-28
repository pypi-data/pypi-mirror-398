# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Email Content Function - Generate professional emails"""


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


class EmailContentFunction(FunctionPlugin):
    """Professional email content generation"""

    @property
    def name(self) -> str:
        return "generate_email"

    @property
    def description(self) -> str:
        return "Generate professional email content with proper structure"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "purpose": ParameterSchema(
                name="purpose",
                type="string",
                required=True,
                description="Purpose or main topic of the email",
            ),
            "recipient_type": ParameterSchema(
                name="recipient_type",
                type="string",
                required=False,
                choices=["colleague", "client", "manager", "external", "team"],
                default="colleague",
                description="Type of recipient to adjust formality",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                choices=["professional", "casual", "technical", "friendly"],
                default="professional",
                description="Writing tone/style for the email",
            ),
            "include_context": ParameterSchema(
                name="include_context",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include project/git context if available",
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
                valid=False, errors=["LLM provider required for email generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute email content generation"""

        purpose = parameters["purpose"]
        recipient_type = parameters.get("recipient_type", "colleague")
        tone = parameters.get("tone", "professional")
        include_context = parameters.get("include_context", True)

        try:
            # Get git context if requested and available
            context_info = ""
            if include_context:
                try:
                    import subprocess

                    result = subprocess.run(
                        ["git", "log", "-1", "--pretty=format:%s%n%b"],
                        capture_output=True,
                        text=True,
                        cwd=context.config.get("working_dir", "."),
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        context_info = (
                            f"\n\nLatest project update:\n{result.stdout.strip()}"
                        )
                except Exception:
                    pass

            # Build email prompt
            formality_guide = {
                "formal": "Very formal and structured",
                "professional": "Professional but approachable",
                "friendly": "Warm and friendly while maintaining professionalism",
                "urgent": "Direct and action-oriented",
            }

            recipient_guide = {
                "colleague": "peer-level professional",
                "client": "external client requiring clear communication",
                "manager": "supervisor requiring concise updates",
                "external": "external stakeholder",
                "team": "team members for coordination",
            }

            prompt = f"""Generate a professional email about: {purpose}

Context:
- Recipient: {recipient_guide.get(recipient_type, recipient_type)}
- Tone: {formality_guide.get(tone, tone)}
{context_info}

Structure:
- Subject line (clear and informative)
- Appropriate greeting
- Clear, well-organized body
- Professional closing
- Signature placeholder

Generate the complete email:"""

            # Get streaming callback if available
            streaming_callback = getattr(context.llm_provider, '_streaming_callback', None)

            # Use complete_with_usage for token tracking if available
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                email = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                email = await context.llm_provider.complete(prompt)
                email = email.strip()
                usage = {}

            # Extract subject line if present
            subject = ""
            lines = email.split("\n")
            if lines and ("subject:" in lines[0].lower() or "re:" in lines[0].lower()):
                subject = (
                    lines[0].replace("Subject:", "").replace("subject:", "").strip()
                )
                email = "\n".join(lines[1:]).strip()

            return ExecutionResult(
                success=True,
                message=email,
                data={
                    "email_body": email,
                    "subject": subject,
                    "purpose": purpose,
                    "recipient_type": recipient_type,
                    "tone": tone,
                    "context_included": bool(context_info),
                    "word_count": len(email.split()),
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Email generation failed: {str(e)}"
            )
