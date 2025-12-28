# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Git Functions - Git workflow automation with AI assistance

NOTE: This file now contains only stateless git functions that don't require file system access.
Legacy server-side git operation functions (GitCommitFunction, GitPRFunction, GitBranchFunction)
have been removed in v0.6.0 as part of the unified architecture refactoring.

Use Client-Owned Workflows instead:
- For git commit: `aii run git commit` (not `aii commit`)
- For pull requests: `aii run git pr` (not `aii pr`)
- For branches: Use git CLI directly

See: system-dev-docs/aii-cli/issues/issue-005-v0.6.0-architecture-compliance-audit.md
"""


import subprocess
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    ParameterSchema,
    ValidationResult,
)

# Import individual function implementations
from .git_diff import GitDiffFunction
from .git_status import GitStatusFunction
