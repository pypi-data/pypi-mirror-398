# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Function Plugin Layer - Universal function system with context gathering"""

from ..core.registry.function_registry import FunctionRegistry
from .analysis.analysis_functions import (
    ExplainFunction,
    ResearchFunction,
    SummarizeFunction,
)
from .code.code_functions import CodeGenerateFunction, CodeReviewFunction
from .content.content_functions import (
    ContentGenerateFunction,
    EmailContentFunction,
    SocialPostFunction,
    TwitterContentFunction,
    UniversalContentFunction,
)
from .content.template_functions import (
    TemplateFunction,
    TemplateListFunction,
)
from .git.git_functions import (
    GitDiffFunction,
    GitStatusFunction,
)
from .shell.contextual_shell_functions import (
    ContextualShellFunction,
)
from .shell.enhanced_shell_functions import (
    EnhancedShellCommandFunction,
)
from .shell.explain_command_function import (
    ExplainCommandFunction,
)
from .shell.shell_functions import (
    ShellCommandFunction,
)
from .shell.streaming_shell_functions import (
    StreamingShellFunction,
)
from .system.stats_functions import StatsFunction
from .system.stats_models_function import StatsModelsFunction
from .system.stats_cost_function import StatsCostFunction
from .translation.translation_functions import TranslationFunction, LanguageDetectionFunction
from .mcp.mcp_functions import MCPToolFunction
from .mcp.mcp_management_functions import (
    MCPAddFunction,
    MCPRemoveFunction,
    MCPListFunction,
    MCPEnableFunction,
    MCPDisableFunction,
    MCPCatalogFunction,
    MCPInstallFunction,
    MCPStatusFunction,
    GitHubIssueFunction,
    MCPTestFunction,
    MCPUpdateFunction,
)


def register_all_functions(registry: FunctionRegistry) -> None:
    """Register all built-in functions with the registry

    NOTE: Legacy server-side functions removed in v0.6.0:
    - GitCommitFunction, GitPRFunction, GitBranchFunction (use 'aii run git <operation>' instead)
    - GitContextFunction, FileContextFunction, SystemContextFunction (use shell commands or MCP tools)

    See: system-dev-docs/aii-cli/issues/issue-005-v0.6.0-architecture-compliance-audit.md
    """

    # Content generation functions (universal)
    registry.register_plugin(UniversalContentFunction())
    registry.register_plugin(TwitterContentFunction())
    registry.register_plugin(EmailContentFunction())
    registry.register_plugin(ContentGenerateFunction())
    registry.register_plugin(SocialPostFunction())

    # Template functions (v0.4.7)
    registry.register_plugin(TemplateFunction())
    registry.register_plugin(TemplateListFunction())

    # Git functions (stateless only)
    registry.register_plugin(GitDiffFunction())
    registry.register_plugin(GitStatusFunction())

    # Translation functions
    registry.register_plugin(TranslationFunction())
    registry.register_plugin(LanguageDetectionFunction())

    # Code functions
    registry.register_plugin(CodeReviewFunction())
    registry.register_plugin(CodeGenerateFunction())

    # Analysis functions
    registry.register_plugin(SummarizeFunction())
    registry.register_plugin(ExplainFunction())
    registry.register_plugin(ResearchFunction())

    # Shell functions with Smart Command Triage System
    registry.register_plugin(EnhancedShellCommandFunction())

    # Command explanation function (v0.4.12)
    registry.register_plugin(ExplainCommandFunction())

    # Streaming shell functions with real-time feedback
    registry.register_plugin(StreamingShellFunction())

    # Contextual shell functions with conversation memory
    registry.register_plugin(ContextualShellFunction())

    # System functions (v0.4.7, v0.9.0)
    registry.register_plugin(StatsFunction())
    registry.register_plugin(StatsModelsFunction())  # v0.9.0
    registry.register_plugin(StatsCostFunction())  # v0.9.0

    # MCP functions (v0.4.8)
    registry.register_plugin(MCPToolFunction())

    # MCP management functions (v0.4.9+)
    registry.register_plugin(MCPAddFunction())
    registry.register_plugin(MCPRemoveFunction())
    registry.register_plugin(MCPListFunction())
    registry.register_plugin(MCPEnableFunction())
    registry.register_plugin(MCPDisableFunction())
    registry.register_plugin(MCPCatalogFunction())
    registry.register_plugin(MCPInstallFunction())
    registry.register_plugin(MCPStatusFunction())  # v0.4.10
    registry.register_plugin(GitHubIssueFunction())  # v0.4.10
    registry.register_plugin(MCPTestFunction())  # v0.4.10
    registry.register_plugin(MCPUpdateFunction())  # v0.4.10

    # Function registration complete - no output needed for clean UX


__all__ = [
    # Git functions (stateless only - legacy server-side functions removed in v0.6.0)
    "GitDiffFunction",
    "GitStatusFunction",
    # Translation
    "TranslationFunction",
    "LanguageDetectionFunction",
    # Code
    "CodeGenerateFunction",
    "CodeReviewFunction",
    # Analysis
    "SummarizeFunction",
    "ExplainFunction",
    "ResearchFunction",
    # Content generation
    "UniversalContentFunction",
    "TwitterContentFunction",
    "EmailContentFunction",
    "ContentGenerateFunction",
    "SocialPostFunction",
    # Templates
    "TemplateFunction",
    "TemplateListFunction",
    # Shell
    "ShellCommandFunction",
    "EnhancedShellCommandFunction",
    "ExplainCommandFunction",
    "StreamingShellFunction",
    "ContextualShellFunction",
    # System
    "StatsFunction",
    "StatsModelsFunction",
    "StatsCostFunction",
    # MCP
    "MCPToolFunction",
    "MCPAddFunction",
    "MCPRemoveFunction",
    "MCPListFunction",
    "MCPEnableFunction",
    "MCPDisableFunction",
    "MCPCatalogFunction",
    "MCPInstallFunction",
    "MCPStatusFunction",
    "GitHubIssueFunction",
    "MCPTestFunction",
    "MCPUpdateFunction",
    # Registry
    "register_all_functions",
]
