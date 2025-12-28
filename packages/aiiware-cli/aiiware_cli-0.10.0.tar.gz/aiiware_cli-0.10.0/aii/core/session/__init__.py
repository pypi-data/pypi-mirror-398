# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Session management for AII with cumulative metrics tracking"""

from .models import FunctionExecution, SessionMetrics
from .manager import SessionManager, start_session, get_session, add_execution, finalize_session, is_active
from .semantic_analyzer import SessionSemanticAnalyzer, SessionInsights

__all__ = [
    "FunctionExecution",
    "SessionMetrics",
    "SessionManager",
    "SessionSemanticAnalyzer",
    "SessionInsights",
    "start_session",
    "get_session",
    "add_execution",
    "finalize_session",
    "is_active"
]
