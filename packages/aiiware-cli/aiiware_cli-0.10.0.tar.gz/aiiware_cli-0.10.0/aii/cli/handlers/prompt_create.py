# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Interactive prompt creation wizard (v0.6.2).

This module provides an interactive wizard for creating custom prompts:
- Step 1: Basic Information (name, description)
- Step 2: Category Selection (6 categories)
- Step 3: System Prompt (multi-line input)
- Step 4: Examples (optional, repeatable)
- Step 5: Review & Save

The wizard uses the rich library for interactive UI and validates inputs inline.
"""


from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
import yaml
import re

from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel


@dataclass
class WizardState:
    """State container for prompt creation wizard.

    Stores user inputs collected during the 5-step wizard flow.
    """
    # Step 1: Basic Information
    name: str = ""
    description: str = ""

    # Step 2: Category
    category: str = ""

    # Step 3: System Prompt
    system_prompt: str = ""

    # Step 4: Examples
    examples: List[Dict[str, str]] = field(default_factory=list)

    # Metadata (defaults)
    author: str = "User"
    version: str = "1.0"
    input_type: str = "natural_language"

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert wizard state to YAML-serializable dictionary.

        Returns:
            Dictionary ready for YAML serialization
        """
        data = {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "author": self.author,
            "version": self.version,
            "input_type": self.input_type,
            "system_prompt": self.system_prompt,
        }

        if self.examples:
            data["examples"] = self.examples

        # Add empty tags list for consistency
        data["tags"] = []

        return data


