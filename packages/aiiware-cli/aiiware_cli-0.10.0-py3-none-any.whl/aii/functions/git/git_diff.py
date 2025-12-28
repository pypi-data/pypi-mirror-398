# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Git Diff Function - Show git diff with optional AI analysis"""


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


class GitDiffFunction(FunctionPlugin):
    """Show git diff with optional AI analysis"""

    @property
    def name(self) -> str:
        return "git_diff"

    @property
    def description(self) -> str:
        return "Show git diff with optional AI analysis"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.GIT

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "staged": ParameterSchema(
                name="staged",
                type="boolean",
                required=False,
                default=False,
                description="Show staged changes (--cached)",
            ),
            "file_path": ParameterSchema(
                name="file_path",
                type="string",
                required=False,
                description="Specific file to diff",
            ),
            "analyze": ParameterSchema(
                name="analyze",
                type="boolean",
                required=False,
                default=False,
                description="Provide AI analysis of changes",
            ),
            "commit": ParameterSchema(
                name="commit",
                type="string",
                required=False,
                description="Show changes in specific commit (e.g., 'HEAD', 'HEAD~1', commit hash)",
            ),
        }

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
            result = subprocess.run(["git", "--version"], capture_output=True)
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Git not available"])

            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"], capture_output=True
            )
            if result.returncode != 0:
                return ValidationResult(valid=False, errors=["Not in a git repository"])

            return ValidationResult(valid=True)

        except Exception as e:
            return ValidationResult(valid=False, errors=[str(e)])

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute git diff"""
        try:
            commit = parameters.get("commit")

            if commit:
                # Show changes in a specific commit
                if commit.lower() in ["head", "last", "latest"]:
                    cmd = ["git", "show", "--format=fuller", "HEAD"]
                else:
                    cmd = ["git", "show", "--format=fuller", commit]
            else:
                # Standard git diff
                cmd = ["git", "diff"]

                if parameters.get("staged", False):
                    cmd.append("--cached")

            file_path = parameters.get("file_path")
            if file_path and not commit:
                cmd.append(file_path)

            # First, get numstat to detect binary files
            numstat_cmd = cmd.copy()
            if "--cached" in numstat_cmd:
                # For staged changes, use --numstat with --cached
                numstat_cmd.append("--numstat")
            else:
                # For regular diff, use --numstat
                if "show" not in numstat_cmd[1]:
                    numstat_cmd.append("--numstat")

            # Detect binary files (only for regular diff, not commit show)
            binary_files = []
            if commit:
                # For commit show, just get the output
                result = subprocess.run(cmd, capture_output=True, text=True)
            else:
                # For regular diff, detect binary files first
                numstat_result = subprocess.run(numstat_cmd, capture_output=True, text=True)

                if numstat_result.returncode == 0 and numstat_result.stdout.strip():
                    for line in numstat_result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 3:
                                added, removed, filename = parts[0], parts[1], parts[2]
                                # Binary files show as "-" for both added and removed
                                if added == '-' and removed == '-':
                                    binary_files.append(filename)

                # Get detailed diff
                result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                return ExecutionResult(
                    success=False, message=f"Git diff failed: {result.stderr}"
                )

            diff_output = result.stdout

            # Add binary file summary if any
            if binary_files:
                binary_summary = f"\n\n📦 Binary files changed ({len(binary_files)}):\n"
                binary_summary += "\n".join(f"  • {f}" for f in binary_files)
                binary_summary += "\n\n(Binary file content not shown)"
                diff_output += binary_summary

            if not diff_output.strip() and not binary_files:
                return ExecutionResult(success=True, message="No changes to show")

            # AI analysis if requested
            analysis = ""
            usage = {}
            if parameters.get("analyze", False) and context.llm_provider:
                analysis, usage = await self._analyze_diff(diff_output, context.llm_provider)

            message = diff_output
            if analysis:
                message = f"AI Analysis:\n{analysis}\n\nDiff:\n{diff_output}"

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "diff": diff_output,
                    "analysis": analysis,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Git diff execution failed: {str(e)}"
            )

    async def _analyze_diff(self, diff: str, llm_provider: Any) -> tuple[str, dict]:
        """Analyze diff using LLM and return analysis with token usage"""
        prompt = f"""Analyze this git diff and provide insights:

{diff[:1500]}{"..." if len(diff) > 1500 else ""}

Please provide:
1. Summary of changes
2. Potential impacts
3. Code quality observations
4. Security considerations (if any)

Keep analysis concise and focused."""

        try:
            # Use complete_with_usage for accurate token tracking
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(prompt)
                analysis = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                analysis = await llm_provider.complete(prompt)
                # Fallback to estimates if usage tracking unavailable
                usage = {
                    "input_tokens": len(prompt.split()) + len(diff[:1500].split()),
                    "output_tokens": len(analysis.split()) if analysis else 0
                }
            return analysis, usage
        except Exception:
            return "Analysis unavailable", {}
