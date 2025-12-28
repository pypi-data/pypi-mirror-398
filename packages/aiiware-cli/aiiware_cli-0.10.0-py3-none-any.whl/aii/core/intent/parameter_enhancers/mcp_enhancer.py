# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for MCP functions."""


from typing import Any

from .base_enhancer import BaseEnhancer


class MCPEnhancer(BaseEnhancer):
    """Enhancer for mcp_tool function."""

    @property
    def supported_functions(self) -> list[str]:
        return ["mcp_tool"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Enhance MCP tool parameters.

        MCP tool function expects a 'user_request' parameter containing the full
        natural language request. The function will then use LLM to select the
        appropriate MCP tool and generate arguments.
        """
        # Always provide the full user input as user_request
        parameters["user_request"] = user_input

        self.debug(f"Enhanced mcp_tool parameters: {parameters}")
        return parameters
