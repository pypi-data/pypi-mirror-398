# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Command-line completion support for AII CLI"""


import argparse
import os
from pathlib import Path
from typing import Any

try:
    import argcomplete

    ARGCOMPLETE_AVAILABLE = True
except ImportError:
    ARGCOMPLETE_AVAILABLE = False


class AIICompleter:
    """Custom completer for AII CLI commands"""

    def __init__(self, engine: Any = None):
        """Initialize completer with optional engine reference"""
        self.engine = engine

    def function_names_completer(
        self, prefix: str, parsed_args: Any, **kwargs
    ) -> list[str]:
        """Complete function names"""
        if not self.engine:
            # Return some common function names as fallback
            return ["git_commit", "git_diff", "translate", "explain", "summarize"]

        # Get actual function names from engine
        functions = self.engine.function_registry.list_functions()
        return [func.name for func in functions if func.name.startswith(prefix)]

    def config_keys_completer(
        self, prefix: str, parsed_args: Any, **kwargs
    ) -> list[str]:
        """Complete configuration keys"""
        config_keys = [
            "llm.provider",
            "llm.model",
            "llm.temperature",
            "web_search.enabled",
            "web_search.provider",
            "chat.auto_save",
            "chat.default_context_limit",
            "ui.color",
            "ui.emoji",
            "security.confirm_dangerous_operations",
        ]
        return [key for key in config_keys if key.startswith(prefix)]

    def file_path_completer(self, prefix: str, parsed_args: Any, **kwargs) -> list[str]:
        """Complete file paths"""
        try:
            path = Path(prefix)
            if path.is_dir():
                # Complete directory contents
                return [str(p) for p in path.iterdir() if str(p).startswith(prefix)]
            else:
                # Complete parent directory contents
                parent = path.parent
                if parent.exists():
                    name_start = path.name
                    return [
                        str(parent / p.name)
                        for p in parent.iterdir()
                        if p.name.startswith(name_start)
                    ]
        except Exception:
            pass

        return []

    def language_completer(self, prefix: str, parsed_args: Any, **kwargs) -> list[str]:
        """Complete programming language names"""
        languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "c",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "html",
            "css",
            "sql",
            "shell",
            "bash",
            "powershell",
        ]
        return [lang for lang in languages if lang.startswith(prefix)]

    def translation_language_completer(
        self, prefix: str, parsed_args: Any, **kwargs
    ) -> list[str]:
        """Complete translation language names"""
        languages = [
            "spanish",
            "french",
            "german",
            "italian",
            "portuguese",
            "chinese",
            "japanese",
            "korean",
            "arabic",
            "russian",
            "hindi",
            "dutch",
            "swedish",
            "norwegian",
            "danish",
            "finnish",
            "polish",
            "czech",
        ]
        return [lang for lang in languages if lang.startswith(prefix)]


def setup_completion(parser: argparse.ArgumentParser, engine: Any = None) -> None:
    """Setup command completion for the parser"""
    if not ARGCOMPLETE_AVAILABLE:
        return

    completer = AIICompleter(engine)

    # Add completion to subparsers if they exist
    if hasattr(parser, "_subparsers"):
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                for subparser_name, subparser in action.choices.items():
                    setup_subparser_completion(subparser, completer, subparser_name)

    # Enable argcomplete
    argcomplete.autocomplete(parser)


def setup_subparser_completion(
    parser: argparse.ArgumentParser, completer: AIICompleter, command: str
) -> None:
    """Setup completion for individual subparsers"""
    if not ARGCOMPLETE_AVAILABLE:
        return

    # Add completers based on command type
    for action in parser._actions:
        if hasattr(action, "dest"):
            if action.dest in ["file_path", "input_file", "output_file"]:
                action.completer = completer.file_path_completer
            elif action.dest in ["function_name", "function"]:
                action.completer = completer.function_names_completer
            elif action.dest in ["language", "programming_language"]:
                action.completer = completer.language_completer
            elif action.dest in ["target_language", "source_language"]:
                action.completer = completer.translation_language_completer
            elif action.dest == "config_key":
                action.completer = completer.config_keys_completer


