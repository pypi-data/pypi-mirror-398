# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Git pull request operation - Client-side implementation.

This operation analyzes the current branch, generates a PR title and description
using LLM, and creates the pull request using the GitHub CLI (gh).

Architecture:
- Client: Executes git/gh commands, owns prompt template, handles user confirmation
- Server: Pure LLM execution (generates PR content from git context)
"""


import subprocess
import sys
from typing import Optional, Dict, Any, Tuple
from aii.cli.debug import debug_print


# Prompt template for PR generation (CLIENT-SIDE)
PR_GENERATION_TEMPLATE = """Generate a pull request title and description for the following changes.

**Current Branch**: {branch_name}
**Base Branch**: {base_branch}
**Commits** ({commit_count} total):
```
{commits}
```

**Changes Summary**:
```diff
{diff_summary}
```

**Full Diff**:
```diff
{full_diff}
```

Requirements:
1. **Title**: Concise, descriptive, follows conventional commit format (type: description)
2. **Description**: Include:
   - ## Summary (2-3 bullet points of key changes)
   - ## Changes (detailed list of modifications)
   - ## Testing (use checkboxes [ ] for test steps, NOT numbered lists)
   - ## Notes (any additional context, breaking changes, etc.)

Output format (plain text, no markdown code blocks):
---
TITLE: <pr-title>
---
DESCRIPTION:
<pr-description>
---

Example:
---
TITLE: feat(domains): add git PR operation for automated pull request creation
---
DESCRIPTION:
## Summary
- Implemented GitPROperation class for client-side PR generation
- Added support for multi-commit branch analysis
- Integrated GitHub CLI for PR creation

## Changes
- Created `aii/domains/git/pr.py` with GitPROperation
- Added PR_GENERATION_TEMPLATE for LLM prompt
- Registered pr operation in GitDomain
- Supports both single and multi-commit branches

## Testing
- [ ] Create a feature branch with commits
- [ ] Run `aii run git pr`
- [ ] Verify generated PR title and description
- [ ] Confirm PR created on GitHub

## Notes
- Requires GitHub CLI (`gh`) installed and authenticated
- Works with any base branch (main, master, develop, etc.)
- Supports dry-run mode for preview without creation

