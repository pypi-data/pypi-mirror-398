# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Git domain operations.

This module provides client-side git operations that execute locally
and use the Aii Server for LLM-powered message generation.

Operations:
- commit: Generate AI-powered commit message and execute commit
- pr: Create pull request with AI-generated title and description
- review: Review code changes (future)
"""

from typing import Dict, Optional, Any
from .commit import GitCommitOperation
from .pr import GitPROperation


class GitDomain:
    """
    Git domain handler.

    Manages git-related operations that execute on the client side.
    """

    def __init__(self):
        """Initialize git domain with available operations."""
        self.operations: Dict[str, type] = {
            "commit": GitCommitOperation,
            "pr": GitPROperation,
            # Future operations:
            # "review": GitReviewOperation,
        }

    def get_operation(self, name: str) -> Optional[type]:
        """
        Get operation class by name.

        Args:
            name: Operation name (e.g., "commit")

        Returns:
            Operation class or None if not found
        """
        return self.operations.get(name)

    def list_operations(self) -> list[str]:
        """
        List all available operations in this domain.

        Returns:
            List of operation names
        """
        return list(self.operations.keys())

    def get_help(self) -> str:
        """
        Get help text for git domain.

        Returns:
            Help text string
        """
        return """Usage: aii run git <operation> [args]

Git domain operations.

Available Operations:
  commit     Generate AI-powered commit message and execute commit
  pr         Create pull request with AI-generated title and description

Examples:
  aii run git commit
  aii run git pr
  aii run git pr --base develop --draft
  aii run git pr --dry-run

Use 'aii run git <operation> --help' for operation-specific options."""


__all__ = ["GitDomain", "GitCommitOperation", "GitPROperation"]
