# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Base classes for wizard steps.

Defines the protocol that all wizard steps must follow.
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any
from rich.console import Console
import sys

# Import termios/tty for Unix-like systems
try:
    import tty
    import termios
    HAS_TERMIOS = True
except ImportError:
    # Windows doesn't have termios
    HAS_TERMIOS = False


@dataclass
class StepResult:
    """
    Result of executing a wizard step.

    Attributes:
        success: Whether the step completed successfully
        message: Human-readable message about the result
        fix_suggestion: Optional suggestion for fixing errors
        data: Optional additional data from step execution
    """
    success: bool
    message: str = ""
    fix_suggestion: Optional[str] = None
    data: Optional[Any] = None


class WizardStep(ABC):
    """
    Base class for all wizard steps.

    Each step is responsible for:
    1. Displaying UI to gather user input
    2. Validating input
    3. Updating the WizardContext
    4. Returning success/failure result

    Steps should follow Single Responsibility Principle:
    - Each step does ONE thing
    - Steps don't depend on each other's internal implementation
    - Steps communicate only through WizardContext
    """

    title: str = "Unnamed Step"

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the wizard step.

        Args:
            console: Rich console for output (creates new if None)
        """
        self.console = console or Console()

    @abstractmethod
    async def execute(self, context: Any) -> StepResult:
        """
        Execute this wizard step.

        Args:
            context: WizardContext with shared state

        Returns:
            StepResult indicating success/failure and any messages

        Raises:
            KeyboardInterrupt: User pressed Ctrl+C (let it propagate)
            Exception: Unexpected errors (should be caught and converted to StepResult)
        """
        pass

    def _prompt(self, message: str, default: Optional[str] = None) -> str:
        """
        Prompt user for input.

        Args:
            message: Prompt message
            default: Default value if user presses Enter

        Returns:
            User input (or default)
        """
        if default:
            full_message = f"{message} [{default}]: "
        else:
            full_message = f"{message}: "

        response = input(full_message).strip()
        return response or default or ""

    def _prompt_choice(self, message: str, choices: list[str], default: Optional[str] = None) -> str:
        """
        Prompt user to choose from a list.

        Args:
            message: Prompt message
            choices: Valid choices
            default: Default choice

        Returns:
            User's choice (validated)
        """
        while True:
            response = self._prompt(message, default)
            if response in choices:
                return response
            else:
                self.console.print(f"Invalid choice. Please choose from: {', '.join(choices)}", style="red")

    def _confirm(self, message: str, default: bool = True) -> bool:
        """
        Ask user for yes/no confirmation.

        Args:
            message: Confirmation message
            default: Default if user presses Enter

        Returns:
            True for yes, False for no
        """
        default_str = "Y/n" if default else "y/N"
        response = input(f"{message} ({default_str}): ").lower().strip()

        if not response:
            return default

        return response in ['y', 'yes']

    def _interactive_menu(self, message: str, choices: list[tuple[str, str]], default_index: int = 0) -> str:
        """
        Display an interactive menu with arrow key navigation.

        Args:
            message: Prompt message
            choices: List of (key, description) tuples
            default_index: Index of default choice

        Returns:
            Selected choice key
        """
        try:
            # Check if interactive mode is supported
            if not HAS_TERMIOS or not sys.stdin.isatty():
                # Fall back to numbered choice if not supported
                return self._numbered_menu(message, choices, default_index)

            selected = default_index

            while True:
                # Clear screen and redraw menu
                self.console.clear()
                self.console.print(f"\n{message}\n", style="bold")
                self.console.print("Use ↑/↓ arrow keys to navigate, Enter to select, or type a number:\n", style="dim")

                for i, (key, desc) in enumerate(choices):
                    # Add blank line before each option (except first)
                    if i > 0:
                        self.console.print()

                    # Handle multi-line descriptions
                    if '\n' in desc:
                        lines = desc.split('\n')
                        if i == selected:
                            self.console.print(f"  → {key}. {lines[0]}", style="cyan bold")
                            for line in lines[1:]:
                                self.console.print(f"     {line}", style="cyan")
                        else:
                            self.console.print(f"    {key}. {lines[0]}", style="white")
                            for line in lines[1:]:
                                self.console.print(f"       {line}", style="dim")
                    else:
                        if i == selected:
                            self.console.print(f"  → {key}. {desc}", style="cyan bold")
                        else:
                            self.console.print(f"    {key}. {desc}", style="white")

                # Get user input
                key_input = self._getch()

                if key_input == '\r' or key_input == '\n':  # Enter
                    return choices[selected][0]
                elif key_input == '\x1b':  # Arrow keys start with ESC
                    next1 = self._getch()
                    next2 = self._getch()
                    if next1 == '[':
                        if next2 == 'A':  # Up arrow
                            selected = (selected - 1) % len(choices)
                        elif next2 == 'B':  # Down arrow
                            selected = (selected + 1) % len(choices)
                elif key_input.isdigit():  # Direct number input
                    # Check if this is a valid choice
                    for i, (key, _) in enumerate(choices):
                        if key == key_input:
                            return key
                elif key_input in ['\x03', '\x04']:  # Ctrl+C or Ctrl+D
                    raise KeyboardInterrupt

        except (ImportError, AttributeError, OSError):
            # Fall back to numbered menu if arrow keys don't work
            return self._numbered_menu(message, choices, default_index)

    def _numbered_menu(self, message: str, choices: list[tuple[str, str]], default_index: int = 0) -> str:
        """
        Display a numbered menu (fallback for non-interactive terminals).

        Args:
            message: Prompt message
            choices: List of (key, description) tuples
            default_index: Index of default choice

        Returns:
            Selected choice key
        """
        self.console.print(f"\n{message}\n", style="bold")

        for i, (key, desc) in enumerate(choices):
            # Add blank line before each option (except first)
            if i > 0:
                self.console.print()

            marker = " ← default" if key == choices[default_index][0] else ""

            # Handle multi-line descriptions
            if '\n' in desc:
                lines = desc.split('\n')
                self.console.print(f"  {key}. {lines[0]}{marker}", style="cyan" if marker else "white")
                for line in lines[1:]:
                    self.console.print(f"     {line}", style="dim")
            else:
                self.console.print(f"  {key}. {desc}{marker}", style="cyan" if marker else "white")

        default_key = choices[default_index][0]
        valid_keys = [k for k, _ in choices] + [""]

        choice = self._prompt_choice(
            f"\nEnter choice [{', '.join(k for k, _ in choices)}]",
            choices=valid_keys,
            default=default_key
        )

        return choice or default_key

    def _getch(self) -> str:
        """
        Get a single character from stdin without echoing.

        Returns:
            Single character
        """
        if not HAS_TERMIOS:
            # Fallback for Windows - use msvcrt
            try:
                import msvcrt
                return msvcrt.getch().decode('utf-8')
            except ImportError:
                # Ultimate fallback - just read normally
                return sys.stdin.read(1)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
