# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""PR Generator - Generate pull request descriptions from commits using LLM"""


import re
from dataclasses import dataclass
from typing import Any

from .github_client import GitCommitInfo


@dataclass
class PRDescription:
    """Pull request description components"""

    title: str
    summary: str
    changes: list[str]
    test_plan: list[str]
    related_issues: list[str]

    def to_markdown(self) -> str:
        """Convert to markdown format for GitHub"""
        md = f"## Summary\n{self.summary}\n\n"

        md += "## Changes\n"
        for change in self.changes:
            md += f"- {change}\n"

        md += "\n## Test Plan\n"
        for test in self.test_plan:
            md += f"- [ ] {test}\n"

        if self.related_issues:
            md += "\n## Related Issues\n"
            for issue in self.related_issues:
                if issue.startswith("#"):
                    md += f"Closes {issue}\n"
                else:
                    md += f"Closes #{issue}\n"

        return md


class PRGenerator:
    """Generate PR descriptions from commit analysis"""

    def __init__(self, llm_provider: Any):
        self.llm_provider = llm_provider

    async def generate_pr_description(
        self, commits: list[GitCommitInfo], current_branch: str, base_branch: str
    ) -> tuple[PRDescription, dict]:
        """Generate PR description from commits using LLM

        Returns:
            Tuple of (PRDescription, token_usage_dict)
        """

        # Format commits for prompt
        commit_list = self._format_commits_for_prompt(commits)

        # Extract issue numbers from commits
        related_issues = self._extract_issue_numbers(commits)

        # Build LLM prompt
        prompt = f"""Analyze these git commits and generate a comprehensive GitHub Pull Request description.

Branch: {current_branch}
Base: {base_branch}
Number of commits: {len(commits)}

Commits:
{commit_list}

Generate a PR description with the following components in JSON format:

{{
  "title": "Conventional commit style title (e.g., feat: add user authentication)",
  "summary": "2-3 sentence overview of the changes",
  "changes": ["Detailed change 1", "Detailed change 2", ...],
  "test_plan": ["Test case 1", "Test case 2", ...]
}}

Rules:
1. Title: Use conventional commit format (feat:, fix:, docs:, refactor:, chore:, test:, perf:, ci:)
2. Title: Keep under 72 characters
3. Summary: High-level overview, 2-3 sentences
4. Changes: Bulleted list of specific modifications (what was added/changed/removed)
5. Test Plan: Actionable test scenarios (what to test, expected behavior)

If all commits use the same type, use that type for the PR title. Otherwise, choose the most significant type.

Output only valid JSON, no markdown formatting."""

        try:
            import asyncio

            # Call LLM with timeout
            token_usage = {}
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await asyncio.wait_for(
                    self.llm_provider.complete_with_usage(prompt), timeout=30.0
                )
                response = llm_response.content.strip()
                token_usage = llm_response.usage or {}
            else:
                response = await asyncio.wait_for(
                    self.llm_provider.complete(prompt), timeout=30.0
                )
                # Estimate tokens if usage not available
                token_usage = {
                    "input_tokens": len(prompt.split()) * 2,
                    "output_tokens": len(response.split()) * 2,
                }

            # Parse JSON response
            pr_data = self._parse_llm_response(response)

            # Create PRDescription
            pr_description = PRDescription(
                title=pr_data.get("title", self._generate_fallback_title(commits)),
                summary=pr_data.get(
                    "summary", "This PR includes changes from multiple commits."
                ),
                changes=pr_data.get("changes", self._generate_fallback_changes(commits)),
                test_plan=pr_data.get(
                    "test_plan", ["Test all modified functionality"]
                ),
                related_issues=related_issues,
            )

            return pr_description, token_usage

        except Exception as e:
            # Fallback to simple PR generation
            return self._generate_fallback_pr(commits, related_issues), {}

    def _format_commits_for_prompt(self, commits: list[GitCommitInfo]) -> str:
        """Format commits for LLM prompt"""
        lines = []
        for i, commit in enumerate(commits, 1):
            lines.append(f"{i}. {commit.message} (by {commit.author})")
        return "\n".join(lines)

    def _extract_issue_numbers(self, commits: list[GitCommitInfo]) -> list[str]:
        """Extract issue numbers from commit messages"""
        issues = set()
        for commit in commits:
            # Match patterns: #123, fixes #123, closes #456, resolves #789
            matches = re.findall(
                r"(?:fixes?|closes?|resolves?)\s*#?(\d+)|#(\d+)", commit.message, re.IGNORECASE
            )
            for match in matches:
                # match is a tuple, take the non-empty group
                issue_num = match[0] or match[1]
                if issue_num:
                    issues.add(issue_num)

        return sorted([f"#{num}" for num in issues])

    def _parse_llm_response(self, response: str) -> dict:
        """Parse LLM JSON response"""
        import json

        # Clean up response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```"):
            # Remove opening ```json or ```
            response = re.sub(r"^```(?:json)?\s*\n?", "", response)
            # Remove closing ```
            response = re.sub(r"\n?```\s*$", "", response)

        # Parse JSON
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from text
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            raise

    def _generate_fallback_title(self, commits: list[GitCommitInfo]) -> str:
        """Generate fallback title if LLM fails"""
        if len(commits) == 1:
            # Single commit - use its message
            return commits[0].message

        # Multiple commits - detect most common type
        type_counts = {}
        for commit in commits:
            match = re.match(r"^(feat|fix|docs|refactor|chore|test|perf|ci|style):", commit.message)
            if match:
                commit_type = match.group(1)
                type_counts[commit_type] = type_counts.get(commit_type, 0) + 1

        if type_counts:
            most_common_type = max(type_counts, key=type_counts.get)
            return f"{most_common_type}: update from {len(commits)} commits"

        return f"chore: update from {len(commits)} commits"

    def _generate_fallback_changes(self, commits: list[GitCommitInfo]) -> list[str]:
        """Generate fallback changes list if LLM fails"""
        # Use commit messages as changes
        changes = []
        for commit in commits:
            # Remove conventional commit prefix if present
            message = re.sub(r"^(feat|fix|docs|refactor|chore|test|perf|ci|style):\s*", "", commit.message)
            changes.append(message)
        return changes[:10]  # Limit to 10 changes

    def _generate_fallback_pr(
        self, commits: list[GitCommitInfo], related_issues: list[str]
    ) -> PRDescription:
        """Generate fallback PR description if LLM completely fails"""
        return PRDescription(
            title=self._generate_fallback_title(commits),
            summary=f"This PR includes {len(commits)} commit(s) with various changes. Please review the commit history for details.",
            changes=self._generate_fallback_changes(commits),
            test_plan=["Review commit changes", "Test affected functionality"],
            related_issues=related_issues,
        )
