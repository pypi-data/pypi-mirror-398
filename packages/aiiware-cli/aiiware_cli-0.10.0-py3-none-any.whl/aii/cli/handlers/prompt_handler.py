# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Prompt Library command handler (v0.6.1).

Handles Tier 1 (local) prompt operations:
- prompt list (discovery) - Local
- prompt show (details) - Local
- prompt validate (syntax check) - Local
- prompt use (execution) - Tier 2 via server

This replaces the old template commands with the new Prompt Library system.
"""


from typing import Any
from pathlib import Path

from aii.core.prompt_engine import (
    TemplateEngine,
    TemplateNotFoundError,
    MissingVariableError,
)
from aii.cli.command_router import CommandRoute


async def handle_prompt_command(route: CommandRoute, config_manager: Any, output_config: Any) -> int:
    """
    Handle prompt commands (v0.6.1 Prompt Library).

    Subcommands:
    - list: List available prompts (local, no server)
    - show: Show prompt details (local, no server)
    - validate: Validate custom prompt (local, no server)
    - use: Execute prompt with variables (requires server)

    Args:
        route: Command route with subcommand and args
        config_manager: Configuration manager
        output_config: Output configuration

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Parse subcommand
        if not route.subcommand:
            _print_prompt_help()
            return 1

        subcommand = route.subcommand
        args = route.args or {}

        # Initialize prompt engine
        engine = TemplateEngine()

        # Route to appropriate handler
        if subcommand == "list":
            return await _handle_list(engine, args, output_config)
        elif subcommand == "show":
            return await _handle_show(engine, args, output_config)
        elif subcommand == "validate":
            return await _handle_validate(engine, args, output_config)
        elif subcommand == "use":
            return await _handle_use(engine, args, config_manager, output_config)
        elif subcommand == "create":
            return await _handle_create(engine, args, output_config)
        else:
            print(f"❌ Unknown prompt subcommand: {subcommand}")
            _print_prompt_help()
            return 1

    except Exception as e:
        print(f"❌ Prompt command failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_list(engine: TemplateEngine, args: dict, output_config: Any) -> int:
    """Handle 'aii prompt list' command."""
    try:
        # Get filters from args
        category = args.get("category")
        tag = args.get("tag")
        verbose = args.get("verbose", False)
        user_only = args.get("user_only", False)
        builtin_only = args.get("builtin_only", False)

        # List prompts
        prompts = engine.list_templates(
            category=category,
            tag=tag,
            user_only=user_only,
            builtin_only=builtin_only,
        )

        if not prompts:
            print("No prompts found.")
            return 0

        # Format output
        output = _format_prompt_list(prompts, verbose, output_config)
        print(output)

        return 0

    except Exception as e:
        print(f"❌ Error listing prompts: {e}")
        return 1


async def _handle_show(engine: TemplateEngine, args: dict, output_config: Any) -> int:
    """Handle 'aii prompt show <name>' command."""
    try:
        # Get prompt name
        prompt_name = args.get("prompt_name") or args.get("name")
        if not prompt_name:
            print("❌ Missing prompt name")
            print("\nUsage: aii prompt show <name>")
            print("\nExample:")
            print("  aii prompt show tweet-launch")
            return 1

        # Load prompt
        try:
            prompt = engine.load_template(prompt_name)
        except TemplateNotFoundError:
            print(f"❌ Prompt not found: {prompt_name}")
            print("\nAvailable prompts:")
            print("  aii prompt list")
            return 1

        # Format output
        output = _format_prompt_details(prompt, output_config)
        print(output)

        return 0

    except Exception as e:
        print(f"❌ Error showing prompt: {e}")
        return 1


async def _handle_validate(engine: TemplateEngine, args: dict, output_config: Any) -> int:
    """Handle 'aii prompt validate <file>' command (enhanced in v0.6.2).

    Supports both:
    - Full file path: aii prompt validate ~/.aii/prompts/development/code-review.yaml
    - Prompt name: aii prompt validate word2 (searches all categories)
    """
    try:
        # Get file path or name
        file_path = args.get("file_path") or args.get("file")
        if not file_path:
            print("❌ Missing file path or prompt name")
            print("\nUsage: aii prompt validate <file_or_name>")
            print("\nExamples:")
            print("  aii prompt validate word2                              # Search by name")
            print("  aii prompt validate ~/.aii/prompts/development/code-review.yaml  # Full path")
            return 1

        # Try to resolve path
        path = Path(file_path).expanduser()

        # If file doesn't exist and looks like a name (not a path), search for it
        if not path.exists() and '/' not in file_path:
            # Search for prompt by name across all categories
            prompts_dir = Path.home() / ".aii" / "prompts"
            found_paths = []

            if prompts_dir.exists():
                # Search in all subdirectories
                for category_dir in prompts_dir.iterdir():
                    if category_dir.is_dir():
                        potential_path = category_dir / f"{file_path}.yaml"
                        if potential_path.exists():
                            found_paths.append(potential_path)

            if len(found_paths) == 0:
                print(f"❌ Prompt not found: {file_path}")
                print(f"\nSearched in: {prompts_dir}/*/")
                print("\nUsage:")
                print("  aii prompt validate <name>       # e.g., word2")
                print("  aii prompt validate <path>       # e.g., ~/.aii/prompts/education/word2.yaml")
                return 1
            elif len(found_paths) == 1:
                path = found_paths[0]
                print(f"Found: {path.relative_to(Path.home())}")
                print()
            else:
                # Multiple prompts with same name in different categories
                print(f"❌ Multiple prompts named '{file_path}' found:")
                for p in found_paths:
                    print(f"  - {p.relative_to(Path.home())}")
                print(f"\nPlease specify the full path or category:")
                print(f"  aii prompt validate {found_paths[0].relative_to(Path.home())}")
                return 1

        # Load and validate prompt with enhanced error reporting (v0.6.2)
        result = engine.validate_prompt_file(path)

        # Use new format_errors method for detailed error display (v0.6.2)
        if not result.is_valid:
            print(result.format_errors())
            return 1
        else:
            # Success message
            print("✅ Validation passed\n")
            print(f"Prompt file: {file_path}")
            # Try to load and show some metadata
            try:
                prompt = engine._parse_template(path)
                print(f"Name: {prompt.name}")
                print(f"Category: {prompt.category}")
                if prompt.system_prompt:
                    print(f"System prompt: {len(prompt.system_prompt)} chars")
                elif prompt.template:
                    print(f"Template: {len(prompt.template)} chars")
            except Exception:
                pass  # Just show validation passed if metadata fails
            return 0

    except Exception as e:
        print(f"❌ Error validating prompt: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_create(engine: TemplateEngine, args: dict, output_config: Any) -> int:
    """Handle 'aii prompt create' command - interactive wizard (v0.6.2)."""
    from .prompt_create import create_prompt_wizard

    try:
        return create_prompt_wizard()
    except KeyboardInterrupt:
        # Wizard already handled and displayed the cancellation message
        # Just return the error code without re-raising
        return 1
    except EOFError:
        # Wizard already handled and displayed the EOF message
        return 1
    except Exception as e:
        print(f"❌ Error creating prompt: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def _handle_use(engine: TemplateEngine, args: dict, config_manager: Any, output_config: Any) -> int:
    """Handle 'aii prompt use <name> [--vars]' command."""
    from aii.cli.client import AiiCLIClient

    try:
        # Get prompt name
        prompt_name = args.get("prompt_name") or args.get("name")
        if not prompt_name:
            print("❌ Missing prompt name")
            print("\nUsage: aii prompt use <name> [--var1 value1] [--var2 value2]")
            print("\nExample:")
            print("  aii prompt use tweet-launch --product 'Aii CLI'")
            return 1

        # Load prompt to validate it exists and check variables
        try:
            prompt = engine.load_template(prompt_name)
        except TemplateNotFoundError:
            print(f"❌ Prompt not found: {prompt_name}")
            print("\nAvailable prompts:")
            print("  aii prompt list")
            return 1

        # Collect variables from args
        # Parse extra_vars from REMAINDER (list of strings like ['--product', 'Aii', '--version', '1.0'])
        variables = {}
        unrecognized_args = []  # Track non-flag arguments
        extra_vars = args.get("extra_vars", [])

        # Output mode flags that should be filtered out (handled by argparse at parent level)
        output_mode_flags = {"--clean", "--standard", "--thinking", "--minimal", "--verbose", "--debug"}

        if extra_vars:
            # Parse --key value pairs
            i = 0
            while i < len(extra_vars):
                arg = extra_vars[i]
                if arg.startswith("--"):
                    # Skip output mode flags (they're handled by output_config)
                    if arg in output_mode_flags:
                        i += 1
                        continue

                    key = arg[2:]  # Remove --
                    # Check if next item is the value (not another flag)
                    if i + 1 < len(extra_vars) and not extra_vars[i + 1].startswith("--"):
                        variables[key] = extra_vars[i + 1]
                        i += 2
                    else:
                        # Flag without value (boolean flag)
                        variables[key] = True
                        i += 1
                else:
                    # Collect non-flag arguments for warning
                    unrecognized_args.append(arg)
                    i += 1

        # Also collect from regular args (for backwards compatibility)
        skip_keys = {"prompt_name", "name", "command", "subcommand", "prompt_action",
                     "category", "tag", "verbose", "user_only", "builtin_only", "file_path", "file", "extra_vars"}
        for k, v in args.items():
            if k not in skip_keys and v is not None:
                variables[k] = str(v)

        # v0.6.1 Dual-Mode System: Handle based on input_type
        from aii.core.prompt_engine import PromptInputType

        if prompt.input_type == PromptInputType.NATURAL_LANGUAGE:
            # Natural Language Mode: User provides free-form text + optional custom flags
            # Examples:
            #   aii prompt use word-explanation prompt
            #   aii prompt use word-explanation prompt --lang Chinese
            #   aii prompt use word-explanation algorithm --lang zh --clean

            output_mode_flags = {"--clean", "--standard", "--thinking", "--minimal", "--verbose", "--debug"}
            extra_vars = args.get("extra_vars") or []

            # Parse custom flags (--key value) and natural language parts
            natural_language_parts = []
            custom_params = []  # Store as ["--lang Chinese", "--format json"]
            i = 0
            while i < len(extra_vars):
                arg = extra_vars[i]

                # Skip output mode flags
                if arg in output_mode_flags:
                    i += 1
                    continue

                # Check if this is a custom flag (--key)
                if arg.startswith("--"):
                    key = arg
                    # Check if next item is the value (not another flag)
                    if i + 1 < len(extra_vars) and not extra_vars[i + 1].startswith("--"):
                        value = extra_vars[i + 1]
                        custom_params.append(f"{key} {value}")
                        i += 2
                    else:
                        # Flag without value (boolean flag)
                        custom_params.append(key)
                        i += 1
                else:
                    # This is natural language text
                    natural_language_parts.append(arg)
                    i += 1

            # Build user_input: natural language + custom parameters
            if not natural_language_parts:
                print(f"❌ Natural language prompt requires input text")
                print(f"\n💡 Usage: aii prompt use {prompt_name} <your text> [--param value]")

                # Show description and examples
                print(f"\n📋 Prompt: {prompt.description}")
                if prompt.examples:
                    print(f"\n📝 Examples:")
                    for ex in prompt.examples[:3]:  # Show up to 3 examples
                        print(f"  {ex.command}")

                return 1

            # Assemble user input with custom params clearly marked
            user_input = " ".join(natural_language_parts)
            if custom_params:
                # Append custom parameters in a clear format for LLM to parse
                user_input += "\n\nParameters: " + ", ".join(custom_params)

            system_prompt = prompt.system_prompt

            if not system_prompt:
                print(f"❌ Natural language prompt missing system_prompt field")
                return 1

        else:  # PromptInputType.TEMPLATE
            # Template Mode: User provides --flag value pairs

            # Warn about unrecognized arguments (helpful for users who provide free-form text)
            if unrecognized_args:
                print(f"⚠️  Ignoring unrecognized arguments: {' '.join(unrecognized_args)}")
                print(f"\n💡 Tip: This prompt expects variables in --name value format")
                print(f"\nAvailable variables for '{prompt_name}':")
                for var in prompt.variables:
                    req_str = "required" if var.required else "optional"
                    example_str = f" (e.g., '{var.example}')" if var.example else ""
                    print(f"  --{var.name} ({req_str}): {var.description}{example_str}")

                # Show example
                if prompt.examples and len(prompt.examples) > 1:
                    print(f"\n📝 Example:")
                    print(f"  {prompt.examples[1].command}")
                print()  # Empty line for readability

            # Validate required variables
            missing = engine.validate_variables(prompt, variables)
            if missing:
                print(f"❌ Missing required variables: {', '.join(missing)}")
                print(f"\n💡 Usage: aii prompt use {prompt_name} {' '.join([f'--{v} <value>' for v in missing])}")

                # Show variable details
                print(f"\n📋 Required variables for '{prompt_name}':")
                for var in prompt.variables:
                    if var.required:
                        example_str = f" (e.g., '{var.example}')" if var.example else ""
                        print(f"  --{var.name}: {var.description}{example_str}")

                # Show example if available
                if prompt.examples:
                    print(f"\n📝 Example:")
                    print(f"  {prompt.examples[0].command}")

                return 1

            # Substitute variables into template
            assembled_prompt = engine.substitute_variables(prompt.template, variables)

        # Execute via server with spinner
        import sys
        from aii.cli.spinner import Spinner

        client = AiiCLIClient(config_manager)

        # Get output mode from output_config (respects CLI flags like --clean, --standard, --thinking)
        # Default to CLEAN for prompts if not specified
        #
        # IMPORTANT: Due to argparse.REMAINDER capturing all args after prompt name,
        # the --clean/--standard/--thinking flags are captured in extra_vars and never
        # reach the parent parser. So we check extra_vars for these flags.
        output_mode = "CLEAN"  # Default for prompts

        # Check if user specified output mode flags in extra_vars
        if "--thinking" in (args.get("extra_vars", []) or []):
            output_mode = "THINKING"
        elif "--standard" in (args.get("extra_vars", []) or []):
            output_mode = "STANDARD"
        elif "--clean" in (args.get("extra_vars", []) or []):
            output_mode = "CLEAN"
        elif hasattr(output_config, 'output_format'):
            # Fall back to output_config if no explicit flag in extra_vars
            output_mode = output_config.output_format.value.upper()

        # Start processing spinner (consistent with other commands)
        processing_spinner = Spinner("Processing...", stream=sys.stdout)
        await processing_spinner.start()

        # Execute based on input_type
        if prompt.input_type == PromptInputType.NATURAL_LANGUAGE:
            # Natural Language Mode: Call LLM directly with system_prompt + user_input
            result = await client.execute_with_system_prompt(
                system_prompt=system_prompt,
                user_input=user_input,
                output_mode=output_mode,
                spinner=processing_spinner,
                prompt_name=prompt_name  # Pass prompt name for metadata display
            )
        else:  # PromptInputType.TEMPLATE
            # Template Mode: Execute assembled prompt via universal_generate
            result = await client.execute_function(
                function_name="universal_generate",
                parameters={"request": assembled_prompt, "format": "auto"},
                output_mode=output_mode,
                spinner=processing_spinner
            )

        # Ensure spinner is stopped
        # v0.6.2: Don't clear if streaming occurred (output already displayed)
        streaming_occurred = result.get("_streaming_occurred", False)
        await processing_spinner.stop(clear=not streaming_occurred)

        # Display result to user if streaming didn't occur
        if result.get("success"):
            # Check if tokens were already printed during streaming
            if not streaming_occurred:
                # No streaming occurred, print the complete result
                # Extract result from various possible fields
                output = result.get("result") or result.get("data", {}).get("clean_output") or result.get("data", {}).get("response") or ""
                if output:
                    print(output, flush=True)
            # If streaming occurred, output was already printed (no extra newline needed here)

            # Print session summary if output mode is STANDARD or THINKING
            if output_mode in ["STANDARD", "THINKING"] and result.get("metadata"):
                # No need for print() here - print_session_summary already adds blank line (main.py:92)
                from aii.main import print_session_summary
                print_session_summary(result.get("metadata", {}), output_mode)

            return 0
        else:
            error_msg = result.get('error') or result.get('result', 'Unknown error')
            print(f"❌ Failed to execute prompt: {error_msg}")
            return 1

    except Exception as e:
        print(f"❌ Error executing prompt: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _format_prompt_list(prompts: list, verbose: bool, output_config: Any) -> str:
    """Format prompt list for display."""
    from collections import defaultdict

    lines = [f"📚 Available Prompts ({len(prompts)} total)\n"]

    # Category icons
    icons = {
        "business": "📅",
        "content": "📝",
        "development": "💻",
        "social": "🐦",
        "marketing": "📣",
        "productivity": "✅",
        "general": "📄",
    }

    # Group by category
    by_category = defaultdict(list)
    for p in prompts:
        by_category[p.category].append(p)

    # Format each category
    for category in sorted(by_category.keys()):
        category_prompts = sorted(by_category[category], key=lambda p: p.name)
        icon = icons.get(category, "📄")

        lines.append(f"{icon} {category.title()} ({len(category_prompts)}):")

        for p in category_prompts:
            if verbose:
                # Verbose mode: show more details
                author_str = f" by {p.author}" if p.author else ""
                tags_str = f" [{', '.join(p.tags)}]" if p.tags else ""
                lines.append(f"  {p.name}{author_str}")
                lines.append(f"    {p.description}{tags_str}")
            else:
                # Normal mode: compact listing
                lines.append(f"  {p.name:25s} - {p.description}")

        lines.append("")  # Blank line between categories

    lines.append("Use: aii prompt show <name> for details")
    lines.append("Use: aii prompt use <name> [--var value] to execute")

    return "\n".join(lines)


def _format_prompt_details(prompt: Any, output_config: Any) -> str:
    """Format prompt details for display."""
    lines = [f"📄 Prompt: {prompt.name}\n"]

    # Metadata
    lines.append(f"Category: {prompt.category}")
    lines.append(f"Description: {prompt.description}")

    if prompt.author:
        lines.append(f"Author: {prompt.author}")
    if prompt.version:
        lines.append(f"Version: {prompt.version}")
    if prompt.tags:
        lines.append(f"Tags: {', '.join(prompt.tags)}")

    # Variables
    if prompt.variables:
        lines.append(f"\n📋 Variables:")
        for var in prompt.variables:
            required_str = "(required)" if var.required else "(optional)"
            default_str = f", default: {var.default}" if var.default else ""
            example_str = f", e.g., '{var.example}'" if var.example else ""

            lines.append(f"  --{var.name} {required_str}")
            lines.append(f"    {var.description}{default_str}{example_str}")
    else:
        lines.append(f"\n📋 Variables: none")

    # Examples
    if prompt.examples:
        lines.append(f"\n📝 Example Usage:")
        for ex in prompt.examples:
            if ex.description:
                lines.append(f"  # {ex.description}")
            lines.append(f"  {ex.command}")
            if ex.output:
                lines.append(f"  # Expected output: {ex.output}")
            lines.append("")  # Blank line between examples

    # Location
    if prompt.path:
        lines.append(f"\n📂 Location: {prompt.path}")

    return "\n".join(lines)


def _format_validation_result(result: Any, file_path: str, output_config: Any) -> str:
    """Format validation result for display."""
    lines = []

    if result.is_valid:
        lines.append(f"✅ Prompt is valid: {file_path}\n")
    else:
        lines.append(f"❌ Prompt validation failed: {file_path}\n")

    # Errors
    if result.errors:
        lines.append("Errors:")
        for error in result.errors:
            lines.append(f"  • {error}")
        lines.append("")

    # Warnings
    if result.warnings:
        lines.append("⚠️  Warnings:")
        for warning in result.warnings:
            lines.append(f"  • {warning}")
        lines.append("")

    # Suggestions
    if result.suggestions:
        lines.append("💡 Suggestions:")
        for suggestion in result.suggestions:
            lines.append(f"  • {suggestion}")
        lines.append("")

    return "\n".join(lines)


def _print_prompt_help():
    """Print prompt command help."""
    help_text = """
❌ Missing prompt subcommand

Usage:
  aii prompt list [OPTIONS]              # List available prompts
  aii prompt show <name>                 # Show prompt details
  aii prompt use <name> [--vars]         # Execute prompt
  aii prompt validate <file>             # Validate custom prompt

List Options:
  --category <cat>      Filter by category (business, content, development, social, marketing, productivity)
  --tag <tag>           Filter by tag
  --verbose             Show detailed information
  --user-only           Show only user prompts
  --builtin-only        Show only built-in prompts

Examples:
  aii prompt list                                    # List all prompts
  aii prompt list --category social                  # List social media prompts
  aii prompt show tweet-launch                       # Show tweet-launch details
  aii prompt use tweet-launch --product "Aii CLI"    # Execute tweet-launch
  aii prompt validate ~/.aii/prompts/custom.yaml     # Validate custom prompt

For more information: https://docs.aii.dev/prompts
    """
    print(help_text)
