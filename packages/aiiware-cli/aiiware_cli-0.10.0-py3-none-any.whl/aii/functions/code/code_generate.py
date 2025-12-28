# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Code Generation Function - Generate code based on requirements."""


import ast
from pathlib import Path
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


class CodeGenerateFunction(FunctionPlugin):
    """Generate code based on specifications"""

    @property
    def name(self) -> str:
        return "code_generate"

    @property
    def description(self) -> str:
        return "Generate code based on natural language specifications"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.CODE

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "specification": ParameterSchema(
                name="specification",
                type="string",
                required=True,
                description="Natural language description of what to code",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Programming language (auto-detected if not specified) or 'text' for content generation",
                choices=[
                    "python",
                    "javascript",
                    "typescript",
                    "java",
                    "cpp",
                    "go",
                    "rust",
                    "text",
                    "auto",
                ],
                default="auto",
            ),
            "style": ParameterSchema(
                name="style",
                type="string",
                required=False,
                description="Code style preference",
                choices=["clean", "documented", "production", "minimal"],
                default="clean",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # User should confirm before generating code

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.CONTEXT_DEPENDENT

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
                errors=["LLM provider required for code generation"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute code or content generation"""
        specification = parameters["specification"]
        language = parameters.get("language", "auto")
        style = parameters.get("style", "clean")

        try:
            # Check if this is content generation (not code)
            # Only match if it's explicitly asking for content creation, not code about those topics
            spec_lower = specification.lower()
            if language == "text" or any(
                pattern in spec_lower
                for pattern in [
                    "write a tweet", "create a tweet", "generate a tweet",
                    "write a post", "create a post", "generate a post",
                    "write a message", "create a message", "generate a message",
                    "write an email", "create an email", "generate an email",
                    "write content", "create content", "generate content"
                ]
            ):
                # This is content generation (tweets, posts, etc.)
                content = await self._generate_content(
                    specification, context.llm_provider
                )

                return ExecutionResult(
                    success=True,
                    message=content,
                    data={
                        "content": content,
                        "type": "content",
                        "specification": specification,
                    },
                )

            # This is code generation
            # Detect language if auto
            if language == "auto":
                language = await self._detect_language(specification)

            # Generate code and capture token usage
            code, usage = await self._generate_code(
                specification, language, style, context.llm_provider
            )

            return ExecutionResult(
                success=True,
                message=f"Generated {language} code:\n\n```{language}\n{code}\n```",
                data={
                    "code": code,
                    "language": language,
                    "specification": specification,
                    "style": style,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Code/content generation failed: {str(e)}"
            )

    async def _detect_language(self, specification: str) -> str:
        """Detect programming language from specification"""
        spec_lower = specification.lower()

        language_keywords = {
            "python": ["python", "django", "flask", "pandas", "numpy", "class", "def"],
            "javascript": [
                "javascript",
                "js",
                "react",
                "node",
                "npm",
                "function",
                "const",
                "let",
            ],
            "typescript": ["typescript", "ts", "interface", "type"],
            "java": ["java", "spring", "class", "public static void"],
            "cpp": ["c++", "cpp", "include", "iostream", "vector"],
            "go": ["go", "golang", "package", "func"],
            "rust": ["rust", "cargo", "fn", "struct", "impl"],
        }

        scores = {}
        for lang, keywords in language_keywords.items():
            score = sum(1 for keyword in keywords if keyword in spec_lower)
            if score > 0:
                scores[lang] = score

        return max(scores.items(), key=lambda x: x[1])[0] if scores else "python"

    async def _generate_content(self, specification: str, llm_provider: Any) -> str:
        """Generate content (tweets, posts, etc.) using LLM"""

        # Check if the request mentions git commit to include latest commit info
        include_git_info = "git commit" in specification.lower()
        git_info = ""

        if include_git_info:
            try:
                import subprocess

                # Get the latest commit information
                result = subprocess.run(
                    ["git", "log", "-1", "--pretty=format:%s%n%b"],
                    capture_output=True,
                    text=True,
                    cwd=".",
                )
                if result.returncode == 0 and result.stdout.strip():
                    git_info = f"\n\nLatest git commit info:\n{result.stdout.strip()}"
            except Exception:
                git_info = ""

        prompt = f"""Generate content based on this request: {specification}

{git_info}

Please create engaging, professional content that matches the requested format:

For TWEETS:
- Include appropriate emojis and hashtags
- Stay within 280 characters
- Engaging and shareable tone

For EMAILS:
- Professional subject line and body
- Clear structure with proper greeting/closing
- Appropriate level of detail

For POSTS/MESSAGES:
- Appropriate tone for the platform
- Include relevant emojis/hashtags if requested
- Proper formatting

Return only the generated content, no additional explanation."""

        try:
            result = await llm_provider.complete(prompt)
            return (
                str(result)
                if result is not None
                else "Content generation failed: No result"
            )
        except Exception as e:
            return f"Content generation failed: {str(e)}"

    async def _generate_code(
        self, specification: str, language: str, style: str, llm_provider: Any
    ) -> tuple[str, dict]:
        """Generate code using LLM and return code with token usage"""
        style_instructions = {
            "clean": "Write clean, readable code with meaningful variable names",
            "documented": "Include comprehensive documentation and comments",
            "production": "Write production-ready code with error handling and validation",
            "minimal": "Write minimal, concise code without extra features",
        }

        style_instruction = style_instructions.get(style, "Write clean, readable code")

        prompt = f"""Generate {language} code based on this specification:

Specification: {specification}

Requirements:
1. {style_instruction}
2. Follow {language} best practices and conventions
3. Include error handling where appropriate
4. Return only the code, no explanations
5. Ensure code is complete and runnable

Generate the code:"""

        try:
            # Use complete_with_usage for token tracking if available
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(prompt)
                result = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                result = str(result) if result is not None else ""
                usage = {}

            # Clean up the response (remove markdown formatting if present)
            code = result.strip()
            if code.startswith("```"):
                lines = code.split("\n")
                if len(lines) > 2:
                    code = "\n".join(lines[1:-1])  # Remove first and last line

            return code, usage
        except Exception as e:
            raise RuntimeError(f"Failed to generate code: {str(e)}") from e
