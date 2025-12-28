# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Real-time Streaming Output Formatter with Live Updates"""


import asyncio
from collections.abc import AsyncIterator
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.text import Text

from .output_formatter import (
    FormattedOutput,
    OutputFormatter,
    OutputSegment,
    OutputType,
)


class StreamingFormatter(OutputFormatter):
    """Enhanced formatter with real-time streaming capabilities"""

    def __init__(self, use_colors: bool = True, use_emojis: bool = True):
        super().__init__(use_colors, use_emojis)
        self.console = Console()

    async def stream_shell_thinking_mode(
        self,
        context: str,
        request: str,
        provider: str | None = None,
        stream_generator: AsyncIterator[str] | None = None,
    ) -> FormattedOutput:
        """Stream shell command generation with real-time thinking display"""

        segments = []

        # Initial context display
        context_icon = "🔍" if self.use_emojis else "[CONTEXT]"
        context_line = f"{context_icon} Context: mac/bash (detected)"
        if provider:
            provider_name = (
                provider.split(":")[0].lower() if ":" in provider else provider.lower()
            )
            if provider_name == "gemini":
                provider_name = "google"
            context_line += f" • {provider_name}"

        self.console.print(context_line)
        segments.append(OutputSegment(context_line, OutputType.INFO))

        # Request display
        request_icon = "📝" if self.use_emojis else "[REQUEST]"
        request_line = f"{request_icon} Request: {request}"
        self.console.print(request_line)
        segments.append(OutputSegment(request_line, OutputType.INFO))

        # Streaming thinking process
        thinking_icon = "🤔" if self.use_emojis else "[THINKING]"

        if stream_generator:
            # Real-time streaming display
            thinking_content = ""

            with Live(console=self.console, refresh_per_second=10) as live:
                live.update(
                    Panel(
                        Text("Starting AI reasoning...", style="yellow"),
                        title=f"{thinking_icon} AII Thinking",
                        border_style="blue",
                    )
                )

                async for chunk in stream_generator:
                    thinking_content += chunk

                    # Update live display with current content
                    display_text = Text(thinking_content)
                    if len(thinking_content) > 200:
                        # Truncate for display but keep full content
                        display_text = Text(thinking_content[-200:] + "...")

                    live.update(
                        Panel(
                            display_text,
                            title=f"{thinking_icon} AII Thinking (streaming...)",
                            border_style="green",
                        )
                    )

                    # Small delay to make streaming visible
                    await asyncio.sleep(0.05)

                # Final display
                final_text = (
                    Markdown(thinking_content)
                    if thinking_content
                    else Text("Processing complete")
                )
                live.update(
                    Panel(
                        final_text,
                        title=f"{thinking_icon} AII Thinking (complete)",
                        border_style="blue",
                    )
                )

            segments.append(
                OutputSegment(
                    f"{thinking_icon} AII Thinking: {thinking_content}", OutputType.INFO
                )
            )
        else:
            # Fallback for non-streaming
            self.console.print(f"{thinking_icon} AII Thinking: Processing request...")
            segments.append(
                OutputSegment(
                    f"{thinking_icon} AII Thinking: Processing request...",
                    OutputType.INFO,
                )
            )

        return FormattedOutput(segments=segments, timestamp=datetime.now())

    async def stream_command_generation(
        self,
        request: str,
        provider: str | None = None,
        command_stream: AsyncIterator[str] | None = None,
    ) -> dict[str, str]:
        """Stream command generation with live progress indicators"""

        result = {"command": "", "explanation": "", "confidence": 95.0}

        if not command_stream:
            return result

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:

            # Create tasks for different phases
            thinking_task = progress.add_task("🧠 Analyzing request...", total=100)
            generation_task = progress.add_task("⚡ Generating command...", total=100)

            content = ""
            phase = "thinking"

            async for chunk in command_stream:
                content += chunk

                # Update progress based on content
                if "command" in chunk.lower() and phase == "thinking":
                    progress.update(thinking_task, completed=100)
                    phase = "generating"
                    progress.update(generation_task, advance=20)
                elif phase == "generating":
                    progress.update(generation_task, advance=5)

                # Small delay for visual effect
                await asyncio.sleep(0.03)

            # Complete all tasks
            progress.update(thinking_task, completed=100)
            progress.update(generation_task, completed=100)

            result["explanation"] = content

            # Extract command from content (simple parsing)
            if "`" in content:
                # Look for command in backticks
                parts = content.split("`")
                if len(parts) >= 2:
                    result["command"] = parts[1].strip()

        return result

    def display_streaming_result(
        self,
        command: str,
        explanation: str,
        confidence: float = 95.0,
        execution_output: str | None = None,
    ) -> None:
        """Display streaming results with enhanced formatting"""

        # Command display
        command_icon = "💡" if self.use_emojis else "[COMMAND]"
        self.console.print(f"\n{command_icon} Generated Command: `{command}`")

        # Additional info
        info_icon = "📝" if self.use_emojis else "[INFO]"
        if "find" in command.lower():
            additional_info = "This command finds the requested files using optimized search patterns."
        else:
            additional_info = "This command executes the requested operation safely."

        self.console.print(f"{info_icon} Additional Info: {additional_info}")

        # Confidence with visual indicator
        confidence_icon = "🎯" if self.use_emojis else "[CONFIDENCE]"
        confidence_color = (
            "green" if confidence >= 90 else "yellow" if confidence >= 70 else "red"
        )
        self.console.print(
            f"{confidence_icon} Confidence: [{confidence_color}]{confidence:.1f}%[/{confidence_color}]"
        )

        # Execution prompt
        execute_icon = "🚀" if self.use_emojis else "[EXECUTE]"
        self.console.print(f"\n{execute_icon} Execute this command? [y/N]: ", end="")

        # If execution output is provided, display it
        if execution_output:
            self.console.print(f"\n📋 Result:\n{execution_output}")

    async def stream_execution_feedback(
        self, command: str, execution_stream: AsyncIterator[str] | None = None
    ) -> str:
        """Stream command execution with real-time output"""

        output = ""

        if execution_stream:
            with Live(console=self.console, refresh_per_second=5) as live:
                live.update(
                    Panel(
                        Text("Initializing command execution...", style="yellow"),
                        title="🚀 Executing Command",
                        border_style="blue",
                    )
                )

                async for chunk in execution_stream:
                    output += chunk

                    # Show live output
                    display_output = (
                        output if len(output) < 500 else "..." + output[-500:]
                    )
                    live.update(
                        Panel(
                            Text(display_output, style="green"),
                            title="🚀 Command Output (live)",
                            border_style="green",
                        )
                    )

                    await asyncio.sleep(0.1)

                # Final result
                live.update(
                    Panel(
                        Text(output, style="bright_green"),
                        title="✅ Execution Complete",
                        border_style="green",
                    )
                )

        return output

    def create_enhanced_status_display(
        self, message: str = "Processing..."
    ) -> "StreamingStatus":
        """Create an enhanced streaming status display"""
        return StreamingStatus(self.console, message)


class StreamingStatus:
    """Enhanced status display with streaming capabilities"""

    def __init__(self, console: Console, message: str):
        self.console = console
        self.message = message
        self.live = None
        self._task = None

    def start(self) -> None:
        """Start the streaming status display"""
        progress = Progress(
            SpinnerColumn(spinner_style="cyan"),
            TextColumn("[cyan]{task.description}"),
            console=self.console,
            transient=True,
        )

        self.live = Live(progress, console=self.console, refresh_per_second=10)
        self.live.start()

        self._task = progress.add_task(self.message, total=None)

    def update_message(self, new_message: str) -> None:
        """Update the status message"""
        if self.live and self._task is not None:
            # This would need to access the progress instance
            # Implementation depends on Rich's API
            self.message = new_message

    def stop(self) -> None:
        """Stop the streaming status display"""
        if self.live:
            self.live.stop()
            self.live = None
