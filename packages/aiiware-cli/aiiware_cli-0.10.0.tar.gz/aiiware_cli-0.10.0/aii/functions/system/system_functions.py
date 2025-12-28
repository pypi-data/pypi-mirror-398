# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""System functions - Help and utilities"""


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


class HelpFunction(FunctionPlugin):
    """Provide help and usage information"""

    @property
    def name(self) -> str:
        return "help"

    @property
    def description(self) -> str:
        return "Show help information and available commands"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "topic": ParameterSchema(
                name="topic",
                type="string",
                required=False,
                description="Specific help topic or function name",
            )
        }

    @property
    def requires_confirmation(self) -> bool:
        return False  # Help is always safe

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: result + metrics"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Provide help information"""
        topic = parameters.get("topic", "").strip()

        if topic:
            # Provide help for specific topic/function
            help_text = await self._get_function_help(topic, context)
        else:
            # General help
            help_text = await self._get_general_help(context)

        return ExecutionResult(
            success=True,
            message=help_text,
            data={"topic": topic, "help_type": "function" if topic else "general"},
        )

    async def _get_general_help(self, context: ExecutionContext) -> str:
        """Get general help information"""
        help_lines = [
            "# AII - AI-Powered CLI Assistant",
            "",
            "AII can help you with various tasks using natural language commands.",
            "",
            "## Available Functions:",
        ]

        # Get available functions from context
        if hasattr(context, "llm_provider") and context.llm_provider:
            # We have LLM access, can provide more intelligent help
            help_lines.append("- 🌐 **Translation**: Translate text between languages")
            help_lines.append('  Example: `aii translate "Hello world" --to spanish`')
            help_lines.append("")

            help_lines.append(
                "- 💻 **Code Generation**: Generate code from descriptions"
            )
            help_lines.append(
                '  Example: `aii code "create a Python function to sort a list"`'
            )
            help_lines.append("")

            help_lines.append("- 🔍 **Code Review**: Analyze code for issues")
            help_lines.append("  Example: `aii review myfile.py`")
            help_lines.append("")

            help_lines.append("- 📋 **Git Assistance**: Generate commit messages")
            help_lines.append("  Example: `aii commit` (after staging changes)")
            help_lines.append("")

            help_lines.append("- 📚 **Explanations**: Explain concepts or topics")
            help_lines.append('  Example: `aii explain "machine learning"`')
            help_lines.append("")

            help_lines.append("- 🔬 **Research**: Find information on topics")
            help_lines.append('  Example: `aii research "latest Python features"`')
            help_lines.append("")
        else:
            help_lines.append("⚠️  **No LLM provider configured**")
            help_lines.append("To use AI features, configure an API key:")
            help_lines.append("`aii config init`")
            help_lines.append("")
            help_lines.append("Limited offline functionality is available.")
            help_lines.append("")

        help_lines.extend(
            [
                "## Configuration:",
                "- `aii config init` - Initialize configuration",
                "- `aii config show` - Show current configuration",
                "",
                "## Chat History:",
                "- `aii history list` - List previous conversations",
                "- `aii continue <chat-id>` - Continue a conversation",
                "- `aii chat` - Start interactive mode",
                "",
                "## Examples:",
                '- `aii "Hello world"` - Simple query',
                '- `aii translate "Bonjour" to english`',
                "- `aii explain docker containers`",
                '- `aii code "fibonacci function in Python"`',
                "",
                "For help with a specific function, use: `aii help <function-name>`",
            ]
        )

        return "\n".join(help_lines)

    async def _get_function_help(self, topic: str, context: ExecutionContext) -> str:
        """Get help for a specific function or topic"""
        # This would ideally access the function registry to get specific help
        # For now, provide a basic response
        return f"""# Help for: {topic}

Sorry, detailed function help is not yet implemented.

Try one of these instead:
- `aii help` - General help
- `aii config show` - Show configuration
- `aii history list` - Show chat history

If you're looking for help with a specific task, try describing it naturally:
- "translate hello to spanish"
- "explain what Docker is"
- "generate code for sorting a list"
"""


class ClarificationFunction(FunctionPlugin):
    """Handle clarification requests when intent is unclear"""

    @property
    def name(self) -> str:
        return "clarify"

    @property
    def description(self) -> str:
        return "Request clarification when user intent is unclear"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        # Make parameters flexible since LLM may generate different parameter names
        return {
            "original_input": ParameterSchema(
                name="original_input",
                type="string",
                required=False,  # Made optional since we can get it from context
                description="The user's original input that needs clarification",
            ),
            "user_input": ParameterSchema(
                name="user_input",
                type="string",
                required=False,  # Alternative parameter name from LLM
                description="The user's input text",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False  # Clarification doesn't need confirmation

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Request clarification from user"""
        # Accept multiple parameter names for flexibility
        original_input = (
            parameters.get("original_input", "")
            or parameters.get("user_input", "")
            or context.user_input
        )

        clarification_message = f"""I'm not sure what you want me to do with: "{original_input}"

Here are some things I can help with:

🌐 **Translation**: `translate "text" to <language>`
💻 **Code Help**: `code "description of what you want"` or `review filename.py`
📋 **Git**: `commit` (after staging changes) or `git status`
📚 **Explanations**: `explain "topic"` or `research "subject"`
💬 **Chat**: `chat` for interactive conversation

Try being more specific about what you'd like to accomplish!

Examples:
- "translate hello world to spanish"
- "explain how docker works"
- "write a python function to sort a list"
- "review my code in main.py"
"""

        return ExecutionResult(
            success=True,
            message=clarification_message,
            data={"original_input": original_input, "type": "clarification_request"},
        )
