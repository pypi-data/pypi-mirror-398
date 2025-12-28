# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""External integrations"""

from .web_search import SearchResult, WebSearchClient
from .mcp.client_manager import MCPClientManager
from .mcp.models import ToolCallResult

__all__ = ["WebSearchClient", "SearchResult", "MCPClientManager", "ToolCallResult"]