class PromptCreationWizard:
    """Interactive wizard for creating custom prompts (v0.6.2).

    Provides a 5-step guided experience:
    1. Basic Information (name, description)
    2. Category Selection
    3. System Prompt (multi-line)
    4. Examples (optional)
    5. Review & Save
    """

    # Available categories
    CATEGORIES = [
        "business",
        "content",
        "development",
        "social",
        "marketing",
        "productivity"
    ]

    def __init__(self, console: Optional[Console] = None):
        """Initialize wizard.

        Args:
            console: Rich console instance (creates new if not provided)
        """
        self.console = console or Console()
        self.state = WizardState()

    def run(self) -> int:
        """Run the 5-step wizard flow with graceful error handling.

        Returns:
            Exit code (0 = success, 1 = error/cancelled)
        """
        # Display welcome banner
        self.console.print(Panel(
            "[bold]📝 Create Custom Prompt - Interactive Wizard[/bold]",
            expand=False
        ))
        self.console.print()
        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")
        self.console.print()

        try:
            # Step 1: Basic Information
            self.state = self.step_1_basic_info(self.state)

            # Step 2: Category
            self.state = self.step_2_category(self.state)

            # Step 3: System Prompt
            self.state = self.step_3_system_prompt(self.state)

            # Step 4: Examples (optional)
            self.state = self.step_4_examples(self.state)

            # Step 5: Review & Save
            return self.step_5_review_and_save(self.state)

        except KeyboardInterrupt:
            # User pressed Ctrl+C - graceful cancellation
            self.console.print()
            self.console.print("[yellow]────────────────────────────────────────────────────────────[/yellow]")
            self.console.print("[yellow]⚠️  Wizard cancelled by user (Ctrl+C)[/yellow]")
            self.console.print()
            self.console.print("[dim]No prompt was created. You can run 'aii prompt create' again anytime.[/dim]")
            self.console.print()
            return 1

        except EOFError:
            # Unexpected EOF (e.g., stdin closed)
            self.console.print()
            self.console.print("[yellow]────────────────────────────────────────────────────────────[/yellow]")
            self.console.print("[yellow]⚠️  Input stream closed unexpectedly[/yellow]")
            self.console.print()
            self.console.print("[dim]No prompt was created. Ensure stdin is available for interactive input.[/dim]")
            self.console.print()
            return 1

        except Exception as e:
            # Unexpected error - show details for debugging
            self.console.print()
            self.console.print("[red]────────────────────────────────────────────────────────────[/red]")
            self.console.print(f"[red]❌ Unexpected error: {e}[/red]")
            self.console.print()
            self.console.print("[dim]Traceback (for debugging):[/dim]")
            import traceback
            traceback.print_exc()
            self.console.print()
            self.console.print("[dim]Please report this issue at: https://github.com/aiiware/aii-cli/issues[/dim]")
            self.console.print()
            return 1

    def step_1_basic_info(self, state: WizardState) -> WizardState:
        """Step 1: Collect prompt name and description.

        Args:
            state: Current wizard state

        Returns:
            Updated wizard state
        """
        self.console.print("[bold]Step 1/5: Basic Information[/bold]")
        self.console.print("─" * 60)
        self.console.print()

        # Prompt name with validation
        self.console.print("[dim]Examples: translate, code-review-security, daily-standup-notes[/dim]")
        self.console.print()
        while True:
            name = Prompt.ask("Prompt name (lowercase, use hyphens for multi-word)")

            # Validate format (lowercase letters, numbers, optional hyphens)
            if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
                self.console.print("[red]❌ Invalid format. Use lowercase letters, numbers, and hyphens only[/red]")
                self.console.print("[dim]Valid: word, translate, code-review, daily-standup[/dim]")
                self.console.print("[dim]Invalid: Word (uppercase), word_case (underscore), word case (space)[/dim]")
                continue

            # Check if already exists
            if self._prompt_exists(name):
                self.console.print(f"[yellow]⚠️  Prompt '{name}' already exists[/yellow]")
                overwrite = Confirm.ask("Overwrite existing prompt?", default=False)
                if not overwrite:
                    continue

            state.name = name
            break

        # Description with validation
        self.console.print("[dim]Examples: 'Security-focused code review with OWASP checks'[/dim]")
        self.console.print("[dim]           'Generate daily standup notes from git commits'[/dim]")
        self.console.print()
        while True:
            description = Prompt.ask("Short description (1 line)")

            if len(description) < 10:
                self.console.print("[red]❌ Description too short (min 10 chars)[/red]")
                continue

            if len(description) > 200:
                self.console.print("[red]❌ Description too long (max 200 chars)[/red]")
                continue

            state.description = description
            break

        self.console.print()
        return state

    def step_2_category(self, state: WizardState) -> WizardState:
        """Step 2: Select prompt category (predefined or custom).

        Args:
            state: Current wizard state

        Returns:
            Updated wizard state
        """
        self.console.print("[bold]Step 2/5: Category[/bold]")
        self.console.print("─" * 60)
        self.console.print()

        # Display categories with numbers (predefined + custom option)
        self.console.print("Select category:")
        for i, category in enumerate(self.CATEGORIES, 1):
            self.console.print(f"  {i}. {category}")
        self.console.print(f"  {len(self.CATEGORIES) + 1}. [cyan]custom[/cyan] (enter your own)")
        self.console.print()

        # Get selection
        while True:
            choice = Prompt.ask(
                "Category",
                choices=[str(i) for i in range(1, len(self.CATEGORIES) + 2)]
            )
            category_index = int(choice) - 1

            if category_index < len(self.CATEGORIES):
                # Predefined category
                state.category = self.CATEGORIES[category_index]
            else:
                # Custom category
                self.console.print()
                self.console.print("[dim]Examples: education, research, data-analysis, machine-learning[/dim]")
                while True:
                    custom_category = Prompt.ask("Enter custom category (lowercase, use hyphens if needed)")

                    # Validate format (lowercase letters, numbers, optional hyphens)
                    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', custom_category):
                        self.console.print("[red]❌ Use lowercase letters, numbers, and hyphens only[/red]")
                        continue

                    # Warn if too long
                    if len(custom_category) > 30:
                        self.console.print("[yellow]⚠️  Category name is quite long[/yellow]")
                        confirm = Confirm.ask("Use this category anyway?", default=True)
                        if not confirm:
                            continue

                    state.category = custom_category
                    break
            break

        self.console.print(f"[green]✓ Selected: {state.category}[/green]")
        self.console.print()
        return state

    def step_3_system_prompt(self, state: WizardState) -> WizardState:
        """Step 3: Collect multi-line system prompt.

        Args:
            state: Current wizard state

        Returns:
            Updated wizard state
        """
        self.console.print("[bold]Step 3/5: System Prompt[/bold]")
        self.console.print("─" * 60)
        self.console.print()
        self.console.print("Enter the system prompt (behavioral instructions for AI).")
        self.console.print("[dim]Example: 'You are a senior software engineer. Review code for bugs,[/dim]")
        self.console.print("[dim]         security issues, and best practices. Provide actionable feedback.'[/dim]")
        self.console.print()
        self.console.print("[dim](Type or paste. Press Ctrl+D when done, Ctrl+C to cancel)[/dim]")
        self.console.print()

        # Multi-line input with readline
        lines = []

        try:
            while True:
                try:
                    line = input("> ")
                    lines.append(line)
                except EOFError:
                    # Ctrl+D pressed - end input
                    break
        except KeyboardInterrupt:
            # Ctrl+C pressed - re-raise to cancel wizard
            raise

        system_prompt = "\n".join(lines).strip()

        # Validate not empty
        if not system_prompt:
            self.console.print("[red]❌ System prompt cannot be empty[/red]")
            return self.step_3_system_prompt(state)  # Retry

        self.console.print()
        self.console.print(f"[green]✓ System prompt captured ({len(system_prompt)} chars)[/green]")
        self.console.print()

        state.system_prompt = system_prompt
        return state

    def step_4_examples(self, state: WizardState) -> WizardState:
        """Step 4: Collect usage examples (optional).

        Args:
            state: Current wizard state

        Returns:
            Updated wizard state
        """
        self.console.print("[bold]Step 4/5: Examples (Optional)[/bold]")
        self.console.print("─" * 60)
        self.console.print()
        self.console.print("[dim]Examples help users understand how to use your prompt[/dim]")
        self.console.print()

        examples = []

        while True:
            add_example = Confirm.ask("Add usage example?", default=False)

            if not add_example:
                break

            self.console.print()
            self.console.print("[dim]Description example: 'Review a Python file for security issues'[/dim]")
            description = Prompt.ask("Example description")

            self.console.print("[dim]Command example: 'aii prompt use code-review auth.py'[/dim]")
            command = Prompt.ask("Example command")

            examples.append({
                "description": description,
                "command": command
            })

            self.console.print(f"[green]✓ Example added[/green]")
            self.console.print()

        state.examples = examples
        self.console.print()
        return state

    def step_5_review_and_save(self, state: WizardState) -> int:
        """Step 5: Review prompt and save to YAML.

        Args:
            state: Current wizard state

        Returns:
            Exit code (0 = success, 1 = error)
        """
        self.console.print("[bold]Step 5/5: Review & Save[/bold]")
        self.console.print("─" * 60)
        self.console.print()
        self.console.print("Preview of your prompt:")
        self.console.print()

        # Display preview
        self.console.print(f"  [cyan]Name:[/cyan] {state.name}")
        self.console.print(f"  [cyan]Category:[/cyan] {state.category}")
        self.console.print(f"  [cyan]Description:[/cyan] {state.description}")
        self.console.print()
        self.console.print(f"  [cyan]System Prompt:[/cyan]")
        preview = state.system_prompt[:100] + "..." if len(state.system_prompt) > 100 else state.system_prompt
        self.console.print(f"  {preview}")
        self.console.print(f"  [dim]({len(state.system_prompt)} chars)[/dim]")
        self.console.print()
        self.console.print(f"  [cyan]Examples:[/cyan] {len(state.examples)}")
        self.console.print()

        # Confirm save
        save = Confirm.ask("Save this prompt?", default=True)

        if not save:
            self.console.print("[yellow]Prompt not saved[/yellow]")
            return 1

        # Generate YAML
        yaml_content = self._generate_yaml(state)

        # Validate structure (use engine validation)
        try:
            from ...core.prompt_engine import TemplateEngine
            engine = TemplateEngine()

            # Write to temp file and validate
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(yaml_content)
                temp_path = Path(f.name)

            result = engine.validate_prompt_file(temp_path)
            temp_path.unlink()  # Clean up temp file

            if not result.is_valid:
                self.console.print(f"[red]❌ Validation failed:[/red]")
                self.console.print(result.format_errors())
                return 1
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Could not validate: {e}[/yellow]")
            # Continue anyway - validation is optional

        # Write to file
        prompt_path = self._get_prompt_path(state.category, state.name)
        try:
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            prompt_path.write_text(yaml_content)
        except Exception as e:
            self.console.print(f"[red]❌ Failed to save: {e}[/red]")
            return 1

        # Success message
        self.console.print()
        self.console.print(f"[green]✅ Prompt saved to: {prompt_path}[/green]")
        self.console.print(f"[green]✅ Validation passed[/green]")
        self.console.print()
        self.console.print("[bold]💡 Try it now:[/bold]")
        self.console.print(f"   aii prompt use {state.name} \"your input here\"")
        self.console.print(f"   cat file.txt | aii prompt use {state.name}")
        self.console.print()

        return 0

    def _prompt_exists(self, name: str) -> bool:
        """Check if prompt already exists.

        Args:
            name: Prompt name

        Returns:
            True if prompt exists, False otherwise
        """
        # Check user prompts directory
        user_path = Path.home() / ".aii" / "prompts"

        # Check all category subdirectories
        for category in self.CATEGORIES:
            category_path = user_path / category / f"{name}.yaml"
            if category_path.exists():
                return True

        # Check flat directory (legacy)
        flat_path = user_path / f"{name}.yaml"
        if flat_path.exists():
            return True

        return False

    def _get_prompt_path(self, category: str, name: str) -> Path:
        """Get prompt file path (safe from path traversal).

        Args:
            category: Prompt category
            name: Prompt name

        Returns:
            Path to prompt file

        Raises:
            ValueError: If path is outside allowed directory
        """
        # Base directory (user's prompt directory)
        base_dir = Path.home() / ".aii" / "prompts"

        # Construct path
        prompt_path = base_dir / category / f"{name}.yaml"

        # Validate path is within base directory (security)
        try:
            resolved = prompt_path.resolve()
            if not str(resolved).startswith(str(base_dir.resolve())):
                raise ValueError(f"Invalid path: {prompt_path}")
        except Exception as e:
            raise ValueError(f"Path validation failed: {e}")

        return prompt_path

    def _generate_yaml(self, state: WizardState) -> str:
        """Generate YAML content from wizard state with pretty formatting.

        Uses custom formatting for better readability:
        - Multi-line strings use literal block style (|-)
        - Proper indentation for nested structures
        - No unnecessary line wrapping

        Args:
            state: Wizard state

        Returns:
            Pretty-formatted YAML string
        """
        yaml_data = state.to_yaml_dict()

        # Manual YAML formatting for better control
        lines = []

        # Helper function to format a single value
        def format_value(value, indent=0):
            """Format a value with proper YAML syntax."""
            spaces = "  " * indent

            if isinstance(value, str) and '\n' in value:
                # Multi-line string - use literal block style
                result = "|-\n"
                for line in value.split('\n'):
                    result += f"{spaces}  {line}\n"
                return result.rstrip() + "\n"
            elif isinstance(value, str):
                # Single-line string - quote if needed
                needs_quotes = any(c in value for c in [':', '#', '@', '!', '&', '*', '[', ']', '{', '}', '|', '>'])
                if needs_quotes or value.startswith(' ') or value.endswith(' '):
                    return f'"{value}"\n'
                return f"{value}\n"
            elif isinstance(value, list):
                if not value:
                    return "[]\n"
                # List of items
                result = "\n"
                for item in value:
                    if isinstance(item, dict):
                        # Dict item - format as YAML mapping
                        result += f"{spaces}-"
                        first = True
                        for k, v in item.items():
                            if first:
                                result += f" {k}: {v}\n"
                                first = False
                            else:
                                result += f"{spaces}  {k}: {v}\n"
                    else:
                        result += f"{spaces}- {item}\n"
                return result
            else:
                return f"{value}\n"

        # Format each field
        for key, value in yaml_data.items():
            formatted = format_value(value)
            if '\n' in formatted and formatted != "\n":
                # Multi-line or list
                lines.append(f"{key}: {formatted}")
            else:
                # Single-line
                lines.append(f"{key}: {formatted}")

        return "".join(lines)


def create_prompt_wizard() -> int:
    """Entry point for prompt creation wizard.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    wizard = PromptCreationWizard()
    return wizard.run()
