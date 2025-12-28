# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Status Display - Loading animations and progress feedback"""


import sys
import threading
import time
from typing import Any


class StatusDisplay:
    """Manages loading animations and status messages"""

    def __init__(self, use_emojis: bool = True, use_animations: bool = True):
        self.use_emojis = use_emojis
        self.use_animations = use_animations
        self.is_displaying = False
        self._display_thread = None
        self._stop_event = threading.Event()

        # Animation frames
        self.spinner_frames = (
            ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            if use_emojis
            else ["|", "/", "-", "\\"]
        )
        self.dots_frames = (
            ["⠋", "⠙", "⠚", "⠞", "⠖", "⠦", "⠴", "⠲", "⠳", "⠓"]
            if use_emojis
            else [".", "..", "...", "...."]
        )

    def start_loading(self, message: str, animation_type: str = "spinner") -> None:
        """Start displaying loading animation with message"""
        if self.is_displaying:
            self.stop_loading()

        # If animations are disabled, just print the message once
        if not self.use_animations:
            print(f"[LOADING] {message}")
            return

        self.is_displaying = True
        self._stop_event.clear()

        # Choose animation frames
        frames = (
            self.spinner_frames if animation_type == "spinner" else self.dots_frames
        )

        self._display_thread = threading.Thread(
            target=self._animate, args=(message, frames), daemon=True
        )
        self._display_thread.start()

    def _animate(self, message: str, frames: list[str]) -> None:
        """Display animation frames"""
        frame_index = 0

        while not self._stop_event.is_set():
            # Clear current line and show animation
            sys.stdout.write(f"\r{frames[frame_index]} {message}")
            sys.stdout.flush()

            frame_index = (frame_index + 1) % len(frames)
            time.sleep(0.1)  # 100ms per frame

    def update_message(self, new_message: str) -> None:
        """Update the loading message (for future enhancement)"""
        # This would require more complex thread communication
        # For now, we'll restart with new message
        if self.is_displaying:
            self.stop_loading()
            self.start_loading(new_message)

    def stop_loading(self) -> None:
        """Stop loading animation and clear the line"""
        # If animations are disabled, there's nothing to stop
        if not self.use_animations:
            return

        if self.is_displaying and self._display_thread:
            self._stop_event.set()
            self._display_thread.join(timeout=0.5)

            # Clear the loading line
            sys.stdout.write(
                "\r" + " " * 80 + "\r"
            )  # Clear with spaces, then return to start
            sys.stdout.flush()

            self.is_displaying = False
            self._display_thread = None

    def show_status(self, message: str, status_type: str = "info") -> None:
        """Show a status message without animation"""
        icons = {
            "info": "ℹ️" if self.use_emojis else "[INFO]",
            "working": "⚙️" if self.use_emojis else "[WORK]",
            "thinking": "🧠" if self.use_emojis else "[THINK]",
            "gathering": "📊" if self.use_emojis else "[GATHER]",
            "generating": "✨" if self.use_emojis else "[GEN]",
            "success": "✅" if self.use_emojis else "[OK]",
            "error": "❌" if self.use_emojis else "[ERR]",
        }

        icon = icons.get(status_type, icons["info"])
        print(f"{icon} {message}")

    async def async_status_context(
        self, message: str, animation_type: str = "spinner"
    ) -> "AsyncStatusContext":
        """Async context manager for loading states"""
        return AsyncStatusContext(self, message, animation_type)


class AsyncStatusContext:
    """Async context manager for loading animations"""

    def __init__(
        self, status_display: StatusDisplay, message: str, animation_type: str
    ):
        self.status_display = status_display
        self.message = message
        self.animation_type = animation_type

    async def __aenter__(self) -> "AsyncStatusContext":
        self.status_display.start_loading(self.message, self.animation_type)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.status_display.stop_loading()


class ProgressTracker:
    """Tracks and displays progress for multi-step operations with inline updates"""

    def __init__(self, use_emojis: bool = True, use_animations: bool = True):
        self.use_emojis = use_emojis
        self.use_animations = use_animations
        self.steps = []
        self.current_step = 0
        self._display_thread = None
        self._stop_event = threading.Event()
        self.is_displaying = False

        # Animation frames
        self.spinner_frames = (
            ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            if use_emojis
            else ["|", "/", "-", "\\"]
        )

    def add_step(self, description: str, icon: str = "⚙️") -> None:
        """Add a step to track"""
        self.steps.append(
            {
                "description": description,
                "icon": icon if self.use_emojis else "[.]",
                "status": "pending",  # pending, in_progress, completed, failed
                "start_time": None,
                "end_time": None,
            }
        )

    def start_step(self, step_index: int | None = None) -> None:
        """Start a specific step (or next step if none specified)"""
        if step_index is None:
            step_index = self.current_step

        if 0 <= step_index < len(self.steps):
            self.steps[step_index]["status"] = "in_progress"
            self.steps[step_index]["start_time"] = time.time()
            self.current_step = step_index

            # Start animated display for this step
            if self.use_animations:
                self._start_animated_step()

    def complete_step(
        self, step_index: int | None = None, success: bool = True
    ) -> None:
        """Complete a specific step"""
        if step_index is None:
            step_index = self.current_step

        if 0 <= step_index < len(self.steps):
            # Stop animation
            self._stop_animated_step()

            self.steps[step_index]["status"] = "completed" if success else "failed"
            self.steps[step_index]["end_time"] = time.time()

            # Show completion status
            icon = "✅" if success else "❌"
            if not self.use_emojis:
                icon = "[✓]" if success else "[✗]"

            elapsed = self.steps[step_index]["end_time"] - self.steps[step_index]["start_time"]
            print(f"{icon} {self.steps[step_index]['description']} ({elapsed:.1f}s)")

            if success and step_index == self.current_step:
                self.current_step += 1

    def _start_animated_step(self) -> None:
        """Start animated display for current step"""
        if self.is_displaying:
            self._stop_animated_step()

        step = self.steps[self.current_step]
        self.is_displaying = True
        self._stop_event.clear()

        self._display_thread = threading.Thread(
            target=self._animate_step, args=(step,), daemon=True
        )
        self._display_thread.start()

    def _animate_step(self, step: dict) -> None:
        """Display animated progress for a step"""
        frame_index = 0

        while not self._stop_event.is_set():
            # Show icon + spinner + description
            spinner = self.spinner_frames[frame_index]
            sys.stdout.write(f"\r{step['icon']} {spinner} {step['description']}...")
            sys.stdout.flush()

            frame_index = (frame_index + 1) % len(self.spinner_frames)
            time.sleep(0.1)

    def _stop_animated_step(self) -> None:
        """Stop animated display"""
        if self.is_displaying and self._display_thread:
            self._stop_event.set()
            self._display_thread.join(timeout=0.5)

            # Clear the line
            sys.stdout.write("\r" + " " * 100 + "\r")
            sys.stdout.flush()

            self.is_displaying = False
            self._display_thread = None

    def finish(self) -> None:
        """Finish progress tracking and clean up"""
        self._stop_animated_step()

    def get_summary(self) -> dict[str, Any]:
        """Get progress summary"""
        completed = sum(1 for step in self.steps if step["status"] == "completed")
        failed = sum(1 for step in self.steps if step["status"] == "failed")
        total = len(self.steps)

        return {
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "in_progress": sum(
                1 for step in self.steps if step["status"] == "in_progress"
            ),
            "pending": total - completed - failed,
            "success_rate": completed / total if total > 0 else 0,
        }
