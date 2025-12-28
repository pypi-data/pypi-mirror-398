# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""GitHub CLI Wrapper - Interact with GitHub via gh command"""


import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class GitHubRepo:
    """GitHub repository information"""

    owner: str
    name: str
    default_branch: str


@dataclass
class GitCommitInfo:
    """Git commit information"""

    sha: str
    message: str
    author: str
    date: str


class GitHubClient:
    """Wrapper for GitHub CLI (gh) commands"""

    def check_gh_installed(self) -> bool:
        """Check if GitHub CLI is installed"""
        try:
            result = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def check_gh_authenticated(self) -> bool:
        """Check if user is authenticated with GitHub"""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_repo_info(self) -> GitHubRepo:
        """Get current repository info"""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "owner,name,defaultBranchRef"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to get repository info: {result.stderr}")

            import json

            data = json.loads(result.stdout)

            return GitHubRepo(
                owner=data["owner"]["login"],
                name=data["name"],
                default_branch=data["defaultBranchRef"]["name"],
            )

        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to get repository info: {str(e)}")

    def get_current_branch(self) -> str:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to get current branch: {result.stderr}")

            branch = result.stdout.strip()
            if not branch:
                raise RuntimeError("Not on a branch (detached HEAD state)")

            return branch

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to get current branch: {str(e)}")

    def get_commits_since_divergence(
        self, base_branch: str, current_branch: Optional[str] = None
    ) -> list[GitCommitInfo]:
        """Get commits since current branch diverged from base"""
        try:
            if not current_branch:
                current_branch = self.get_current_branch()

            # Get commits between base and current branch
            # Format: %H = commit hash, %s = subject, %an = author name, %ai = author date
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"{base_branch}..{current_branch}",
                    "--pretty=format:%H|%s|%an|%ai",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to get commits: {result.stderr}")

            commits = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("|", 3)
                if len(parts) != 4:
                    continue

                sha, message, author, date = parts
                commits.append(
                    GitCommitInfo(sha=sha, message=message, author=author, date=date)
                )

            return commits

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to get commits: {str(e)}")

    def create_pr(
        self,
        title: str,
        body: str,
        base_branch: Optional[str] = None,
        draft: bool = False,
    ) -> str:
        """Create PR and return PR URL"""
        try:
            cmd = ["gh", "pr", "create", "--title", title, "--body", body]

            if base_branch:
                cmd.extend(["--base", base_branch])

            if draft:
                cmd.append("--draft")

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"Failed to create PR: {result.stderr}")

            # gh pr create returns the PR URL
            pr_url = result.stdout.strip()
            return pr_url

        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(f"Failed to create PR: {str(e)}")
