# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Git Status Function - Show git status with AI summary"""


import subprocess
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    ParameterSchema,
    ValidationResult,
)


class GitStatusFunction(FunctionPlugin):
    """Show git status with helpful suggestions"""

    @property
    def name(self) -> str:
        return "git_status"

    @property
    def description(self) -> str:
        return "Show git status with helpful suggestions"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check git availability"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True
            )
            return ValidationResult(valid=result.returncode == 0)
        except Exception:
            return ValidationResult(valid=False, errors=["Git not available"])

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git status"""
        try:
            # Get git status
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return ExecutionResult(
                    success=False, message=f"Git status failed: {result.stderr}"
                )

            status_lines = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )

            # Get branch info
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"], capture_output=True, text=True
            )
            current_branch = (
                branch_result.stdout.strip()
                if branch_result.returncode == 0
                else "unknown"
            )

            # Parse status
            staged_files = []
            unstaged_files = []
            untracked_files = []

            for line in status_lines:
                if not line:
                    continue

                status = line[:2]
                filename = line[3:]

                if status[0] in ["A", "M", "D", "R", "C"]:  # Staged
                    staged_files.append(f"{status[0]} {filename}")
                if status[1] in ["M", "D"] or status == " M":  # Modified unstaged
                    unstaged_files.append(f"M {filename}")
                if status == "??":  # Untracked
                    untracked_files.append(filename)

            # Build status message
            message_parts = [f"On branch: {current_branch}"]

            if staged_files:
                message_parts.append(f"\nStaged changes ({len(staged_files)} files):")
                message_parts.extend(f"  {f}" for f in staged_files)

            if unstaged_files:
                message_parts.append(
                    f"\nUnstaged changes ({len(unstaged_files)} files):"
                )
                message_parts.extend(f"  {f}" for f in unstaged_files)

            if untracked_files:
                message_parts.append(
                    f"\nUntracked files ({len(untracked_files)} files):"
                )
                message_parts.extend(f"  {f}" for f in untracked_files[:10])
                if len(untracked_files) > 10:
                    message_parts.append(f"  ... and {len(untracked_files) - 10} more")

            if not any([staged_files, unstaged_files, untracked_files]):
                message_parts.append("\nWorking directory clean")

            # Add suggestions
            suggestions = []
            if unstaged_files or untracked_files:
                suggestions.append("Use 'git add <file>' to stage changes")
            if staged_files:
                suggestions.append(
                    "Use 'aii run git commit' to commit with AI-generated message"
                )

            if suggestions:
                message_parts.append("\nSuggestions:")
                message_parts.extend(f"  • {s}" for s in suggestions)

            return ExecutionResult(
                success=True,
                message="\n".join(message_parts),
                data={
                    "branch": current_branch,
                    "staged_files": staged_files,
                    "unstaged_files": unstaged_files,
                    "untracked_files": untracked_files,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git status execution failed: {str(e)}"
            )
