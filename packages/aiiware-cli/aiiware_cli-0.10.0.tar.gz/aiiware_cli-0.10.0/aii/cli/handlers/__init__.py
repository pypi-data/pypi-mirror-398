# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Command handlers for AII CLI (v0.6.1).

This package contains handler modules for Tier 1 (local) commands.
Tier 2 (AI) commands are handled via WebSocket client (client.py).
"""

from .config_handler import handle_config_command
from .mcp_handler import handle_mcp_command
from .serve_handler import handle_serve_command
from .prompt_handler import handle_prompt_command
from .other_handlers import (
    handle_history_command,
    handle_template_command,
    handle_stats_command,
    handle_doctor_command,
    handle_completion_command,
    handle_help_command,
)

__all__ = [
    "handle_config_command",
    "handle_mcp_command",
    "handle_serve_command",
    "handle_prompt_command",
    "handle_history_command",
    "handle_template_command",
    "handle_stats_command",
    "handle_doctor_command",
    "handle_completion_command",
    "handle_help_command",
]