🤖 Generated with [aii](https://pypi.org/project/aiiware-cli)
---
"""


class GitPROperation:
    """
    Generate AI-powered pull request and create using GitHub CLI.

    Flow:
    1. Validate git repository and GitHub CLI
    2. Get current branch and base branch
    3. Get commit history and diff
    4. Build prompt with git context
    5. Send to Aii Server for LLM generation
    6. Parse PR title and description
    7. Display preview to user
    8. Request confirmation
    9. Create PR using `gh pr create`
    """

    def __init__(self, config_manager, api_client):
        """
        Initialize git PR operation.

        Args:
            config_manager: ConfigManager instance
            api_client: AiiCLIClient instance for server communication
        """
        self.config = config_manager
        self.client = api_client

    async def execute(self, args: Optional[list] = None) -> int:
        """
        Execute git PR operation.

        Args:
            args: Optional command-line arguments
                  Supported: [--base <branch>] [--draft] [--dry-run]

        Returns:
            Exit code (0 = success, 1 = error)
        """
        debug_print("GIT PR: Starting operation...")

        # Parse arguments
        base_branch_override = None
        is_draft = False
        is_dry_run = False

        if args:
            i = 0
            while i < len(args):
                if args[i] == "--base" and i + 1 < len(args):
                    base_branch_override = args[i + 1]
                    i += 2
                elif args[i] == "--draft":
                    is_draft = True
                    i += 1
                elif args[i] == "--dry-run":
                    is_dry_run = True
                    i += 1
                else:
                    print(f"⚠️  Unknown argument: {args[i]}")
                    i += 1

        # Step 1: Validate prerequisites
        if not self._is_git_repository():
            print("❌ Not in a git repository.")
            print("💡 Initialize with: git init")
            return 1

        if not self._is_gh_installed():
            print("❌ GitHub CLI (gh) is not installed.")
            print("💡 Install from: https://cli.github.com/")
            return 1

        if not self._is_gh_authenticated():
            print("❌ GitHub CLI (gh) is not authenticated.")
            print("💡 Authenticate with: gh auth login")
            return 1

        # Step 2: Get current branch
        current_branch = self._get_current_branch()
        if not current_branch:
            print("❌ Could not determine current branch.")
            return 1

        # Step 3: Determine base branch
        base_branch = base_branch_override or self._get_default_branch()
        if current_branch == base_branch:
            print(f"❌ Current branch '{current_branch}' is the same as base branch '{base_branch}'.")
            print("💡 Create a feature branch first: git checkout -b feature/my-feature")
            return 1

        print(f"📋 Creating PR: {current_branch} → {base_branch}")

        # Step 4: Check for staged changes that need to be committed
        if self._has_staged_changes():
            print("\n⚠️  You have staged changes that aren't committed yet")
            print("💡 Commit your staged changes first:")
            print("   git commit -m 'your message'")
            print("\n💡 Or unstage them if you don't want them in the PR:")
            print("   git restore --staged <file>")
            return 1

        # Step 5: Check if branch is pushed to remote (BEFORE generating PR content)
        if not self._is_branch_pushed(current_branch):
            print(f"\n⚠️  Branch '{current_branch}' is not pushed to remote")
            try:
                push_response = input("Push branch to remote? (y/n): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelled by user")
                return 1

            if push_response == "y":
                if not self._push_branch(current_branch):
                    print("❌ Failed to push branch")
                    return 1
                print(f"✅ Branch '{current_branch}' pushed to origin")
            else:
                print("❌ PR creation cancelled (branch not pushed)")
                return 1

        # Step 6: Check if local branch has unpushed commits
        unpushed_count = self._get_unpushed_commits_count(current_branch)
        if unpushed_count > 0:
            print(f"\n⚠️  You have {unpushed_count} unpushed commit(s)")
            try:
                push_response = input("Push commits to remote? (y/n): ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Cancelled by user")
                return 1

            if push_response == "y":
                if not self._push_branch(current_branch):
                    print("❌ Failed to push commits")
                    return 1
                print(f"✅ Pushed {unpushed_count} commit(s) to origin")
            else:
                print("❌ PR creation cancelled (unpushed commits)")
                return 1

        # Step 7: Get git context
        commits = self._get_commits(base_branch, current_branch)
        if not commits:
            print(f"❌ No commits found between '{base_branch}' and '{current_branch}'.")
            print("💡 Make some commits first")
            return 1

        diff_summary = self._get_diff_summary(base_branch, current_branch)
        full_diff = self._get_full_diff(base_branch, current_branch)

        print(f"📊 Found {len(commits.splitlines())} commits with {len(diff_summary.splitlines())} files changed")

        # Step 8: Build prompt
        prompt = PR_GENERATION_TEMPLATE.format(
            branch_name=current_branch,
            base_branch=base_branch,
            commit_count=len(commits.splitlines()),
            commits=commits,
            diff_summary=diff_summary,
            full_diff=full_diff[:5000]  # Limit diff to 5000 chars to avoid token overflow
        )
        debug_print(f"GIT PR: Prompt built ({len(prompt)} chars)")

        # Step 9: Send to server for LLM generation (bypass intent recognition)
        from aii.cli.spinner import Spinner

        # Start animated loading message
        spinner = Spinner("Generating PR content...")
        await spinner.start()

        try:
            # Use execute_function to call universal_generate directly
            # This bypasses intent recognition to avoid misinterpretation
            result = await self.client.execute_function(
                function_name="universal_generate",
                parameters={"request": prompt},
                output_mode="STANDARD"
            )
            debug_print(f"GIT PR: Server response - success={result.get('success')}")
        except Exception as e:
            print(f"\n❌ Failed to generate PR content: {e}")
            return 1
        finally:
            # Stop spinner
            await spinner.stop()

        # Step 8: Parse PR title and description
        pr_title, pr_description = self._parse_pr_content(result)
        if not pr_title or not pr_description:
            print("\n❌ Failed to parse PR content from LLM response")
            print(f"Debug: Result: {result.get('result')[:200]}...")
            return 1

        # Step 9: Clear "Generating..." and display preview
        print("\r\033[K", end="")  # Clear current line

        print("="*70)
        print("📝 Generated Pull Request:")
        print("="*70)
        print(f"\n**Title**: {pr_title}\n")
        print("**Description**:")
        print(pr_description)
        print("\n" + "="*70)

        # Display metadata
        if result.get("metadata"):
            metadata = result["metadata"]
            if metadata.get("confidence"):
                confidence = metadata['confidence']
                print(f"🎯 Confidence: {int(confidence)}%")

            # Session summary
            if metadata.get("execution_time") and metadata.get("model"):
                tokens = metadata.get("tokens", {})
                exec_time = metadata["execution_time"]
                model = metadata["model"]
                cost = metadata.get("cost", 0)

                print("\n📊 Session Summary:")
                token_info = f"{tokens.get('input', 0)}↗ {tokens.get('output', 0)}↘ ({tokens.get('input', 0) + tokens.get('output', 0)} total)" if tokens else ""
                print(f"✓ git_pr: • ⚡ Total time: {exec_time:.1f}s • 🔢 Tokens: {token_info} • 💰 ${cost:.6f} • 🤖 {model}")

        # Step 10: Dry run check
        if is_dry_run:
            print("\n🔍 Dry run mode - PR not created")
            print("💡 Remove --dry-run to create the PR")
            return 0

        # Step 11: Request confirmation
        print()
        try:
            response = input("Create this pull request? (y/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cancelled by user")
            return 1

        if response != "y":
            print("❌ PR creation cancelled")
            return 1

        # Step 12: Create PR using gh CLI
        success = self._create_pr(pr_title, pr_description, base_branch, is_draft)
        if success:
            print("✅ Pull request created successfully!")
            return 0
        else:
            print("❌ Failed to create pull request")
            return 1

    def _is_git_repository(self) -> bool:
        """Check if current directory is inside a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _is_gh_installed(self) -> bool:
        """Check if GitHub CLI is installed."""
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _is_gh_authenticated(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_current_branch(self) -> Optional[str]:
        """Get current git branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def _get_default_branch(self) -> str:
        """
        Get default branch (main or master).

        Returns:
            Default branch name (main, master, or develop)
        """
        try:
            # Try to get default branch from remote
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                # Output: refs/remotes/origin/main
                branch = result.stdout.strip().split("/")[-1]
                return branch

            # Fallback: check if main exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "main"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return "main"

            # Fallback: check if master exists
            result = subprocess.run(
                ["git", "rev-parse", "--verify", "master"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return "master"

            # Final fallback
            return "main"
        except Exception:
            return "main"

    def _get_commits(self, base_branch: str, current_branch: str) -> str:
        """
        Get commit history between base and current branch.

        Args:
            base_branch: Base branch (e.g., main)
            current_branch: Current feature branch

        Returns:
            Formatted commit history
        """
        try:
            result = subprocess.run(
                ["git", "log", f"{base_branch}..{current_branch}", "--oneline"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def _get_diff_summary(self, base_branch: str, current_branch: str) -> str:
        """
        Get summary of changed files.

        Args:
            base_branch: Base branch
            current_branch: Current feature branch

        Returns:
            Diff stat summary
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{base_branch}...{current_branch}", "--stat"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def _get_full_diff(self, base_branch: str, current_branch: str) -> str:
        """
        Get full diff between branches.

        Args:
            base_branch: Base branch
            current_branch: Current feature branch

        Returns:
            Full diff content
        """
        try:
            result = subprocess.run(
                ["git", "diff", f"{base_branch}...{current_branch}"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return ""
        except Exception:
            return ""

    def _parse_pr_content(self, result: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse PR title and description from LLM result.

        Args:
            result: Result from API client

        Returns:
            Tuple of (title, description)
        """
        # Get the generated text from result
        text = result.get("result", "").strip()

        if not text:
            return None, None

        try:
            # Strategy 1: Try to parse --- delimited format
            if "---" in text:
                parts = text.split("---")
                if len(parts) >= 3:
                    title_part = parts[1].strip()
                    desc_part = parts[2].strip()

                    # Extract title
                    title = title_part.replace("TITLE:", "").strip()

                    # Extract description
                    description = desc_part.replace("DESCRIPTION:", "").strip()

                    if title and description:
                        return title, description

            # Strategy 2: Look for "Title:" and extract everything after
            if "Title:" in text:
                lines = text.split("\n")
                title = None
                desc_lines = []
                found_title = False

                for line in lines:
                    if line.strip().startswith("Title:"):
                        title = line.replace("Title:", "").strip()
                        found_title = True
                    elif found_title and line.strip() and not line.strip().startswith("##"):
                        # Skip empty lines and section headers right after title
                        if desc_lines or line.strip().startswith("##"):
                            desc_lines.append(line)
                    elif found_title and line.strip().startswith("##"):
                        desc_lines.append(line)

                if title and desc_lines:
                    description = "\n".join(desc_lines).strip()
                    # Remove the footer if present
                    if "🤖 Generated with" in description:
                        description = description.split("🤖 Generated with")[0].strip()
                    return title, description

            # Strategy 3: Fallback - first line is title, rest is description
            lines = text.split("\n", 1)
            title = lines[0].strip()

            # Remove any box characters or markdown formatting from title
            title = title.replace("╭", "").replace("╮", "").replace("│", "").replace("╰", "").strip()
            title = title.replace("**Title**:", "").replace("Title:", "").strip()

            description = lines[1].strip() if len(lines) > 1 else ""

            # Clean up description - remove fancy boxes
            description = description.replace("│", "").replace("╰", "").replace("╭", "").replace("╮", "")
            description = description.replace("**Description**:", "").strip()

            # Remove footer
            if "🤖 Generated with" in description:
                description = description.split("🤖 Generated with")[0].strip()

            # Remove any "📊 Analyzed" lines
            if "📊 Analyzed" in description:
                description = description.split("📊 Analyzed")[0].strip()

            # Remove any "Create this PR?" or confirmation prompts from LLM output
            if "Create this PR?" in description:
                description = description.split("Create this PR?")[0].strip()
            if "Create this pull request?" in description:
                description = description.split("Create this pull request?")[0].strip()

            return title, description

        except Exception as e:
            debug_print(f"GIT PR: Failed to parse PR content: {e}")
            return None, None

    def _is_branch_pushed(self, branch: str) -> bool:
        """
        Check if current branch is pushed to remote.

        Args:
            branch: Branch name to check

        Returns:
            True if branch exists on remote, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", branch],
                capture_output=True,
                text=True,
                check=False
            )
            # Check if output contains refs/heads/<branch> (more precise than just branch name)
            # Output format: <hash>\trefs/heads/<branch>
            return result.returncode == 0 and f"refs/heads/{branch}" in result.stdout
        except Exception:
            return False

    def _push_branch(self, branch: str) -> bool:
        """
        Push current branch to remote origin.

        Args:
            branch: Branch name to push

        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "push", "-u", "origin", branch],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except Exception:
            return False

    def _has_staged_changes(self) -> bool:
        """
        Check if there are staged changes (files in staging area waiting to be committed).

        Returns:
            True if there are staged changes, False otherwise
        """
        try:
            # Check for staged changes only (--cached shows only staged files)
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            # If output is not empty, there are staged changes
            return result.returncode == 0 and len(result.stdout.strip()) > 0
        except Exception:
            return False

    def _get_unpushed_commits_count(self, branch: str) -> int:
        """
        Get number of commits that are ahead of remote.

        Args:
            branch: Branch name to check

        Returns:
            Number of unpushed commits (0 if none or error)
        """
        try:
            # Compare local branch with remote
            result = subprocess.run(
                ["git", "rev-list", f"origin/{branch}..{branch}", "--count"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 0
        except Exception:
            return 0

    def _create_pr(self, title: str, description: str, base_branch: str, is_draft: bool) -> bool:
        """
        Create pull request using GitHub CLI.

        Args:
            title: PR title
            description: PR description
            base_branch: Base branch to merge into
            is_draft: Whether to create as draft PR

        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", description,
                "--base", base_branch
            ]

            if is_draft:
                cmd.append("--draft")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode == 0:
                # Print PR URL
                print(f"\n🔗 {result.stdout.strip()}")
                return True
            else:
                print(f"\nError: {result.stderr.strip()}")
                return False

        except Exception as e:
            print(f"\nException: {e}")
            return False
