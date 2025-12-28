# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Twitter Content Function - Generate tweets and threads"""


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


class TwitterContentFunction(FunctionPlugin):
    """Specialized Twitter content generation with optimized prompting"""

    @property
    def name(self) -> str:
        return "generate_tweet"

    @property
    def description(self) -> str:
        return """Generate Twitter/X posts optimized for engagement and format (max 280 characters).

Use this function when the user wants to create a tweet or Twitter post.

Common patterns:
- "tweet about [topic]"
- "create a tweet [topic]"
- "write a tweet about [topic]"
- "generate tweet: [topic]"
- "post to twitter about [topic]"

The 'topic' parameter should contain the subject matter or message for the tweet.
Extract the topic from user input - everything after keywords like "tweet about", "create a tweet", etc.

Examples:
- "tweet announcing our new AI-powered CLI tool" → topic: "announcing our new AI-powered CLI tool"
- "create a tweet about Python tips" → topic: "Python tips"
- "write a tweet launching our product" → topic: "launching our product"

Output: A tweet under 280 characters with optional hashtags and emojis."""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "topic": ParameterSchema(
                name="topic",
                type="string",
                required=True,
                description="Topic or theme for the tweet",
            ),
            "include_hashtags": ParameterSchema(
                name="include_hashtags",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include relevant hashtags",
            ),
            "include_emojis": ParameterSchema(
                name="include_emojis",
                type="boolean",
                required=False,
                default=True,
                description="Whether to include relevant emojis",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                choices=["professional", "casual", "technical", "friendly"],
                default="casual",
                description="Writing tone/style for the tweet",
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
                valid=False, errors=["LLM provider required for tweet generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute Twitter content generation with specialized prompting"""

        topic = parameters["topic"]
        include_hashtags = parameters.get("include_hashtags", True)
        include_emojis = parameters.get("include_emojis", True)
        tone = parameters.get("tone", "casual")

        try:
            # Build specialized tweet prompt
            prompt = f"""Create an engaging Twitter post about: {topic}

Requirements:
- Maximum 280 characters
- {tone} tone
- {'Include relevant hashtags' if include_hashtags else 'No hashtags'}
- {'Include appropriate emojis' if include_emojis else 'No emojis'}
- Focus on engagement and shareability
- Be authentic and valuable to the audience

Generate only the tweet text, no additional explanation:"""

            # Use complete_with_usage for accurate token tracking
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                tweet = llm_response.content.strip().strip('"').strip("'")
                usage = llm_response.usage or {}
            else:
                tweet = await context.llm_provider.complete(prompt)
                tweet = tweet.strip().strip('"').strip("'")
                usage = {}

            # Validate length
            if len(tweet) > 280:
                return ExecutionResult(
                    success=False,
                    message=f"Generated tweet is too long ({len(tweet)} characters, max 280)",
                )

            return ExecutionResult(
                success=True,
                message=tweet,
                data={
                    "tweet": tweet,
                    "clean_output": tweet,  # For CLEAN output mode
                    "character_count": len(tweet),
                    "topic": topic,
                    "tone": tone,
                    "includes_hashtags": "#" in tweet,
                    "includes_emojis": any(ord(char) > 127 for char in tweet),
                    "timestamp": datetime.now().isoformat(),
                    # Token tracking (v0.6.0)
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Tweet generation failed: {str(e)}"
            )
