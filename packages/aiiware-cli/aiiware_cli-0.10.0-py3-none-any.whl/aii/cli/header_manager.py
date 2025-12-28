# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Output Header Manager for session-level display with verbosity control"""


import time
from enum import Enum
from typing import Optional, Dict, Any

from ..core.session.manager import SessionManager, get_session
from ..core.session.models import SessionMetrics


class VerbosityLevel(Enum):
    """Output verbosity levels"""
    MINIMAL = 1
    STANDARD = 2
    DETAILED = 3


class ExecutionMode(Enum):
    """Execution mode context"""
    CLI = "cli"
    INTERACTIVE = "interactive"


class FunctionSafety(Enum):
    """Function safety classification"""
    SAFE = "SAFE"
    RISKY = "RISKY"
    CONTEXT_DEPENDENT = "CONTEXT"
    DESTRUCTIVE = "DESTRUCTIVE"


class OutputHeaderManager:
    """Manages session-level headers with clean context display"""

    def __init__(self, verbosity: VerbosityLevel = VerbosityLevel.STANDARD,
                 mode: ExecutionMode = ExecutionMode.CLI, use_colors: bool = True,
                 use_emojis: bool = True):
        self.verbosity = verbosity
        self.mode = mode
        self.use_colors = use_colors
        self.use_emojis = use_emojis
        self.session_start_time = time.time()
        self.header_shown = False

        # Color codes for terminal output
        self.color_codes = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "red": "\033[31m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_red": "\033[91m",
        }

        # Emoji mappings
        self.emoji_map = {
            "context": "🔍",
            "request": "📝",
            "processing": "⚡",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "confirmation": "🤖",
            "timer": "⏱️",
            "tokens": "🔢",
        }

        # Safety level colors
        self.safety_colors = {
            FunctionSafety.SAFE: "bright_green",
            FunctionSafety.RISKY: "bright_yellow",
            FunctionSafety.CONTEXT_DEPENDENT: "bright_blue",
            FunctionSafety.DESTRUCTIVE: "bright_red",
        }

    def show_session_header(self, user_input: str, session_id: str,
                          llm_provider: Optional[str] = None, function_count: Optional[int] = None) -> None:
        """Display Phase 1 initial context header - matches design spec format"""
        if self.header_shown:
            return

        # Phase 1: Initial Context Header
        # Format: 🔍 aii • Claude Sonnet 3.5 • Functions: 24 loaded
        icon = self._get_icon("context")
        parts = ["aii"]

        if llm_provider:
            parts.append(self._format_provider_name(llm_provider))

        # Add function count info
        if function_count is not None:
            parts.append(f"Functions: {function_count} loaded")
        else:
            parts.append("Functions: 24 loaded")  # Fallback

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Request line with processing indicator
        # Format: 📝 Converting 1000 feet to meters...
        request_icon = self._get_icon("request")
        print(f"{request_icon} {user_input}")
        print()  # Blank line to separate header from content

        self.header_shown = True

    def show_function_context_header(self, function_name: str, safety_level: FunctionSafety,
                                   llm_provider: Optional[str] = None, user_input: str = "") -> None:
        """Display Phase 2 processing header with function context - matches design spec"""
        # Format: 🔍 aii • Claude Sonnet 3.5 • content_generate (SAFE)
        icon = self._get_icon("context")
        parts = ["aii"]

        if llm_provider:
            parts.append(self._format_provider_name(llm_provider))

        # Add function name and safety level
        safety_text = self._colorize_safety(safety_level.value, safety_level)
        parts.append(f"{function_name} ({safety_text})")

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Request line
        request_icon = self._get_icon("request")
        print(f"{request_icon} {user_input}")

    def show_execution_result_header(self, function_name: str, safety_level: FunctionSafety,
                                   llm_provider: Optional[str] = None, user_input: str = "",
                                   execution_time: Optional[float] = None,
                                   tokens: Optional[Dict[str, int]] = None) -> None:
        """Display Phase 3 result header with execution info - matches design spec"""
        # Format: 🔍 aii • Claude Sonnet 3.5 • content_generate (SAFE)
        icon = self._get_icon("context")
        parts = ["aii"]

        if llm_provider:
            parts.append(self._format_provider_name(llm_provider))

        # Add function name and safety level
        safety_text = self._colorize_safety(safety_level.value, safety_level)
        parts.append(f"{function_name} ({safety_text})")

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Request line with "Request:" prefix
        request_icon = self._get_icon("request")
        print(f"{request_icon} Request: {user_input}")

        # Execution details line
        # Format: ⚡ Generated response • 2.3s • 45↗ 12↘ tokens
        if execution_time is not None or tokens:
            processing_icon = self._get_icon("processing")
            details = ["Generated response"]

            if execution_time is not None:
                details.append(f"{execution_time:.1f}s")

            if tokens:
                input_tokens = tokens.get("input_tokens", 0) or tokens.get("input", 0)
                output_tokens = tokens.get("output_tokens", 0) or tokens.get("output", 0)
                reasoning_tokens = tokens.get("reasoning_tokens", 0) or tokens.get("reasoning", 0)
                total_input = input_tokens + reasoning_tokens
                details.append(f"{total_input}↗ {output_tokens}↘ tokens")

            detail_line = f"{processing_icon} {' • '.join(details)}"
            print(detail_line)

    def show_function_mini_header(self, function_name: str, safety_level: FunctionSafety,
                                description: Optional[str] = None) -> None:
        """Display mini-header for individual function execution"""
        icon = self._get_icon("processing")
        safety_text = self._colorize_safety(safety_level.value, safety_level)

        if self.verbosity == VerbosityLevel.MINIMAL:
            print(f"{icon} {function_name} ({safety_text})")
        else:
            desc_text = f": {description}" if description else ""
            print(f"{icon} {function_name} ({safety_text}){desc_text}")

    def update_processing_status(self, status: str, timing: Optional[float] = None,
                               tokens: Optional[Dict[str, int]] = None,
                               confidence: Optional[float] = None) -> None:
        """Update dynamic processing status line"""
        icon = self._get_icon("processing")
        parts = [f"{icon} {status}"]

        if self.verbosity.value >= VerbosityLevel.STANDARD.value:
            if timing is not None:
                parts.append(f"{timing:.1f}s")

            if tokens:
                input_tokens = tokens.get("input", 0)
                output_tokens = tokens.get("output", 0)
                reasoning_tokens = tokens.get("reasoning", 0)
                total_input = input_tokens + reasoning_tokens
                parts.append(f"{total_input}↗ {output_tokens}↘ tokens")

            if confidence is not None and self.verbosity.value >= VerbosityLevel.DETAILED.value:
                parts.append(f"{confidence:.0f}% confidence")

        status_line = " • ".join(parts)
        print(status_line)

    def show_confirmation_prompt(self, prompt_text: str, default: bool = False) -> None:
        """Display confirmation request with consistent formatting"""
        icon = self._get_icon("confirmation")
        default_text = " [Y/n]" if default else " [y/N]"

        if self.verbosity == VerbosityLevel.MINIMAL:
            print(f"{icon} {prompt_text}{default_text}: ", end="", flush=True)
        else:
            print(f"{icon} {prompt_text}{default_text}: ", end="", flush=True)

    def show_result_status(self, success: bool, message: str) -> None:
        """Display final result with appropriate indicator"""
        if success:
            icon = self._get_icon("success")
            colored_message = self._colorize(message, "bright_green")
        else:
            icon = self._get_icon("error")
            colored_message = self._colorize(message, "bright_red")

        print(f"{icon} {colored_message}")

    def show_request_context(self, user_input: str) -> None:
        """Show user request context line"""
        icon = self._get_icon("request")
        print(f"{icon} {user_input}")

    def _show_minimal_header(self, session: SessionMetrics, llm_provider: Optional[str]) -> None:
        """Minimal header: aii • Current session info"""
        icon = self._get_icon("context")
        parts = ["aii"]

        # For minimal, just show basic info
        if self.mode == ExecutionMode.INTERACTIVE:
            session_duration = time.time() - session.start_time
            parts.append(f"Session: {session_duration:.0f}s")

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Show request context
        self.show_request_context(session.user_input)

    def _show_standard_header(self, session: SessionMetrics, llm_provider: Optional[str]) -> None:
        """Standard header: aii • Provider Model • session info"""
        icon = self._get_icon("context")
        parts = ["aii"]

        if llm_provider:
            parts.append(self._format_provider_name(llm_provider))

        # Add session context for interactive mode
        if self.mode == ExecutionMode.INTERACTIVE:
            session_duration = time.time() - session.start_time
            parts.append(f"Session: {session_duration:.0f}s")

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Show request context
        self.show_request_context(session.user_input)

    def _show_detailed_header(self, session: SessionMetrics, llm_provider: Optional[str]) -> None:
        """Detailed header: aii • Provider Model • Session: ID/Duration • Functions: count"""
        icon = self._get_icon("context")
        parts = ["aii"]

        if llm_provider:
            parts.append(self._format_provider_name(llm_provider))

        # Session info
        if self.mode == ExecutionMode.INTERACTIVE:
            session_duration = time.time() - session.start_time
            parts.append(f"Session: {session_duration:.0f}s")
        else:
            # Show short session ID for CLI mode
            short_id = session.session_id.split("_")[-1][:8] if "_" in session.session_id else session.session_id[:8]
            parts.append(f"Session: {short_id}")

        # Show function count if any have been executed
        if session.total_functions > 0:
            parts.append(f"Functions: {session.total_functions}")

        header = f"{icon} {' • '.join(parts)}"
        print(header)

        # Show request context
        self.show_request_context(session.user_input)

    def _show_fallback_header(self, user_input: str) -> None:
        """Fallback header when no session is available"""
        icon = self._get_icon("context")
        print(f"{icon} aii")
        self.show_request_context(user_input)

    def _format_provider_name(self, provider: str) -> str:
        """Format LLM provider name in user-friendly way"""
        # Handle provider:model format
        if ":" in provider:
            provider_name, model = provider.split(":", 1)
        else:
            provider_name, model = provider, ""

        # Convert provider names to friendly format
        provider_map = {
            "anthropic": "Claude",
            "openai": "GPT",
            "google": "Gemini",
            "gemini": "Gemini"
        }

        friendly_name = provider_map.get(provider_name.lower(), provider_name)

        # Extract model version for common patterns
        if model:
            if "claude" in model.lower():
                if "sonnet" in model.lower():
                    # Extract version from model name (e.g., claude-3-7-sonnet-20250219 -> Sonnet 3.7)
                    if "3-7" in model or "3.7" in model:
                        return f"{friendly_name} Sonnet 3.7"
                    elif "3-5" in model or "3.5" in model:
                        return f"{friendly_name} Sonnet 3.5"
                    elif "3-" in model:
                        # Extract any 3.x version
                        import re
                        version_match = re.search(r'3[-.](\d+)', model)
                        if version_match:
                            return f"{friendly_name} Sonnet 3.{version_match.group(1)}"
                        return f"{friendly_name} Sonnet 3.x"
                    else:
                        return f"{friendly_name} Sonnet"
                elif "haiku" in model.lower():
                    return f"{friendly_name} Haiku"
                elif "opus" in model.lower():
                    return f"{friendly_name} Opus"
            elif "gpt" in model.lower():
                if "4" in model:
                    return f"{friendly_name}-4"
                elif "3.5" in model:
                    return f"{friendly_name}-3.5"
            elif "gemini" in model.lower():
                if "pro" in model.lower():
                    return f"{friendly_name} Pro"
                elif "flash" in model.lower():
                    return f"{friendly_name} Flash"

        return friendly_name

    def _colorize_safety(self, text: str, safety_level: FunctionSafety) -> str:
        """Apply color to safety level text"""
        color = self.safety_colors.get(safety_level, "reset")
        return self._colorize(text, color)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.use_colors or color not in self.color_codes:
            return text
        return f"{self.color_codes[color]}{text}{self.color_codes['reset']}"

    def _get_icon(self, icon_type: str) -> str:
        """Get emoji icon or fallback text"""
        if self.use_emojis and icon_type in self.emoji_map:
            return self.emoji_map[icon_type]

        # Fallback text for non-emoji environments
        fallbacks = {
            "context": "[AII]",
            "request": "[REQ]",
            "processing": "[PROC]",
            "success": "[OK]",
            "error": "[ERR]",
            "warning": "[WARN]",
            "confirmation": "[?]",
            "timer": "[TIME]",
            "tokens": "[TOK]",
        }
        return fallbacks.get(icon_type, "[INFO]")

    def reset_header_state(self) -> None:
        """Reset header state for new session"""
        self.header_shown = False
        self.session_start_time = time.time()
