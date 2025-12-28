# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Animated spinner utility for Aii CLI.

Provides consistent animated spinners across all CLI features.
"""


import sys
import asyncio
from typing import Optional


# Braille spinner characters for smooth animation
SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Animation refresh rate (100ms = 10 FPS)
SPINNER_REFRESH_RATE = 0.1


class Spinner:
    """
    Animated spinner context manager for async operations.

    Usage:
        async with Spinner("Loading..."):
            await some_async_operation()

    Or manual control:
        spinner = Spinner("Processing...")
        task = await spinner.start()
        # ... do work ...
        await spinner.stop()
    """

    def __init__(self, message: str, stream=sys.stderr):
        """
        Initialize spinner with message.

        Args:
            message: Message to display with spinner (e.g., "Connecting...")
            stream: Output stream (default: sys.stderr for non-interference)
        """
        self.message = message
        self.stream = stream
        self.running = [False]  # Use list to allow modification in async function
        self.task: Optional[asyncio.Task] = None
        self.is_tty = stream.isatty()  # Check if output is a terminal

    async def _animate(self):
        """Internal animation loop."""
        if not self.is_tty:
            # Non-TTY: Just show static message once (no animation)
            self.stream.write(f"{self.message}...")
            self.stream.flush()
            # Wait until stopped
            while self.running[0]:
                await asyncio.sleep(SPINNER_REFRESH_RATE)
        else:
            # TTY: Animate with spinner characters
            i = 0
            while self.running[0]:
                self.stream.write(f"\r{SPINNER_CHARS[i % len(SPINNER_CHARS)]} {self.message}")
                self.stream.flush()
                i += 1
                await asyncio.sleep(SPINNER_REFRESH_RATE)

    async def start(self) -> asyncio.Task:
        """
        Start the spinner animation.

        Returns:
            The asyncio Task running the animation
        """
        self.running[0] = True
        self.task = asyncio.create_task(self._animate())
        return self.task

    async def stop(self, clear: bool = True):
        """
        Stop the spinner animation.

        Args:
            clear: If True, clear the spinner line (default: True)
        """
        self.running[0] = False
        if self.task:
            await self.task
        if clear:
            # v0.6.0: Print newline first to push any subprocess output to previous line
            # This ensures MCP server logs (which write to stdout without \n) don't
            # appear on the same line as the spinner
            self.stream.write("\n")
            if self.is_tty:
                # Move up one line and clear it
                self.stream.write("\033[1A\r\033[K")  # Move up + clear line
            else:
                # Non-TTY: Just clear current line
                self.stream.write("\r\033[K")
            self.stream.flush()

    def stop_sync(self, clear: bool = True):
        """
        Stop the spinner animation synchronously (for use in sync callbacks).

        This method stops the spinner immediately without waiting for the task.
        The animation task will finish on its own in the background.

        Args:
            clear: If True, clear the spinner line (default: True)
        """
        self.running[0] = False  # Stop the animation loop
        if clear:
            # v0.6.0: Print newline first to push any subprocess output to previous line
            self.stream.write("\n")
            if self.is_tty:
                # Move up one line and clear it
                self.stream.write("\033[1A\r\033[K")  # Move up + clear line
            else:
                # Non-TTY: Just clear current line
                self.stream.write("\r\033[K")
            self.stream.flush()

    async def __aenter__(self):
        """Context manager entry: start spinner."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: stop spinner."""
        await self.stop()
        return False


def create_spinner(message: str, stream=sys.stderr) -> Spinner:
    """
    Factory function to create a Spinner instance.

    Args:
        message: Message to display with spinner
        stream: Output stream (default: sys.stderr)

    Returns:
        Spinner instance

    Example:
        spinner = create_spinner("Loading data...")
        task = await spinner.start()
        # ... do work ...
        await spinner.stop()
    """
    return Spinner(message, stream)


async def show_spinner(message: str, duration: float = 2.0):
    """
    Show spinner for a specific duration (for testing/demo).

    Args:
        message: Message to display
        duration: How long to show spinner (seconds)

    Example:
        await show_spinner("Processing...", 3.0)
    """
    async with Spinner(message):
        await asyncio.sleep(duration)
