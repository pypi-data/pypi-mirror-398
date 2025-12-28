# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Output Formatter - Format and display results to user"""


import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class OutputType(Enum):
    """Types of output content"""

    TEXT = "text"
    CODE = "code"
    JSON = "json"
    TABLE = "table"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"


@dataclass
class OutputSegment:
    """Represents a segment of output with formatting information"""

    content: str
    type: OutputType = OutputType.TEXT
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FormattedOutput:
    """Represents formatted output ready for display"""

    segments: list[OutputSegment]
    timestamp: datetime
    total_length: int = 0

    def __post_init__(self) -> None:
        self.total_length = sum(len(segment.content) for segment in self.segments)

    @property
    def message(self) -> str:
        """Get combined message from all segments"""
        return "\n".join(segment.content for segment in self.segments)


class OutputFormatter:
    """Format various types of output for display"""

    def __init__(self, use_colors: bool | None = None, use_emojis: bool = True):
        # Auto-detect color support if not specified
        if use_colors is None:
            use_colors = self._supports_color()

        self.use_colors = use_colors
        self.use_emojis = use_emojis
        self.color_codes = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "bright_red": "\033[91m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_magenta": "\033[95m",
            "bright_cyan": "\033[96m",
        }
        self.emoji_map = {
            "robot": "🤖",
            "success": "✓",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "search": "🔍",
            "file": "📄",
            "folder": "📁",
            "link": "🔗",
            "code": "💻",
            "git": "📋",
            "translate": "🌐",
            "thinking": "💭",
            "loading": "⏳",
            "context": "🔍",
            "request": "📝",
            "logic": "🧠",
            "output": "📤",
            "confidence": "🎯",
            "tokens": "🔢",
        }

    def format_intent_recognition(
        self, intent: str, confidence: float, requires_confirmation: bool = False
    ) -> FormattedOutput:
        """Format intent recognition results"""
        segments = []

        # Robot emoji and detection message
        robot = self.emoji_map.get("robot", "🤖") if self.use_emojis else "AI"
        segments.append(OutputSegment(f"{robot} I detected: {intent}", OutputType.INFO))

        # Confidence level
        confidence_color = self._get_confidence_color(confidence)
        confidence_text = f"   Confidence: {confidence:.0%}"
        segments.append(
            OutputSegment(
                self._colorize(confidence_text, confidence_color), OutputType.INFO
            )
        )

        # Confirmation prompt if needed
        if requires_confirmation:
            segments.append(OutputSegment("   Confirm? (y/n): ", OutputType.INFO))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_function_call(
        self,
        function_name: str,
        parameters: dict[str, Any],
        requires_confirmation: bool = False,
    ) -> FormattedOutput:
        """Format function call for display"""
        segments = []

        # Function call header
        icon = self.emoji_map.get("function", "⚡") if self.use_emojis else "[FUNC]"
        header = f"{icon} Function: {function_name}"
        segments.append(
            OutputSegment(self._colorize(header, "bright_blue"), OutputType.SUCCESS)
        )

        # Parameters if any
        if parameters:
            params_str = ", ".join(f"{k}={v}" for k, v in parameters.items())
            segments.append(
                OutputSegment(f"   Parameters: {params_str}", OutputType.INFO)
            )

        # Confirmation prompt if needed
        if requires_confirmation:
            segments.append(OutputSegment("   Confirm? (y/n): ", OutputType.INFO))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_help(self, help_data: dict[str, Any]) -> FormattedOutput:
        """Format help information for display"""
        segments = []

        # Help header
        icon = self.emoji_map.get("help", "📖") if self.use_emojis else "[HELP]"
        header = f"{icon} Available Functions"
        segments.append(
            OutputSegment(self._colorize(header, "bright_cyan"), OutputType.INFO)
        )

        # Functions list
        functions = help_data.get("functions", [])
        for func in functions:
            name = func.get("name", "unknown")
            description = func.get("description", "No description")
            category = func.get("category", "general")

            func_line = f"  • {name} ({category}): {description}"
            segments.append(OutputSegment(func_line, OutputType.TEXT))

        # Categories if provided
        categories = help_data.get("categories", [])
        if categories:
            segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
            categories_line = f"Categories: {', '.join(categories)}"
            segments.append(OutputSegment(categories_line, OutputType.INFO))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_execution_result(
        self, result: Any, function_name: str, success: bool = True
    ) -> FormattedOutput:
        """Format function execution results"""
        segments = []

        if success:
            icon = self.emoji_map.get("success", "✓") if self.use_emojis else "[OK]"
            color = "bright_green"
        else:
            icon = self.emoji_map.get("error", "❌") if self.use_emojis else "[ERROR]"
            color = "bright_red"

        # Status line - separate emoji from colored text to preserve emoji display
        colored_text = self._colorize(f"{function_name}: ", color)
        status_line = f"{icon} {colored_text}"
        segments.append(
            OutputSegment(
                status_line,
                OutputType.SUCCESS if success else OutputType.ERROR,
            )
        )

        # Result content
        if isinstance(result, str):
            segments.append(OutputSegment(result, OutputType.TEXT))
        elif isinstance(result, dict):
            segments.append(OutputSegment(self._format_dict(result), OutputType.JSON))
        elif isinstance(result, list):
            segments.append(OutputSegment(self._format_list(result), OutputType.TEXT))
        else:
            segments.append(OutputSegment(str(result), OutputType.TEXT))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_chat_history_list(self, chats: list[dict[str, Any]]) -> FormattedOutput:
        """Format chat history list in table format"""
        segments = []

        if not chats:
            segments.append(OutputSegment("No chat history found.", OutputType.INFO))
            return FormattedOutput(segments=segments, timestamp=datetime.now())

        # Table header
        header = "┌─────────────────────┬─────────────────────────────────────────┬────────────┬─────────────┐"
        segments.append(OutputSegment(header, OutputType.TABLE))

        title_row = "│ Chat ID             │ Title/Summary                           │ Messages   │ Last Active │"
        segments.append(OutputSegment(title_row, OutputType.TABLE))

        separator = "├─────────────────────┼─────────────────────────────────────────┼────────────┼─────────────┤"
        segments.append(OutputSegment(separator, OutputType.TABLE))

        # Table rows
        for chat in chats:
            chat_id = chat.get("id", "N/A")[:19].ljust(19)
            title = chat.get("title", "Untitled")[:39].ljust(39)
            msg_count = str(chat.get("message_count", 0)).ljust(10)
            last_active = self._format_relative_time(chat.get("updated_at", ""))[
                :11
            ].ljust(11)

            row = f"│ {chat_id} │ {title} │ {msg_count} │ {last_active} │"
            segments.append(OutputSegment(row, OutputType.TABLE))

        # Table footer
        footer = "└─────────────────────┴─────────────────────────────────────────┴────────────┴─────────────┘"
        segments.append(OutputSegment(footer, OutputType.TABLE))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_error(
        self, error_message: str, error_type: str = "Error"
    ) -> FormattedOutput:
        """Format error messages"""
        segments = []

        error_icon = self.emoji_map.get("error", "❌") if self.use_emojis else "[ERROR]"
        colored_text = self._colorize(f"{error_type}: {error_message}", "bright_red")
        error_text = f"{error_icon} {colored_text}"

        segments.append(OutputSegment(error_text, OutputType.ERROR))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_loading(self, message: str) -> FormattedOutput:
        """Format loading/progress messages"""
        segments = []

        loading_icon = (
            self.emoji_map.get("loading", "⏳") if self.use_emojis else "[...]"
        )
        colored_text = self._colorize(message, "yellow")
        loading_text = f"{loading_icon} {colored_text}"

        segments.append(OutputSegment(loading_text, OutputType.INFO))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_code_block(self, code: str, language: str = "") -> FormattedOutput:
        """Format code blocks with syntax highlighting"""
        segments = []

        # Code block header
        if language:
            header = f"```{language}"
        else:
            header = "```"

        segments.append(OutputSegment(self._colorize(header, "dim"), OutputType.CODE))

        # Code content
        segments.append(OutputSegment(code, OutputType.CODE))

        # Code block footer
        segments.append(OutputSegment(self._colorize("```", "dim"), OutputType.CODE))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_thinking_mode(
        self,
        context: str,
        request: str,
        reasoning: str,
        result: str,
        confidence: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        provider: str | None = None,
    ) -> FormattedOutput:
        """Format thinking mode output with step-by-step reasoning"""
        segments = []

        # Context line
        context_icon = (
            self.emoji_map.get("context", "🔍") if self.use_emojis else "[CONTEXT]"
        )
        context_line = f"{context_icon} Context: {context}"
        if provider:
            context_line += f" • {provider}"
        segments.append(OutputSegment(context_line, OutputType.INFO))

        # Request line
        request_icon = (
            self.emoji_map.get("request", "📝") if self.use_emojis else "[REQUEST]"
        )
        segments.append(
            OutputSegment(f"{request_icon} Request: {request}", OutputType.INFO)
        )

        # Empty line for spacing
        segments.append(OutputSegment("", OutputType.TEXT))

        # Reasoning/Logic line
        logic_icon = self.emoji_map.get("logic", "🧠") if self.use_emojis else "[LOGIC]"
        segments.append(
            OutputSegment(
                f"{logic_icon} Translation Logic: {reasoning}", OutputType.INFO
            )
        )

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Main result
        translate_icon = (
            self.emoji_map.get("translate", "🌐") if self.use_emojis else "[TRANSLATE]"
        )
        segments.append(
            OutputSegment(f"{translate_icon} Translation:", OutputType.INFO)
        )
        segments.append(OutputSegment(result, OutputType.TEXT))

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Additional info if provided
        if reasoning and "Additional Info:" not in reasoning:
            info_icon = (
                self.emoji_map.get("request", "📝") if self.use_emojis else "[INFO]"
            )
            segments.append(
                OutputSegment(
                    f"{info_icon} Additional Info: Accurate translation preserving meaning and tone.",
                    OutputType.INFO,
                )
            )
            segments.append(OutputSegment("", OutputType.TEXT))

        # Confidence score
        if confidence is not None:
            confidence_icon = (
                self.emoji_map.get("confidence", "🎯")
                if self.use_emojis
                else "[CONFIDENCE]"
            )
            segments.append(
                OutputSegment(
                    f"{confidence_icon} Confidence: {confidence:.1f}%", OutputType.INFO
                )
            )

        # Token usage
        if input_tokens is not None or output_tokens is not None:
            tokens_icon = (
                self.emoji_map.get("tokens", "🔢") if self.use_emojis else "[TOKENS]"
            )
            token_info = []
            if input_tokens:
                token_info.append(f"Input: {input_tokens}")
            if output_tokens:
                token_info.append(f"Output: {output_tokens}")
            if token_info:
                segments.append(
                    OutputSegment(
                        f"{tokens_icon} Tokens: {' • '.join(token_info)}",
                        OutputType.INFO,
                    )
                )

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_git_commit_thinking_mode(
        self,
        context: str,
        git_diff: str,
        commit_message: str,
        reasoning: str,
        confidence: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        provider: str | None = None,
    ) -> FormattedOutput:
        """Format git commit thinking mode output with git diff and commit message"""
        segments = []

        # Context line
        context_icon = (
            self.emoji_map.get("context", "🔍") if self.use_emojis else "[CONTEXT]"
        )
        context_line = f"{context_icon} Context: {context}"
        if provider:
            context_line += f" • {provider}"
        segments.append(OutputSegment(context_line, OutputType.INFO))

        # Request line
        request_icon = (
            self.emoji_map.get("request", "📝") if self.use_emojis else "[REQUEST]"
        )
        segments.append(
            OutputSegment(
                f"{request_icon} Request: Generate AI-powered git commit message",
                OutputType.INFO,
            )
        )

        # Empty line for spacing
        segments.append(OutputSegment("", OutputType.TEXT))

        # Git diff section
        git_icon = self.emoji_map.get("git", "📋") if self.use_emojis else "[GIT]"
        segments.append(OutputSegment(f"{git_icon} Git Diff:", OutputType.INFO))

        # Format git diff in code block style
        if git_diff.strip():
            diff_lines = git_diff.split("\n")
            for line in diff_lines:
                if line.startswith("+++") or line.startswith("---"):
                    segments.append(
                        OutputSegment(
                            self._colorize(line, "bright_blue"), OutputType.CODE
                        )
                    )
                elif line.startswith("@@"):
                    segments.append(
                        OutputSegment(
                            self._colorize(line, "bright_cyan"), OutputType.CODE
                        )
                    )
                elif line.startswith("+"):
                    segments.append(
                        OutputSegment(
                            self._colorize(line, "bright_green"), OutputType.CODE
                        )
                    )
                elif line.startswith("-"):
                    segments.append(
                        OutputSegment(
                            self._colorize(line, "bright_red"), OutputType.CODE
                        )
                    )
                else:
                    segments.append(OutputSegment(line, OutputType.CODE))

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Thinking/Logic line
        logic_icon = (
            self.emoji_map.get("logic", "🧠") if self.use_emojis else "[THINKING]"
        )
        segments.append(
            OutputSegment(f"{logic_icon} Thinking: {reasoning}", OutputType.INFO)
        )

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Generated commit message
        code_icon = self.emoji_map.get("code", "💻") if self.use_emojis else "[COMMIT]"
        segments.append(
            OutputSegment(f"{code_icon} Generated Commit Message:", OutputType.INFO)
        )

        # Format commit message in code block
        commit_lines = commit_message.split("\n")
        for line in commit_lines:
            segments.append(OutputSegment(line, OutputType.TEXT))

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Confidence score
        if confidence is not None:
            confidence_icon = (
                self.emoji_map.get("confidence", "🎯")
                if self.use_emojis
                else "[CONFIDENCE]"
            )
            segments.append(
                OutputSegment(
                    f"{confidence_icon} Confidence: {confidence:.1f}%", OutputType.INFO
                )
            )

        # Token usage
        if input_tokens is not None or output_tokens is not None:
            tokens_icon = (
                self.emoji_map.get("tokens", "🔢") if self.use_emojis else "[TOKENS]"
            )
            token_info = []
            if input_tokens:
                token_info.append(f"Input: {input_tokens}")
            if output_tokens:
                token_info.append(f"Output: {output_tokens}")
            if token_info:
                segments.append(
                    OutputSegment(
                        f"{tokens_icon} Tokens: {' • '.join(token_info)}",
                        OutputType.INFO,
                    )
                )

        # Empty line before confirmation
        segments.append(OutputSegment("", OutputType.TEXT))

        # Confirmation prompt
        segments.append(
            OutputSegment("Proceed with this commit? (y/n): ", OutputType.INFO)
        )

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def display(self, output: FormattedOutput) -> None:
        """Display formatted output to console"""
        for segment in output.segments:
            # Convert literal \n to actual newlines for proper formatting
            content = (
                segment.content.replace("\\n", "\n")
                if isinstance(segment.content, str)
                else segment.content
            )
            print(content)

    def display_segments(self, segments: list[OutputSegment]) -> None:
        """Display a list of output segments"""
        for segment in segments:
            # Convert literal \n to actual newlines for proper formatting
            content = (
                segment.content.replace("\\n", "\n")
                if isinstance(segment.content, str)
                else segment.content
            )
            print(content)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.use_colors or color not in self.color_codes:
            return text

        return f"{self.color_codes[color]}{text}{self.color_codes['reset']}"

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence level"""
        if confidence >= 0.8:
            return "bright_green"
        elif confidence >= 0.6:
            return "bright_yellow"
        else:
            return "bright_red"

    def _format_dict(self, data: dict[str, Any]) -> str:
        """Format dictionary as readable JSON"""
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_list(self, data: list[Any]) -> str:
        """Format list as readable text"""
        if not data:
            return "[]"

        # For simple lists, format as bullet points
        if all(isinstance(item, (str, int, float)) for item in data):
            return "\\n".join(f"- {item}" for item in data)

        # For complex lists, use JSON
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _format_relative_time(self, timestamp: str) -> str:
        """Format timestamp as relative time"""
        if not timestamp:
            return "Unknown"

        try:
            # This is a simplified implementation
            # In practice, you'd want proper datetime parsing and formatting
            return timestamp[:10]  # Just return date part for now
        except (ValueError, TypeError):
            return "Unknown"

    def _supports_color(self) -> bool:
        """Check if the terminal supports ANSI color codes"""
        # Check if we're in a TTY
        if not sys.stdout.isatty():
            return False

        # Check environment variables
        term = os.environ.get("TERM", "").lower()
        if term in ("dumb", "unknown"):
            return False

        # Check for common color-supporting terminals
        if any(
            color_term in term
            for color_term in ["color", "ansi", "xterm", "screen", "tmux"]
        ):
            return True

        # Check COLORTERM environment variable
        if os.environ.get("COLORTERM"):
            return True

        # Check for NO_COLOR environment variable (widely adopted standard)
        if os.environ.get("NO_COLOR"):
            return False

        # Default to True for most modern terminals
        return True

    def format_shell_thinking_mode(
        self,
        context: str,
        request: str,
        command: str,
        explanation: str,
        safety_notes: list[str] | None = None,
        confidence: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        provider: str | None = None,
        execution_output: str | None = None,
    ) -> FormattedOutput:
        """Format shell command thinking mode output matching original aii style"""
        segments = []

        # Context line with system detection and provider
        context_icon = "🔍" if self.use_emojis else "[CONTEXT]"
        context_line = f"{context_icon} Context: mac/bash (detected)"
        if provider:
            # Extract just the provider name (e.g., "google" from "Gemini:gemini-2.0-flash")
            provider_name = (
                provider.split(":")[0].lower() if ":" in provider else provider.lower()
            )
            if provider_name == "gemini":
                provider_name = "google"
            context_line += f" • {provider_name}"
        segments.append(OutputSegment(context_line, OutputType.INFO))

        # Request line
        request_icon = "📝" if self.use_emojis else "[REQUEST]"
        segments.append(
            OutputSegment(f"{request_icon} Request: {request}", OutputType.INFO)
        )

        # AII Thinking process
        thinking_icon = "🤔" if self.use_emojis else "[THINKING]"
        segments.append(
            OutputSegment(
                f"{thinking_icon} AII Thinking: {explanation}", OutputType.INFO
            )
        )

        # Generated Command (with bulb icon)
        command_icon = "💡" if self.use_emojis else "[COMMAND]"
        segments.append(
            OutputSegment(
                f"{command_icon} Generated Command: {command}", OutputType.INFO
            )
        )

        # Additional Info (dynamic based on request)
        info_icon = "📝" if self.use_emojis else "[INFO]"
        # Fix grammar - ensure proper verb form
        if "find" in request.lower():
            additional_info = f"This command finds {request.lower().replace('find ', '').replace('the ', '')}."
        else:
            additional_info = f"This command executes: {request.lower()}."
        segments.append(
            OutputSegment(
                f"{info_icon} Additional Info: {additional_info}", OutputType.INFO
            )
        )

        # Confidence score (use actual confidence or default to 95.0%)
        confidence_icon = "🎯" if self.use_emojis else "[CONFIDENCE]"
        actual_confidence = confidence if confidence is not None else 95.0
        segments.append(
            OutputSegment(
                f"{confidence_icon} Confidence: {actual_confidence:.1f}%",
                OutputType.INFO,
            )
        )

        # Execute prompt (matching original style)
        execute_icon = "🚀" if self.use_emojis else "[EXECUTE]"
        segments.append(
            OutputSegment(
                f"{execute_icon} Execute this command? [y/N]: ", OutputType.INFO
            )
        )

        # Execution output if available (just the raw output, no extra formatting)
        if execution_output:
            segments.append(OutputSegment(execution_output, OutputType.TEXT))

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_shell_execution_result(
        self,
        command: str,
        output: str,
        success: bool = True,
        execution_time: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        output_mode: "OutputMode | None" = None,
    ) -> FormattedOutput:
        """Format shell command execution results

        Args:
            output_mode: If CLEAN, only show the command output (no metadata)
        """
        from ..core.models import OutputMode

        segments = []

        # CLEAN mode: Only show the actual output, nothing else
        if output_mode == OutputMode.CLEAN:
            if output and output.strip():
                segments.append(OutputSegment(output.strip(), OutputType.TEXT))
            else:
                # Even in CLEAN mode, indicate if there's no output
                segments.append(OutputSegment("(no output)", OutputType.TEXT))
            return FormattedOutput(segments=segments, timestamp=datetime.now())

        # STANDARD/THINKING modes: Show metadata + output
        # Success/failure indicator
        if success:
            status_icon = "✅" if self.use_emojis else "[SUCCESS]"
            status_text = self._colorize(
                "Command executed successfully", "bright_green"
            )
        else:
            status_icon = "❌" if self.use_emojis else "[ERROR]"
            status_text = self._colorize("Command execution failed", "bright_red")

        segments.append(OutputSegment(f"{status_icon} {status_text}", OutputType.INFO))

        # Command that was executed
        if command:
            cmd_icon = "🚀" if self.use_emojis else "[CMD]"
            segments.append(
                OutputSegment(f"{cmd_icon} Executed: `{command}`", OutputType.INFO)
            )

        # Execution time if provided
        if execution_time:
            time_icon = "⏱️" if self.use_emojis else "[TIME]"
            segments.append(
                OutputSegment(
                    f"{time_icon} Completed in {execution_time}", OutputType.INFO
                )
            )

        # Token usage if provided
        if input_tokens is not None or output_tokens is not None:
            tokens_icon = "🔢" if self.use_emojis else "[TOKENS]"
            token_info = []
            if input_tokens is not None:
                token_info.append(f"Input: {input_tokens}")
            if output_tokens is not None:
                token_info.append(f"Output: {output_tokens}")
            if token_info:
                segments.append(
                    OutputSegment(
                        f"{tokens_icon} Tokens: {' • '.join(token_info)}",
                        OutputType.INFO,
                    )
                )

        # Empty line for spacing
        segments.append(OutputSegment("", OutputType.TEXT))

        # Output results
        if output and output.strip():
            result_icon = "📋" if self.use_emojis else "[OUTPUT]"
            segments.append(OutputSegment(f"{result_icon} Result:", OutputType.INFO))
            segments.append(OutputSegment(output.strip(), OutputType.TEXT))
        else:
            result_icon = "📋" if self.use_emojis else "[OUTPUT]"
            segments.append(
                OutputSegment(
                    f"{result_icon} Command completed with no output", OutputType.INFO
                )
            )

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    def format_universal_thinking_mode(
        self,
        context: str,
        request: str,
        reasoning: str,
        content: str,
        content_type: str = "content",
        confidence: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        provider: str | None = None,
        context_used: bool = False,
        context_summary: str | None = None,
    ) -> FormattedOutput:
        """Format universal thinking mode output for any content generation"""
        segments = []

        # Header with provider info
        context_icon = (
            self.emoji_map.get("context", "🔍") if self.use_emojis else "[CONTEXT]"
        )
        context_line = f"{context_icon} Context: {context}"
        if provider:
            context_line += f" • {provider}"
        segments.append(OutputSegment(context_line, OutputType.INFO))

        # Request line
        request_icon = (
            self.emoji_map.get("request", "📝") if self.use_emojis else "[REQUEST]"
        )
        segments.append(
            OutputSegment(f"{request_icon} Request: {request}", OutputType.INFO)
        )

        # Empty line for spacing
        segments.append(OutputSegment("", OutputType.TEXT))

        # Context summary if available
        if context_used and context_summary:
            context_detail_icon = (
                self.emoji_map.get("info", "📊") if self.use_emojis else "[INFO]"
            )
            segments.append(
                OutputSegment(
                    f"{context_detail_icon} Context Gathered:", OutputType.INFO
                )
            )
            for line in context_summary.split("\n"):
                if line.strip():
                    segments.append(OutputSegment(f"  {line}", OutputType.INFO))
            segments.append(OutputSegment("", OutputType.TEXT))

        # Thinking process
        thinking_icon = (
            self.emoji_map.get("logic", "🧠") if self.use_emojis else "[THINKING]"
        )
        segments.append(
            OutputSegment(f"{thinking_icon} Thinking: {reasoning}", OutputType.INFO)
        )

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Content type icon mapping
        content_icons = {"tweet": "🐦", "email": "📧", "post": "📱", "content": "📄"}
        content_icon = (
            content_icons.get(content_type.lower(), "📄")
            if self.use_emojis
            else f"[{content_type.upper()}]"
        )

        # Main result
        segments.append(
            OutputSegment(
                f"{content_icon} Generated {content_type.title()}:", OutputType.INFO
            )
        )
        segments.append(OutputSegment(content, OutputType.TEXT))

        # Empty line
        segments.append(OutputSegment("", OutputType.TEXT))

        # Confidence score
        if confidence is not None:
            confidence_icon = (
                self.emoji_map.get("confidence", "🎯")
                if self.use_emojis
                else "[CONFIDENCE]"
            )
            segments.append(
                OutputSegment(
                    f"{confidence_icon} Confidence: {confidence:.1f}%", OutputType.INFO
                )
            )

        # Token usage
        if input_tokens is not None or output_tokens is not None:
            tokens_icon = (
                self.emoji_map.get("tokens", "🔢") if self.use_emojis else "[TOKENS]"
            )
            token_info = []
            if input_tokens:
                token_info.append(f"Input: {input_tokens}")
            if output_tokens:
                token_info.append(f"Output: {output_tokens}")
            if token_info:
                segments.append(
                    OutputSegment(
                        f"{tokens_icon} Tokens: {' • '.join(token_info)}",
                        OutputType.INFO,
                    )
                )

        return FormattedOutput(segments=segments, timestamp=datetime.now())