def create_completion_script(shell: str = "bash", command_name: str = "aii") -> str:
    """Generate shell completion script"""
    if not ARGCOMPLETE_AVAILABLE:
        return f"# argcomplete not available - completion disabled for {shell}"

    if shell == "bash":
        return f"""
# AII CLI Bash Completion
# Add this to your ~/.bashrc or source it directly

_aii_completion() {{
    local IFS=$'\\n'
    COMPREPLY=( $(COMP_CWORD={command_name} argcomplete-{command_name} "${{COMP_WORDS[@]}}") )
}}

complete -F _aii_completion {command_name}
"""
    elif shell == "zsh":
        return f"""
# AII CLI Zsh Completion
# Add this to your ~/.zshrc or source it directly

autoload -U compinit
compinit

_aii_completion() {{
    eval "$(register-python-argcomplete {command_name})"
}}

compdef _aii_completion {command_name}
"""
    elif shell == "fish":
        return f"""
# AII CLI Fish Completion
# Add this to your ~/.config/fish/completions/{command_name}.fish

register-python-argcomplete --shell fish {command_name} | source
"""
    else:
        return f"# Unsupported shell: {shell}"


def install_completion(shell: str | None = None, command_name: str = "aii") -> bool:
    """Install shell completion for the current user"""
    if not ARGCOMPLETE_AVAILABLE:
        print(
            "Error: argcomplete package not available. Install with: pip install argcomplete"
        )
        return False

    if shell is None:
        # Auto-detect shell
        shell = Path(os.environ.get("SHELL", "/bin/bash")).name

    completion_script = create_completion_script(shell, command_name)

    try:
        if shell == "bash":
            completion_dir = Path.home() / ".bash_completion.d"
            completion_dir.mkdir(exist_ok=True)
            completion_file = completion_dir / f"{command_name}_completion.bash"

        elif shell == "zsh":
            completion_dir = Path.home() / ".zsh" / "completions"
            completion_dir.mkdir(parents=True, exist_ok=True)
            completion_file = completion_dir / f"_{command_name}"

        elif shell == "fish":
            completion_dir = Path.home() / ".config" / "fish" / "completions"
            completion_dir.mkdir(parents=True, exist_ok=True)
            completion_file = completion_dir / f"{command_name}.fish"

        else:
            print(f"Unsupported shell: {shell}")
            return False

        completion_file.write_text(completion_script)
        print(f"✅ Completion script installed to: {completion_file}")
        print(
            "Restart your shell or source the completion file to enable tab completion."
        )

        return True

    except Exception as e:
        print(f"Failed to install completion: {e}")
        return False


def validate_input_format(input_text: str, expected_format: str) -> tuple[bool, str]:
    """Validate input against expected format"""
    if expected_format == "file_path":
        path = Path(input_text)
        if not path.exists():
            return False, f"File not found: {input_text}"
        return True, ""

    elif expected_format == "language":
        valid_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "go",
            "rust",
            "spanish",
            "french",
            "german",
            "italian",
            "portuguese",
            "chinese",
        ]
        if input_text.lower() not in valid_languages:
            return False, f"Unsupported language: {input_text}"
        return True, ""

    elif expected_format == "email":
        import re

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, input_text):
            return False, f"Invalid email format: {input_text}"
        return True, ""

    elif expected_format == "url":
        import re

        url_pattern = r"^https?://.+"
        if not re.match(url_pattern, input_text):
            return False, f"Invalid URL format: {input_text}"
        return True, ""

    # Default: accept any input
    return True, ""


class ValidationError(Exception):
    """Exception raised for input validation errors"""

    pass


def validate_and_complete_args(args: Any, engine: Any = None) -> Any:
    """Post-process and validate parsed arguments"""
    # Validate file paths
    for attr_name in dir(args):
        if "file" in attr_name.lower() or "path" in attr_name.lower():
            file_path = getattr(args, attr_name, None)
            if file_path and not Path(file_path).exists():
                raise ValidationError(f"File not found: {file_path}")

    # Validate function names if engine available
    if engine and hasattr(args, "function_name"):
        function_name = getattr(args, "function_name", None)
        if function_name and not engine.function_registry.function_exists(
            function_name
        ):
            available_functions = [
                f.name for f in engine.function_registry.list_functions()
            ]
            raise ValidationError(
                f"Unknown function: {function_name}. "
                f"Available functions: {', '.join(available_functions)}"
            )

    return args
