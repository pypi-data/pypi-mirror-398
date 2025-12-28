# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Social Post Function - Generate social media posts"""


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


class SocialPostFunction(FunctionPlugin):
    """Social media post generation for various platforms"""

    @property
    def name(self) -> str:
        return "generate_social_post"

    @property
    def description(self) -> str:
        return """Generate social media posts optimized for different platforms (Twitter, LinkedIn, Facebook, Instagram).

Use this function when the user wants to create a social media post (not just Twitter).

Common patterns:
- "social post about [content]"
- "create a social media post [content]"
- "write a post for [platform] about [content]"
- "generate social post: [content]"
- "create linkedin post about [content]"

The 'content' parameter should contain the topic or message for the social post.
Extract the content from user input - everything after keywords like "social post", "create post", etc.

Examples:
- "social post about product launch" → content: "product launch"
- "create a linkedin post about AI trends" → content: "AI trends", platform: "linkedin"
- "write a facebook post announcing new feature" → content: "announcing new feature", platform: "facebook"

Output: Platform-optimized social media post with appropriate formatting, hashtags, and style."""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CONTENT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content": ParameterSchema(
                name="content",
                type="string",
                required=True,
                description="Topic or content to create a post about",
            ),
            "platform": ParameterSchema(
                name="platform",
                type="string",
                required=False,
                choices=["twitter", "linkedin", "facebook", "instagram", "general"],
                default="general",
                description="Target social media platform",
            ),
            "style": ParameterSchema(
                name="style",
                type="string",
                required=False,
                choices=[
                    "informative",
                    "promotional",
                    "personal",
                    "professional",
                    "humorous",
                ],
                default="informative",
                description="Style of the post",
            ),
            "tone": ParameterSchema(
                name="tone",
                type="string",
                required=False,
                description="Writing tone/style for the post",
                choices=["professional", "casual", "technical", "friendly"],
                default="casual",
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
                valid=False, errors=["LLM provider required for social post generation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute social media post generation"""

        content = parameters["content"]
        platform = parameters.get("platform", "general")
        style = parameters.get("style", "informative")

        try:
            # Platform-specific guidelines
            platform_guides = {
                "twitter": "280 characters max, hashtags, engaging and concise",
                "linkedin": "Professional tone, industry insights, call-to-action",
                "facebook": "Casual but informative, encourage engagement",
                "instagram": "Visual focus, story-driven, relevant hashtags",
                "general": "Adaptable for multiple platforms, balanced approach",
            }

            guide = platform_guides.get(platform, platform_guides["general"])

            prompt = f"""Create a {platform} post about: {content}

Style: {style}
Platform guidelines: {guide}

Requirements:
- Match the {style} style appropriately
- Include relevant hashtags if appropriate for the platform
- Encourage engagement where suitable
- Make it shareable and valuable

Generate only the post content:"""

            # Use complete_with_usage for accurate token tracking
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                post = llm_response.content.strip().strip('"').strip("'")
                usage = llm_response.usage or {}
            else:
                post = await context.llm_provider.complete(prompt)
                post = post.strip().strip('"').strip("'")
                usage = {}

            return ExecutionResult(
                success=True,
                message=post,
                data={
                    "post": post,
                    "clean_output": post,  # For CLEAN output mode
                    "platform": platform,
                    "style": style,
                    "content_topic": content,
                    "character_count": len(post),
                    "hashtag_count": post.count("#"),
                    "timestamp": datetime.now().isoformat(),
                    # Token tracking (v0.6.0)
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Social post generation failed: {str(e)}"
            )
