# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Base class and protocol for function parameter enhancers."""


import os
import re
from typing import Any, Protocol, runtime_checkable

# Debug mode flag (set via environment variable)
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


@runtime_checkable
class ParameterEnhancer(Protocol):
    """Protocol for parameter enhancement plugins."""

    @property
    def supported_functions(self) -> list[str]:
        """List of function names this enhancer supports."""
        ...

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """
        Enhance parameters for a specific function.

        Args:
            parameters: Raw parameters from LLM
            user_input: Original user input
            context: Optional chat context

        Returns:
            Enhanced parameters dict
        """
        ...


class BaseEnhancer:
    """Base implementation with common utilities."""

    def extract_pattern(
        self, pattern: str, text: str, group: int = 1
    ) -> str | None:
        """
        Extract text using regex pattern.

        Args:
            pattern: Regex pattern
            text: Text to search
            group: Group number to extract (default: 1)

        Returns:
            Extracted text or None if not found
        """
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(group).strip() if match else None

    def extract_multiple_patterns(
        self, patterns: list[str], text: str
    ) -> str | None:
        """
        Try multiple patterns, return first match.

        Args:
            patterns: List of regex patterns to try
            text: Text to search

        Returns:
            First match or None
        """
        for pattern in patterns:
            result = self.extract_pattern(pattern, text)
            if result:
                return result
        return None

    def normalize_parameter(
        self, parameters: dict, old_key: str, new_key: str
    ) -> dict:
        """
        Rename parameter key if exists.

        Args:
            parameters: Parameters dict
            old_key: Old parameter name
            new_key: New parameter name

        Returns:
            Updated parameters dict
        """
        if old_key in parameters and new_key not in parameters:
            parameters[new_key] = parameters.pop(old_key)
        return parameters

    def debug(self, message: str) -> None:
        """
        Print debug message if DEBUG_MODE enabled.

        Args:
            message: Debug message to print
        """
        if DEBUG_MODE:
            print(f"🔍 DEBUG [{self.__class__.__name__}]: {message}")
