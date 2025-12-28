# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for research function."""


import re
from typing import Any

from .base_enhancer import BaseEnhancer


class ResearchEnhancer(BaseEnhancer):
    """Enhancer for research function."""

    @property
    def supported_functions(self) -> list[str]:
        return ["research"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Enhance research parameters."""

        # 1. QUERY EXTRACTION
        if "query" not in parameters:
            query = self._extract_query(user_input)
            if query:
                parameters["query"] = query

        # 2. DEPTH PREFERENCE
        if "depth" not in parameters:
            depth = self._extract_depth(user_input)
            if depth:
                parameters["depth"] = depth

        # 3. NUMBER OF SOURCES
        sources = self._extract_sources(user_input)
        if sources:
            parameters["sources"] = sources

        self.debug(f"Enhanced research parameters: {parameters}")
        return parameters

    def _extract_query(self, user_input: str) -> str | None:
        """Extract research query."""
        patterns = [
            r"research\s+(?:about\s+|on\s+|the\s+)?(.+?)(?:\s+with\s+\d+\s+sources|\s+in\s+detail|\s+comprehensively|$)",
            r"research:\s*(.+)$",
            r"look\s+up\s+(?:information\s+(?:about\s+|on\s+))?(.+)$",
            r"find\s+(?:information\s+(?:about\s+|on\s+))?(.+)$",
            r"search\s+(?:for\s+)?(?:information\s+(?:about\s+|on\s+))?(.+)$",
        ]

        query = self.extract_multiple_patterns(patterns, user_input)
        if query:
            query = query.strip('"\'')
            if query.endswith(".") and len(query) < 100:
                query = query.rstrip(".")
            return query

        # Fallback: remove trigger words
        query = re.sub(
            r"^(?:research|look\s+up|find|search)\s+",
            "",
            user_input,
            flags=re.IGNORECASE,
        ).strip()
        return query if query else None

    def _extract_depth(self, user_input: str) -> str | None:
        """Extract depth preference."""
        patterns = {
            r"(?:brief|quick|overview|high-level)": "overview",
            r"(?:detailed|thorough)": "detailed",
            r"(?:comprehensive|in-depth|extensive|complete)": "comprehensive",
        }

        for pattern, depth_level in patterns.items():
            if re.search(pattern, user_input.lower()):
                return depth_level
        return None

    def _extract_sources(self, user_input: str) -> int | None:
        """Extract number of sources."""
        match = re.search(r"(\d+)\s+sources?", user_input.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return None
