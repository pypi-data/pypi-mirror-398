# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Server Management Functions

Commands for managing MCP server configurations:
- mcp_add: Add a new MCP server
- mcp_remove: Remove an MCP server
- mcp_list: List all configured servers
- mcp_enable: Enable a disabled server
- mcp_disable: Disable a server (keeps config)
- mcp_catalog: List popular pre-configured servers
- mcp_install: Install server from catalog
"""


import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
)
from .config_manager import MCPConfigManager

logger = logging.getLogger(__name__)


from .mcp_add import MCPAddFunction
from .mcp_remove import MCPRemoveFunction
from .mcp_list import MCPListFunction

from .mcp_enable import MCPEnableFunction
from .mcp_disable import MCPDisableFunction
from .mcp_catalog import MCPCatalogFunction

from .mcp_install import MCPInstallFunction
from .mcp_status import MCPStatusFunction

from .mcp_test import MCPTestFunction
from .mcp_update import MCPUpdateFunction

# Import GitHub function (moved to github/ module)
from ..github import GitHubIssueFunction
