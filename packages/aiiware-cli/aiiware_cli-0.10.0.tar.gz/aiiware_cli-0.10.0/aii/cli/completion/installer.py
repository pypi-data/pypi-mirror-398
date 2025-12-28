# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Shell completion installer.

This module handles installation and uninstallation of shell completion scripts
for bash, zsh, and fish.
"""


import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, List

from .generator import CompletionGenerator


class CompletionInstaller:
    """Install and uninstall shell completion scripts.

    This class detects the user's shell, generates appropriate completion
    scripts, and installs them to standard shell completion directories.
    """

    SHELLS = ["bash", "zsh", "fish"]

    # Standard completion paths for each shell (in priority order)
    COMPLETION_PATHS = {
        "bash": [
            "~/.bash_completion.d/aii",
            "~/.local/share/bash-completion/completions/aii",
        ],
        "zsh": [
            "~/.zsh/completion/_aii",
            "~/.local/share/zsh/site-functions/_aii",
        ],
        "fish": [
            "~/.config/fish/completions/aii.fish",
        ],
    }

    # Shell config files where completion might need to be sourced
    SHELL_CONFIGS = {
        "bash": ["~/.bashrc", "~/.bash_profile"],
        "zsh": ["~/.zshrc"],
        "fish": ["~/.config/fish/config.fish"],
    }

    def __init__(self, generator: CompletionGenerator):
        """Initialize completion installer.

        Args:
            generator: CompletionGenerator instance for script generation
        """
        self.generator = generator

    def detect_shell(self) -> Optional[str]:
        """Auto-detect user's current shell from $SHELL environment variable.

        Returns:
            Shell name ("bash", "zsh", or "fish") or None if not detected
        """
        shell = os.environ.get("SHELL", "")

        if "bash" in shell:
            return "bash"
        elif "zsh" in shell:
            return "zsh"
        elif "fish" in shell:
            return "fish"

        return None

    def _get_script_for_shell(self, shell: str) -> str:
        """Get completion script for specified shell.

        Args:
            shell: Shell name ("bash", "zsh", or "fish")

        Returns:
            Completion script content as string
        """
        if shell == "bash":
            return self.generator.generate_bash()
        elif shell == "zsh":
            return self.generator.generate_zsh()
        elif shell == "fish":
            return self.generator.generate_fish()
        else:
            raise ValueError(f"Unsupported shell: {shell}")

    def _find_writable_path(self, paths: List[str]) -> Optional[Path]:
        """Find first writable path from list of candidates.

        Args:
            paths: List of path templates (may contain ~)

        Returns:
            First writable Path or None if none found
        """
        for path_template in paths:
            path = Path(path_template).expanduser()

            # Create parent directory if it doesn't exist
            try:
                path.parent.mkdir(parents=True, exist_ok=True)

                # Test if we can write to this location
                if path.parent.exists() and os.access(path.parent, os.W_OK):
                    return path
            except (PermissionError, OSError):
                continue

        return None

    def install(self, shell: Optional[str] = None) -> Tuple[bool, str]:
        """Install completion for specified shell (or auto-detect).

        Args:
            shell: Shell name ("bash", "zsh", "fish") or None to auto-detect

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Auto-detect shell if not specified
        if shell is None:
            shell = self.detect_shell()
            if shell is None:
                return False, (
                    "❌ Could not detect shell from $SHELL environment variable.\n"
                    "   Please specify shell manually: aii install-completion --shell <bash|zsh|fish>"
                )

        # Validate shell
        if shell not in self.SHELLS:
            return False, f"❌ Unsupported shell: {shell}. Supported: {', '.join(self.SHELLS)}"

        # Generate completion script
        try:
            script = self._get_script_for_shell(shell)
        except Exception as e:
            return False, f"❌ Failed to generate completion script: {e}"

        # Find installation path
        paths = self.COMPLETION_PATHS[shell]
        install_path = self._find_writable_path(paths)

        if install_path is None:
            return False, (
                f"❌ Could not find writable installation path for {shell}.\n"
                f"   Attempted paths:\n" +
                "\n".join(f"   - {p}" for p in paths)
            )

        # Write completion script
        try:
            install_path.write_text(script)
            install_path.chmod(0o644)  # Read-write for owner, read for others
        except (PermissionError, OSError) as e:
            return False, f"❌ Failed to write completion script: {e}"

        # Build success message
        reload_cmd = self._get_reload_command(shell, install_path)

        if shell == "zsh":
            message = (
                f"✅ Installed {shell} completion to {install_path}\n\n"
                f"💡 To activate completion:\n"
                f"   1. Add to ~/.zshrc: fpath=(~/.zsh/completion $fpath) && autoload -Uz compinit && compinit\n"
                f"   2. Restart your shell: exec zsh\n"
                f"   (or just restart your terminal)\n"
            )
        else:
            message = (
                f"✅ Installed {shell} completion to {install_path}\n\n"
                f"💡 Reload your shell or run:\n"
                f"   {reload_cmd}\n"
            )

        return True, message

    def _get_reload_command(self, shell: str, install_path: Path) -> str:
        """Get command to reload completion for shell.

        Args:
            shell: Shell name
            install_path: Path where completion was installed

        Returns:
            Command to reload completion
        """
        if shell == "fish":
            return "# Fish automatically loads completions on next launch"
        elif shell == "zsh":
            return "# Restart your shell or run: exec zsh"
        elif shell == "bash":
            return f"source {install_path}  # bash"
        else:
            return f"source {install_path}  # {shell}"

    def uninstall(self, shell: Optional[str] = None) -> Tuple[bool, str]:
        """Uninstall completion for specified shell (or auto-detect).

        Args:
            shell: Shell name ("bash", "zsh", "fish") or None to auto-detect

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Auto-detect shell if not specified
        if shell is None:
            shell = self.detect_shell()
            if shell is None:
                return False, (
                    "❌ Could not detect shell from $SHELL environment variable.\n"
                    "   Please specify shell manually: aii uninstall-completion --shell <bash|zsh|fish>"
                )

        # Validate shell
        if shell not in self.SHELLS:
            return False, f"❌ Unsupported shell: {shell}. Supported: {', '.join(self.SHELLS)}"

        # Remove completion files
        removed: List[str] = []
        paths = self.COMPLETION_PATHS[shell]

        for path_template in paths:
            path = Path(path_template).expanduser()
            if path.exists():
                try:
                    path.unlink()
                    removed.append(str(path))
                except (PermissionError, OSError) as e:
                    return False, f"❌ Failed to remove {path}: {e}"

        # Build response message
        if removed:
            message = "✅ Removed completion from:\n" + "\n".join(f"   - {p}" for p in removed)
            return True, message
        else:
            message = f"ℹ️  No completion installed for {shell}"
            return False, message

    def is_installed(self, shell: Optional[str] = None) -> bool:
        """Check if completion is installed for specified shell.

        Args:
            shell: Shell name ("bash", "zsh", "fish") or None to auto-detect

        Returns:
            True if completion is installed, False otherwise
        """
        if shell is None:
            shell = self.detect_shell()
            if shell is None:
                return False

        if shell not in self.SHELLS:
            return False

        paths = self.COMPLETION_PATHS[shell]
        for path_template in paths:
            path = Path(path_template).expanduser()
            if path.exists():
                return True

        return False
