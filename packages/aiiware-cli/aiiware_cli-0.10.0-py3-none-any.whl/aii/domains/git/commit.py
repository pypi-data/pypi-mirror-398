# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Git commit operation - Client-side implementation.

This operation executes git diff locally, builds a prompt with the diff content,
sends it to the stateless Aii Server for commit message generation, and then
executes the commit locally.

Architecture:
- Client: Executes git commands, owns prompt template, handles user confirmation
- Server: Pure LLM execution (no knowledge of git, just generates text)
"""


import subprocess
import tempfile
import os
import sys
from typing import Optional, Dict, Any
from aii.cli.debug import debug_print


class GitCommitOperation:
    """
    Generate AI-powered commit message and execute commit.

    Flow:
    1. Validate git repository
    2. Get staged changes (git diff --cached)
    3. Display diff preview to user
    4. Build prompt with diff embedded
    5. Send to Aii Server for LLM generation
    6. Display generated commit message
    7. Request user confirmation
    8. Execute git commit with generated message
    """

    def __init__(self, config_manager, api_client):
        """
        Initialize git commit operation.

        Args:
            config_manager: ConfigManager instance
            api_client: AiiCLIClient instance for server communication
        """
        self.config = config_manager
        self.client = api_client

    async def execute(self, args: Optional[list] = None) -> int:
        """
        Execute git commit operation.

        Args:
            args: Optional command-line arguments

        Returns:
            Exit code (0 = success, 1 = error)
        """
        debug_print("GIT COMMIT: Starting operation...")

        # Step 1: Validate git repository
        if not self._is_git_repository():
            print("❌ Not in a git repository.")
            print("💡 Initialize with: git init")
            return 1

        # Step 2: Get staged changes
        git_diff = self._get_staged_diff()
        if not git_diff:
            print("❌ No staged changes to commit.")
            print("💡 Stage changes with: git add <files>")
            return 1

        # Step 3: Display diff preview
        self._display_diff_preview(git_diff)

        # Step 4: Build user prompt (just the requirements, not the template)
        user_prompt = f"""Generate a conventional commit message for the following git diff.

Git diff of staged changes:
```diff
{git_diff}
```"""
        debug_print(f"GIT COMMIT: Prompt built ({len(user_prompt)} chars)")

        # Step 5: Send to server for LLM generation (direct LLM call, bypass intent recognition & orchestrator)
        from aii.cli.spinner import Spinner

        # Start animated loading message
        spinner = Spinner("Generating commit message...")
        await spinner.start()

        # System prompt defines the requirements
        system_prompt = """You are an expert at writing conventional commit messages.

Requirements:
1. Use Conventional Commits format: type(scope): description
2. Allowed types: feat, fix, refactor, docs, style, test, chore, perf, ci, revert
3. Keep the subject line under 72 characters
4. **ALWAYS include a body section** (1-3 sentences) explaining:
   - WHAT changed (briefly summarize the modifications)
   - WHY the change was made (purpose, problem being solved)
   - HOW it impacts the codebase (behavior changes, new capabilities)
5. Focus on clarity and context for future developers
6. Footer (must include exactly as shown):
   🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)

Output ONLY the commit message in plain text (no markdown code blocks, no explanatory text).

Example format:
feat(cli): implement stats command to display usage statistics

Implemented stats handler to fetch and display aggregated usage metrics
over user-specified periods including executions, token counts, and costs.
This provides developers with visibility into AI function usage patterns
and helps track token consumption for cost optimization.

🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)"""

        try:
            # Use execute_with_system_prompt for direct LLM call (v0.6.1 pattern)
            # This bypasses the orchestrator and intent recognition entirely
            result = await self.client.execute_with_system_prompt(
                system_prompt=system_prompt,
                user_input=user_prompt,
                output_mode="STANDARD",  # STANDARD mode shows session summary
                spinner=spinner
            )
            debug_print(f"GIT COMMIT: Server response - success={result.get('success')}")
            debug_print(f"GIT COMMIT: Server response keys - {list(result.keys())}")
            debug_print(f"GIT COMMIT: Result field - {result.get('result')}")
        except Exception as e:
            print(f"\n❌ Failed to generate commit message: {e}")
            return 1
        finally:
            # Stop spinner
            await spinner.stop()

        # Extract commit message from result
        commit_message = self._extract_commit_message(result)
        if not commit_message:
            # Debug: Show what we received
            print(f"\n❌ Failed to generate commit message (empty response)")
            print(f"Debug: Response keys: {list(result.keys())}")
            print(f"Debug: Result field: '{result.get('result')}'")
            print(f"Debug: Data field: {result.get('data')}")
            print(f"Debug: Metadata: {result.get('metadata')}")
            print("\nThis appears to be a server-side issue. The server is not returning")
            print("the commit message in the expected 'data' or 'result' field.")
            print("\nNote: For stateless architecture (v0.6.0), the server-side git_commit")
            print("function should be removed and replaced with client-side logic.")
            return 1

        # Step 6: Clear "Generating..." message and display generated message
        # Use carriage return to overwrite the "Generating..." line
        print("\r\033[K", end="")  # Clear current line

        # Display the commit message box (overwriting "Generating..." message)
        print("="*70)
        print("📝 Generated Commit Message:")
        print("="*70)
        print(commit_message)
        print("="*70)

        # Display metadata if available (with fixed confidence percentage)
        if result.get("metadata"):
            metadata = result["metadata"]
            if metadata.get("confidence"):
                confidence = metadata['confidence']
                # Fix: confidence is already a percentage (0-100), not a fraction
                print(f"🎯 Confidence: {int(confidence)}%")

            # Display session summary (STANDARD mode) - tokens are shown here
            if metadata.get("execution_time") and metadata.get("model"):
                tokens = metadata.get("tokens", {})
                exec_time = metadata["execution_time"]
                model = metadata["model"]
                cost = metadata.get("cost", 0)

                print("\n📊 Session Summary:")
                token_info = f"{tokens.get('input', 0)}↗ {tokens.get('output', 0)}↘ ({tokens.get('input', 0) + tokens.get('output', 0)} total)" if tokens else ""
                print(f"✓ git_commit: • ⚡ Total time: {exec_time:.1f}s • 🔢 Tokens: {token_info} • 💰 ${cost:.6f} • 🤖 {model}")

        # Step 7: Request user confirmation
        print()
        try:
            response = input("Proceed with this commit? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cancelled by user")
            return 1

        if response != "y":
            print("❌ Commit cancelled")
            return 1

        # Step 8: Execute git commit
        success = self._execute_git_commit(commit_message)
        if success:
            print("✅ Commit successful!")
            return 0
        else:
            print("❌ Commit failed")
            return 1

    def _is_git_repository(self) -> bool:
        """
        Check if current directory is inside a git repository.

        Returns:
            True if in git repo, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _get_staged_diff(self) -> Optional[str]:
        """
        Get staged changes using git diff --cached.

        Returns:
            Git diff string or None if no staged changes
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached"],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            return None

        except FileNotFoundError:
            return None

    def _display_diff_preview(self, git_diff: str) -> None:
        """
        Display preview of git diff to user with syntax highlighting.

        Shows first 2000 characters and indicates if truncated.

        Args:
            git_diff: Full git diff string
        """
        print("\n📋 Git Diff:")

        # Try to colorize the diff using pygments
        try:
            from pygments import highlight
            from pygments.lexers import DiffLexer
            from pygments.formatters import TerminalFormatter

            # Truncate for display (full diff is sent to LLM)
            max_preview_length = 2000
            diff_to_display = git_diff
            truncated = False

            if len(git_diff) > max_preview_length:
                diff_to_display = git_diff[:max_preview_length]
                truncated = True

            # Apply syntax highlighting
            colorized_diff = highlight(diff_to_display, DiffLexer(), TerminalFormatter())
            print(colorized_diff)

            if truncated:
                print(f"\n... (diff truncated for display, showing first {max_preview_length} chars)")
                print(f"Full diff ({len(git_diff)} chars) will be sent to AI for analysis")

        except ImportError:
            # Fallback to plain text if pygments is not available
            max_preview_length = 2000
            if len(git_diff) > max_preview_length:
                print(git_diff[:max_preview_length])
                print(f"\n... (diff truncated for display, showing first {max_preview_length} chars)")
                print(f"Full diff ({len(git_diff)} chars) will be sent to AI for analysis")
            else:
                print(git_diff)

    def _extract_commit_message(self, result: Dict[str, Any]) -> Optional[str]:
        """
        Extract commit message from server result.

        The server-side git_commit function returns commit message in data["commit_message"].

        Args:
            result: Server response dict

        Returns:
            Commit message string or None
        """
        # Try different possible fields (in order of likelihood)
        message = None

        # Server-side git_commit stores in data["commit_message"] (current behavior)
        if result.get("data") and isinstance(result["data"], dict):
            message = (
                result["data"].get("commit_message")  # git_commit specific field
                or result["data"].get("clean_output")  # generic clean mode
                or result["data"].get("message")  # fallback
            )

        # CLEAN mode: result is in 'result' field (for future universal_generate)
        elif result.get("result"):
            message = result["result"]

        # Check metadata for the full message (fallback)
        elif result.get("metadata") and result["metadata"].get("message"):
            message = result["metadata"]["message"]

        # Check direct message field
        elif result.get("message"):
            message = result["message"]

        # Check response field (legacy)
        elif result.get("response"):
            message = result["response"]

        if message:
            # Clean up the message
            message = message.strip()

            # Remove markdown code blocks if present
            if message.startswith("```"):
                lines = message.split("\n")
                # Remove first line (```diff or similar)
                lines = lines[1:]
                # Remove last line (```)
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                message = "\n".join(lines).strip()

            return message

        return None

    def _execute_git_commit(self, commit_message: str) -> bool:
        """
        Execute git commit with the generated message.

        Creates a temporary file with the commit message and passes it to git.

        Args:
            commit_message: Commit message to use

        Returns:
            True if commit succeeded, False otherwise
        """
        try:
            # Create temporary file for commit message
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(commit_message)
                temp_file = f.name

            try:
                # Execute git commit with message from file
                result = subprocess.run(
                    ["git", "commit", "-F", temp_file],
                    capture_output=True,
                    text=True,
                    check=False
                )

                # Display git output
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr, file=sys.stderr)

                return result.returncode == 0

            finally:
                # Clean up temporary file
                if os.path.exists(temp_file):
                    os.remove(temp_file)

        except Exception as e:
            print(f"❌ Error executing git commit: {e}", file=sys.stderr)
            return False


__all__ = ["GitCommitOperation", "COMMIT_MESSAGE_TEMPLATE"]
