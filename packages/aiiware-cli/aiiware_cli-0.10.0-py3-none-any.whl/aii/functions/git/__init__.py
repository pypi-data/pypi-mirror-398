# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Git Functions - Git workflow and assistance functions

NOTE: Legacy server-side git operation functions (GitCommitFunction, GitPRFunction, GitBranchFunction)
have been removed in v0.6.0. Use Client-Owned Workflows instead:
- For git commit: `aii run git commit` (not `aii commit`)
- For pull requests: `aii run git pr` (not `aii pr`)

See: system-dev-docs/aii-cli/issues/issue-005-v0.6.0-architecture-compliance-audit.md
"""

from .git_functions import GitDiffFunction, GitStatusFunction

__all__ = ["GitDiffFunction", "GitStatusFunction"]
