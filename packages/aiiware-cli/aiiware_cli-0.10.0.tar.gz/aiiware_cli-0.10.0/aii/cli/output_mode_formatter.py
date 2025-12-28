# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Output Mode Formatter - Handles different display modes for function results"""


from typing import Any, Optional
from ..core.models import ExecutionResult, OutputMode


class OutputModeFormatter:
    """Formats function execution results based on output mode"""

    def __init__(self, use_colors: bool = True, use_emojis: bool = True):
        self.use_colors = use_colors
        self.use_emojis = use_emojis

    def format_result(
        self,
        result: ExecutionResult,
        mode: OutputMode,
        function_name: str = None
    ) -> str:
        """
        Format execution result based on output mode

        Args:
            result: The execution result to format
            mode: The output mode (CLEAN, STANDARD, THINKING)
            function_name: Optional function name for context

        Returns:
            Formatted string ready for display
        """
        if mode == OutputMode.CLEAN:
            return self._format_clean(result)
        elif mode == OutputMode.STANDARD:
            return self._format_standard(result, function_name)
        elif mode == OutputMode.THINKING:
            return self._format_thinking(result, function_name)
        else:  # AUTO - use STANDARD as default
            return self._format_standard(result, function_name)

    def _format_clean(self, result: ExecutionResult) -> str:
        """
        CLEAN mode: Just the result, no metadata

        Examples:
        - translate: "hola"
        - explain: [explanation text]
        - code_generate: [code block]
        """
        # v0.4.13: For confirmation prompts, always show the full message (not clean_output)
        if result.data and result.data.get("requires_execution_confirmation"):
            return result.message

        # Check if result has specific clean output
        if result.data and "clean_output" in result.data:
            return result.data["clean_output"]

        # For translation, show just the translation
        if result.data and "translated_text" in result.data:
            return result.data["translated_text"]

        # For code generation, show just the code
        if result.data and "generated_code" in result.data:
            return result.data["generated_code"]

        # Default: use message
        return result.message

    def _format_standard(self, result: ExecutionResult, function_name: str = None) -> str:
        """
        STANDARD mode: Result + basic metrics (time, tokens, cost)

        Example:
        hola

        ✓ translate: (2.1s) • 145↗ 28↘ (173 tokens) • $0.000043
        """
        lines = []

        # Main result
        clean_result = self._format_clean(result)
        if clean_result:
            lines.append(clean_result)
            lines.append("")  # Blank line before metrics

        # Metrics line
        metrics_parts = []

        # Success status
        status_icon = "✓" if result.success else "❌"
        if function_name:
            metrics_parts.append(f"{status_icon} {function_name}:")
        else:
            metrics_parts.append(status_icon)

        # Execution time
        if result.execution_time and result.execution_time > 0:
            time_str = f"({result.execution_time:.1f}s)" if result.execution_time >= 0.1 else f"({result.execution_time*1000:.0f}ms)"
            metrics_parts.append(time_str)

        # Tokens
        if result.data:
            input_tokens = result.data.get("input_tokens", 0)
            output_tokens = result.data.get("output_tokens", 0)
            if input_tokens or output_tokens:
                total_tokens = input_tokens + output_tokens
                metrics_parts.append(f"{input_tokens}↗ {output_tokens}↘ ({total_tokens} tokens)")

        # Cost
        if result.data and "cost" in result.data and result.data["cost"] > 0:
            cost = result.data["cost"]
            cost_str = f"${cost:.6f}" if cost < 0.01 else f"${cost:.4f}"
            metrics_parts.append(cost_str)

        if len(metrics_parts) > 1:  # Only show if we have more than just status icon
            lines.append(" • ".join(metrics_parts))

        return "\n".join(lines)

    def _format_thinking(self, result: ExecutionResult, function_name: str = None) -> str:
        """
        THINKING mode: Full reasoning display with context

        Used for functions like git_commit, research, complex analysis
        Shows the full thinking mode output if available
        """
        # If function provided thinking mode data, use existing formatter
        if result.data and result.data.get("thinking_mode"):
            # This will be handled by the existing thinking mode formatter
            # in output_formatter.py - just return empty and let that handle it
            return ""

        # Otherwise, show standard + reasoning if available
        lines = []

        # Standard output
        standard = self._format_standard(result, function_name)
        if standard:
            lines.append(standard)

        # Add reasoning if available
        if result.data and "reasoning" in result.data:
            lines.append("")
            lines.append(f"💭 Reasoning: {result.data['reasoning']}")

        # Add confidence if available
        if result.data and "confidence" in result.data:
            confidence = result.data["confidence"]
            lines.append(f"🎯 Confidence: {confidence:.1f}%")

        return "\n".join(lines)

    def should_show_session_summary(self, mode: OutputMode) -> bool:
        """Determine if session summary should be shown for this mode"""
        # CLEAN mode: No session summary
        # STANDARD mode: Show session summary
        # THINKING mode: Show session summary
        return mode != OutputMode.CLEAN
