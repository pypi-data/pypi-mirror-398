# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Branch Namer - Generate conventional branch names from descriptions"""


import re
import subprocess
from dataclasses import dataclass
from typing import Dict


@dataclass
class BranchNameConfig:
    """Configuration for branch naming"""

    prefixes: Dict[str, str]  # branch_type -> prefix
    max_length: int = 50
    separator: str = "/"


class BranchNamer:
    """Generate conventional branch names from descriptions"""

    # Type detection keywords
    TYPE_KEYWORDS = {
        "feature": ["add", "implement", "create", "new", "feature"],
        "bugfix": ["fix", "bug", "issue", "error", "broken", "repair"],
        "docs": ["doc", "documentation", "readme", "update doc", "guide"],
        "refactor": ["refactor", "reorganize", "restructure", "clean up", "cleanup"],
        "chore": ["chore", "update", "upgrade", "dependency", "maintain"],
        "hotfix": ["hotfix", "urgent", "critical", "emergency"],
        "test": ["test", "testing", "spec", "unittest"],
    }

    def __init__(self, config: BranchNameConfig):
        self.config = config

    def generate_branch_name(self, description: str, forced_type: str = None) -> str:
        """Generate conventional branch name from description"""
        # Detect type or use forced type
        branch_type = forced_type if forced_type else self.detect_branch_type(description)

        # Get prefix for the type
        prefix = self.config.prefixes.get(branch_type, branch_type)

        # Generate slug from description
        slug = self.generate_slug(description, self.config.max_length)

        # Combine prefix and slug
        return f"{prefix}{self.config.separator}{slug}"

    def detect_branch_type(self, description: str) -> str:
        """Detect branch type from description keywords"""
        desc_lower = description.lower()

        # Score each type based on keyword matches
        type_scores = {}
        for branch_type, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in desc_lower)
            if score > 0:
                type_scores[branch_type] = score

        if type_scores:
            # Return type with highest score
            return max(type_scores, key=type_scores.get)

        # Default to "feature" if no keywords match
        return "feature"

    def generate_slug(self, description: str, max_length: int) -> str:
        """Generate URL-friendly slug from description"""
        # 1. Lowercase
        slug = description.lower()

        # 2. Remove common branch type prefixes if present in description
        slug = re.sub(
            r"^(feat|fix|docs|refactor|chore|test|perf|ci|style|hotfix|bugfix|feature):\s*",
            "",
            slug,
        )

        # 3. Replace spaces and underscores with hyphens
        slug = slug.replace(" ", "-").replace("_", "-")

        # 4. Remove special characters (keep alphanumeric and hyphens)
        slug = re.sub(r"[^a-z0-9-]", "", slug)

        # 5. Collapse multiple hyphens
        slug = re.sub(r"-+", "-", slug)

        # 6. Truncate to max_length
        slug = slug[:max_length].rstrip("-")

        # 7. Ensure slug is not empty
        if not slug:
            slug = "branch"

        return slug

    def check_branch_exists(self, branch_name: str) -> bool:
        """Check if branch already exists (locally or remotely)"""
        try:
            # Check local branches
            result = subprocess.run(
                ["git", "branch", "--list", branch_name],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if branch_name in result.stdout:
                return True

            # Check remote branches
            result = subprocess.run(
                ["git", "branch", "--list", "--remotes", f"*/{branch_name}"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return branch_name in result.stdout

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # If git is not available or timeout, assume branch doesn't exist
            return False
