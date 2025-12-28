# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Response Streaming Formatter - Real-time LLM response display"""


import sys
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text


class ResponseStreamingFormatter:
    """Format LLM streaming responses with real-time rendering

    This formatter displays LLM tokens in real-time by printing directly to console.
    Avoids the flickering issue of Live display updates.
    """

    def __init__(self, enable_markdown: bool = True, show_cursor: bool = True, status_display=None):
        """Initialize response streaming formatter

        Args:
            enable_markdown: Whether to render markdown during streaming
            show_cursor: Whether to show typing cursor (█) during streaming
            status_display: Optional status display to stop when streaming starts
        """
        self.console = Console()
        self.enable_markdown = enable_markdown
        self.show_cursor = show_cursor
        self.accumulated_text = ""
        self.streaming_started = False
        self.status_display = status_display

    def start_streaming(self) -> None:
        """Initialize streaming display"""
        self.accumulated_text = ""
        self.streaming_started = True
        # Don't print newline - spinner already cleared the line

    def update(self, new_tokens: str) -> None:
        """Update display with new tokens

        Args:
            new_tokens: New tokens to append and display
        """
        if not self.streaming_started:
            # Stop the spinner on first chunk (smooth transition)
            if self.status_display:
                self.status_display.stop_loading()

            self.start_streaming()

        # Accumulate tokens
        self.accumulated_text += new_tokens

        # Print the new tokens directly without newline
        # This creates true streaming effect
        print(new_tokens, end='', flush=True)

    def complete(self, final_text: str, function_name: str = None, success: bool = True, execution_time: float = None) -> None:
        """Finalize display with complete response

        Args:
            final_text: The complete final text to display
            function_name: Optional function name to show in status
            success: Whether the execution was successful
            execution_time: Optional execution time in seconds
        """
        # Update accumulated text to final version
        self.accumulated_text = final_text

        # Print newline to complete the stream
        print()

        # Print status line with proper color formatting using Rich
        if function_name:
            from rich.console import Console
            console = Console()
            status_icon = "✓" if success else "❌"
            color = "green" if success else "red"

            # Format timing if available
            if execution_time is not None:
                time_str = f" ({execution_time:.1f}s)" if execution_time >= 0.1 else f" ({execution_time*1000:.0f}ms)"
                console.print(f"{status_icon} [{color}]{function_name}:[/{color}] [dim]{time_str}[/dim]")
            else:
                console.print(f"{status_icon} [{color}]{function_name}:[/{color}]")
            # No extra newline - let engine control spacing

    def stop(self) -> None:
        """Stop streaming display immediately

        This is useful for cleanup in error scenarios.
        """
        if self.streaming_started:
            # Print newline to end the stream cleanly
            print()
            self.streaming_started = False

    def reset(self) -> None:
        """Reset formatter state for reuse"""
        self.accumulated_text = ""
        self.streaming_started = False
