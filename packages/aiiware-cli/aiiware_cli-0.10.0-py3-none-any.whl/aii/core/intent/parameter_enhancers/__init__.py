# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancement system for intent recognition.

This module provides a plugin-based system for enhancing LLM-generated parameters
with function-specific intelligence.
"""


from typing import Any

from .base_enhancer import ParameterEnhancer, BaseEnhancer
from .code_enhancer import CodeEnhancer
from .content_enhancer import ContentEnhancer
from .translation_enhancer import TranslationEnhancer
from .research_enhancer import ResearchEnhancer
from .git_enhancer import GitEnhancer
from .mcp_enhancer import MCPEnhancer
from .shell_enhancer import ShellEnhancer


class EnhancerRegistry:
    """Registry for parameter enhancers."""

    def __init__(self):
        self.enhancers: dict[str, ParameterEnhancer] = {}
        self._register_default_enhancers()

    def _register_default_enhancers(self):
        """Register all built-in enhancers."""
        enhancers = [
            CodeEnhancer(),
            ContentEnhancer(),
            TranslationEnhancer(),
            ResearchEnhancer(),
            GitEnhancer(),
            MCPEnhancer(),
            ShellEnhancer(),
        ]

        for enhancer in enhancers:
            for function_name in enhancer.supported_functions:
                self.enhancers[function_name] = enhancer

    def enhance(
        self, function_name: str, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """
        Enhance parameters for a function.

        Args:
            function_name: Name of the function
            parameters: Raw parameters from LLM
            user_input: Original user input
            context: Optional chat context

        Returns:
            Enhanced parameters (or original if no enhancer found)
        """
        enhancer = self.enhancers.get(function_name)
        if enhancer:
            return enhancer.enhance(parameters, user_input, context)
        return parameters

    def register(self, enhancer: ParameterEnhancer) -> None:
        """Register a custom enhancer."""
        for function_name in enhancer.supported_functions:
            self.enhancers[function_name] = enhancer


# Global registry instance
_registry = EnhancerRegistry()


def get_enhancer_registry() -> EnhancerRegistry:
    """Get the global enhancer registry."""
    return _registry


__all__ = [
    "ParameterEnhancer",
    "BaseEnhancer",
    "CodeEnhancer",
    "ContentEnhancer",
    "TranslationEnhancer",
    "ResearchEnhancer",
    "GitEnhancer",
    "MCPEnhancer",
    "ShellEnhancer",
    "EnhancerRegistry",
    "get_enhancer_registry",
]
