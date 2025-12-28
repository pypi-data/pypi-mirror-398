# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for git functions."""


import re
from typing import Any

from .base_enhancer import BaseEnhancer


class GitEnhancer(BaseEnhancer):
    """Enhancer for git_diff function."""

    @property
    def supported_functions(self) -> list[str]:
        return ["git_diff"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Enhance git_diff parameters."""
        user_lower = user_input.lower()

        # 1. COMMIT DETECTION
        if self._is_commit_request(user_lower):
            parameters["commit"] = "HEAD"
            parameters["analyze"] = True

        # 2. STAGED CHANGES
        if any(keyword in user_lower for keyword in ["staged", "cached", "--cached"]):
            parameters["staged"] = True

        # 3. ANALYSIS REQUEST
        if any(
            keyword in user_lower for keyword in ["analyze", "analysis", "explain", "review"]
        ):
            parameters["analyze"] = True

        self.debug(f"Enhanced git_diff parameters: {parameters}")
        return parameters

    def _is_commit_request(self, user_input: str) -> bool:
        """Check if user wants to see commit diff."""
        commit_patterns = [
            r"(?:what|show)\s+changed\s+in\s+(?:the\s+)?last\s+commit",
            r"(?:what|show)\s+(?:was\s+)?in\s+(?:the\s+)?last\s+commit",
            r"diff\s+(?:of\s+)?(?:the\s+)?last\s+commit",
            r"(?:what|show)\s+changed\s+in\s+(?:the\s+)?(?:latest|recent)\s+commit",
            r"show\s+(?:me\s+)?(?:the\s+)?(?:latest|last|recent)\s+commit",
            r"(?:what|show)\s+changed\s+in\s+HEAD",
            r"git\s+show",
        ]

        return any(re.search(pattern, user_input) for pattern in commit_patterns)
