# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for shell functions."""


from typing import Any

from .base_enhancer import BaseEnhancer


class ShellEnhancer(BaseEnhancer):
    """Enhancer for shell command functions."""

    @property
    def supported_functions(self) -> list[str]:
        return [
            "shell_command",
            "streaming_shell",
            "contextual_shell",
            "enhanced_shell",
        ]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Enhance shell command parameters.

        Shell functions typically receive parameters normalized by the recognizer.
        This enhancer ensures parameter name consistency.
        """
        # Normalize parameter names (command → request)
        parameters = self.normalize_parameter(parameters, "command", "request")

        # Ensure request exists
        if "request" not in parameters:
            parameters["request"] = user_input.strip()

        # Default execute to True (with confirmation)
        if "execute" not in parameters:
            parameters["execute"] = True

        self.debug(f"Enhanced shell parameters: {parameters}")
        return parameters
