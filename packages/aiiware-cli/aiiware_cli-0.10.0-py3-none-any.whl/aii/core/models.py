# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Core data models and types used across the engine"""


from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class FunctionCategory(Enum):
    """Categories for function plugins"""

    GIT = "git"
    TRANSLATION = "translation"
    CODE = "code"
    DOCUMENT = "document"
    ANALYSIS = "analysis"
    SYSTEM = "system"
    CONTENT = "content"
    CUSTOM = "custom"


class FunctionSafety(Enum):
    """Safety categories for functions"""

    SAFE = "safe"  # No confirmation needed (read-only, informational)
    CONTEXT_DEPENDENT = "context_dependent"  # Confirm based on confidence/context
    RISKY = "risky"  # Always confirm (destructive, external actions)
    DESTRUCTIVE = "destructive"  # Highest risk (data loss, system changes)


class OutputMode(Enum):
    """Output display modes for function results"""

    CLEAN = "clean"  # Just the result, minimal formatting, no metadata
    STANDARD = "standard"  # Result + basic metrics (time, tokens, cost)
    THINKING = "thinking"  # Full thinking mode with reasoning and context
    AUTO = "auto"  # Let function decide based on its nature


class RouteSource(Enum):
    """Source of route decision"""

    DIRECT_MATCH = "direct_match"
    LLM_RECOGNITION = "llm_recognition"
    FALLBACK = "fallback"


@dataclass
class RecognitionResult:
    """Result of intent recognition"""

    intent: str
    confidence: float
    parameters: dict[str, Any]
    function_name: str
    requires_confirmation: bool = False
    reasoning: str = ""
    source: RouteSource = RouteSource.LLM_RECOGNITION
    intent_recognition_tokens: dict[str, int] = field(default_factory=dict)

    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high enough for direct execution"""
        return self.confidence >= 0.8

    @property
    def needs_clarification(self) -> bool:
        """Check if confidence is too low and needs clarification"""
        return self.confidence < 0.5


@dataclass
class ValidationResult:
    """Result of parameter validation"""

    valid: bool
    errors: list[str] = field(default_factory=list)
    normalized_params: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of function execution"""

    success: bool
    message: str
    data: dict[str, Any] | None = None
    next_actions: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    function_name: str = ""


@dataclass
class ExecutionContext:
    """Context for function execution"""

    chat_context: Any  # ChatContext
    user_input: str
    function_name: str
    parameters: dict[str, Any]
    client_type: str = "cli"  # Client source: "cli", "vscode", "chrome", "api"
    llm_provider: Any = None  # LLMProvider
    web_client: Any = None  # WebSearchClient
    mcp_client: Any = None  # MCPClient (not used in v0.6.0 cloud-only mode)
    config: dict[str, Any] = field(default_factory=dict)
    offline_mode: bool = False
    streaming_callback: Any = None  # Optional[Callable[[str], None]] for token streaming
    websocket_handler: Any = None  # WebSocket handler for client delegation (v0.6.0 cloud-only MCP)


@dataclass
class ParameterSchema:
    """Schema for function parameters"""

    name: str
    type: str
    required: bool = False
    description: str = ""
    default: Any = None
    choices: list[str] | None = None
    validation_regex: str | None = None


@dataclass
class FunctionDefinition:
    """Definition of a function plugin"""

    name: str
    description: str
    category: FunctionCategory
    parameters: dict[str, ParameterSchema]
    execution_handler: Callable[..., Any]
    confirmation_required: bool = True
    requires_web: bool = False
    requires_mcp: bool = False
    requires_files: bool = False
    examples: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@runtime_checkable
class FunctionPlugin(Protocol):
    """Protocol for function plugins"""

    @property
    def name(self) -> str:
        """Unique function name"""
        ...

    @property
    def description(self) -> str:
        """Human-readable description for LLM recognition"""
        ...

    @property
    def category(self) -> FunctionCategory:
        """Function category"""
        ...

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        """Expected parameters with validation schema"""
        ...

    @property
    def requires_confirmation(self) -> bool:
        """Whether this function requires user confirmation"""
        ...

    @property
    def safety_level(self) -> FunctionSafety:
        """Safety level of this function for confirmation logic"""
        ...

    @property
    def default_output_mode(self) -> OutputMode:
        """
        Preferred output mode for this function.
        CLEAN: Just the result (translate, explain, summarize)
        STANDARD: Result + metrics (most functions)
        THINKING: Full reasoning display (git_commit, research)
        AUTO: Decide based on context
        """
        return OutputMode.STANDARD  # Default for most functions

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """List of output modes this function supports (for CLI override)"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if all prerequisites are met"""
        ...

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Main execution logic"""
        ...


@dataclass
class CacheEntry:
    """Cache entry for performance optimization"""

    key: str
    value: Any
    timestamp: datetime
    ttl: float  # time to live in seconds
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl <= 0:
            return False  # Never expires
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring"""

    function_name: str
    execution_time: float
    success: bool
    confidence: float
    cache_hit: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ErrorContext:
    """Context information for error handling"""

    function_name: str
    user_input: str
    error_type: str
    error_message: str
    stack_trace: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
