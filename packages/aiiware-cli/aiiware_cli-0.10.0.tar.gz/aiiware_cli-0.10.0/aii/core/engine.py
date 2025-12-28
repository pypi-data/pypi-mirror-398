# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Main AII Engine - Orchestrates all components"""


import os
from pathlib import Path
from typing import Any, List

# Debug mode flag
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")

from ..cli.output_formatter import (
    FormattedOutput,
    OutputFormatter,
    OutputSegment,
    OutputType,
)
from ..cli.header_manager import OutputHeaderManager, VerbosityLevel, ExecutionMode, FunctionSafety
from ..cli.footer_formatter import SessionFooterFormatter
from ..cli.output_mode_formatter import OutputModeFormatter
from ..config.output_config import OutputConfig
from ..data.storage.conversation_manager import ConversationManager
from .context.manager import ContextManager
from .context.models import ChatContext
from .execution.executor import ExecutionEngine
from .intent.recognizer import IntentRecognizer
from .models import ExecutionContext, ExecutionResult, RecognitionResult, OutputMode
from .registry.function_registry import FunctionRegistry
from .session import SessionManager, start_session, finalize_session, FunctionExecution
from .session.models import SessionMetrics
from .session.semantic_analyzer import SessionSemanticAnalyzer
from .cost.calculator import CostCalculator
from .budget.budget_manager import BudgetManager


class AIIEngine:
    """Main engine that orchestrates all AII components"""

    def __init__(
        self, config: dict[str, Any] | None = None, storage_path: Path | None = None,
        output_config: OutputConfig | None = None, config_manager: Any | None = None
    ):
        """Initialize AII Engine with configuration"""
        self.config = config or {}
        self.storage_path = storage_path or Path.home() / ".aii"
        self.output_config = output_config or OutputConfig()
        self.config_manager = config_manager  # For output mode overrides

        # Initialize core components
        self.function_registry = FunctionRegistry()
        self.context_manager = ContextManager(storage_path)
        self.intent_recognizer = IntentRecognizer()
        # Initialize cost calculator for budget management
        self.cost_calculator = CostCalculator(self.storage_path)
        # Initialize budget manager (SRP: extracted from engine)
        self.budget_manager = BudgetManager(self.cost_calculator, self.output_config)

        # Initialize chat storage first (v0.4.7)
        from ..data.storage.chat_storage import ChatStorage
        self.chat_storage = ChatStorage(self.storage_path / "chats.db")

        # Initialize execution logger for model intelligence (v0.9.0)
        from .execution.execution_logger import ExecutionLogger
        self.execution_logger = ExecutionLogger(
            storage=self.chat_storage,
            batch_size=10,
            batch_timeout_ms=100
        )
        self._logger_started = False  # Track if logger has been started

        self.execution_engine = ExecutionEngine(
            self.function_registry,
            self.cost_calculator,
            self.execution_logger
        )
        self.output_formatter = OutputFormatter(
            use_colors=self.output_config.use_colors,
            use_emojis=self.output_config.use_emojis
        )

        # Initialize session output system with output configuration
        self.verbosity_level = self.output_config.get_effective_verbosity()
        self.execution_mode = ExecutionMode.CLI  # Default to CLI mode
        self.header_manager = OutputHeaderManager(
            verbosity=self.verbosity_level,
            mode=self.execution_mode,
            use_colors=self.output_config.use_colors,
            use_emojis=self.output_config.use_emojis
        )
        # Initialize semantic analyzer for footer insights
        self.semantic_analyzer = None  # Will be set when LLM provider is available
        self.footer_formatter = SessionFooterFormatter(
            use_colors=self.output_config.use_colors,
            use_emojis=self.output_config.use_emojis
        )
        self.output_mode_formatter = OutputModeFormatter(
            use_colors=self.output_config.use_colors,
            use_emojis=self.output_config.use_emojis
        )

        # Initialize conversation manager for enhanced context
        self.conversation_manager: ConversationManager | None = None

        # External integrations (to be injected)
        self.llm_provider: Any | None = None
        self.web_client: Any | None = None
        self.mcp_client: Any | None = None

        # State for handling confirmations
        self._last_recognition_result: RecognitionResult | None = None
        self._last_user_input: str | None = None
        self._last_context: ChatContext | None = None
        self._last_offline_mode: bool = False
        self._last_output_mode_override: OutputMode | None = None  # Store original output mode
        self._pending_shell_command: str | None = None
        self._pending_shell_tokens: dict[str, int] | None = None

        # Connect components
        self.intent_recognizer.register_function_registry(self.function_registry)

    def check_budget_warnings(self) -> List[str]:
        """Check budget status and return any warnings (delegates to BudgetManager)"""
        return self.budget_manager.check_warnings()

    def show_budget_warnings(self) -> None:
        """Display budget warnings if any (delegates to BudgetManager)"""
        self.budget_manager.display_warnings()

    def configure(
        self,
        llm_provider: Any = None,
        web_client: Any = None,
        mcp_client: Any = None,
        config: dict[str, Any] = None,
    ) -> None:
        """Configure external dependencies"""
        if llm_provider:
            self.llm_provider = llm_provider
            self.intent_recognizer.llm_provider = llm_provider

            # Initialize semantic analyzer for enhanced footer insights
            try:
                self.semantic_analyzer = SessionSemanticAnalyzer(llm_provider)
                # Update footer formatter with semantic analyzer
                self.footer_formatter = SessionFooterFormatter(
                    use_colors=self.footer_formatter.use_colors,
                    use_emojis=self.footer_formatter.use_emojis,
                    semantic_analyzer=self.semantic_analyzer
                )
            except (TypeError, AttributeError):
                # Skip semantic analyzer for mock providers
                pass

            # Initialize conversation manager with LLM provider (but skip for mocks)
            if not self.conversation_manager:
                # Only initialize with proper LLM providers, not test mocks
                try:
                    self.conversation_manager = ConversationManager(
                        storage_path=self.storage_path, llm_provider=llm_provider
                    )
                except (TypeError, AttributeError):
                    # Skip conversation manager initialization for mock providers
                    pass

        if web_client:
            self.web_client = web_client

        if mcp_client:
            self.mcp_client = mcp_client

        if config:
            self.config.update(config)

    def set_output_config(
        self,
        verbosity: VerbosityLevel = None,
        mode: ExecutionMode = None,
        use_colors: bool = True,
        use_emojis: bool = True
    ) -> None:
        """Configure output system settings"""
        if verbosity is not None:
            self.verbosity_level = verbosity
        if mode is not None:
            self.execution_mode = mode

        # Recreate header manager with new settings
        self.header_manager = OutputHeaderManager(
            verbosity=self.verbosity_level,
            mode=self.execution_mode,
            use_colors=use_colors,
            use_emojis=use_emojis
        )

        # Recreate footer formatter with new settings
        self.footer_formatter = SessionFooterFormatter(
            use_colors=use_colors,
            use_emojis=use_emojis
        )

    async def process_input(
        self,
        user_input: str,
        context: ChatContext | None = None,
        offline_mode: bool = False,
        session_id: str | None = None,
        status_display: Any | None = None,
        output_mode_override: OutputMode | None = None,  # CLI flag override
        client_type: str = "cli",  # v0.9.2: Track client source
    ) -> FormattedOutput:
        """Main input processing pipeline with enhanced context management"""
        try:
            # Start execution logger on first request (v0.9.0)
            if not self._logger_started:
                await self.execution_logger.start()
                self._logger_started = True

            # Track total wall-clock time from user's perspective
            import time
            total_start_time = time.time()

            # Initialize session for tracking cumulative metrics
            session_id = session_id or f"engine_session_{int(__import__('time').time())}"
            session = start_session(user_input, session_id)

            # Note: Header display will be determined after intent recognition
            # to respect CLEAN output mode preference

            # Show processing indicator
            if status_display:
                status_display.start_loading("Processing your request...", "spinner")

            # Enhanced context management
            conversation_context = ""
            contextual_info = {}  # Initialize for reuse
            # Skip conversation manager for git commit to avoid LLM hanging issue
            if self.conversation_manager and user_input != "commit":
                # Processing conversation context
                # Check if we should continue an existing conversation session
                if session_id:
                    await self.conversation_manager.continue_session(session_id)
                elif not self.conversation_manager.get_current_session():
                    # Create execution context for conversation manager
                    exec_context = ExecutionContext(
                        chat_context=context,
                        user_input=user_input,
                        function_name="",
                        parameters={},
                        client_type=client_type,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        config=self.config,
                        offline_mode=offline_mode,
                    )
                    await self.conversation_manager.start_new_session(exec_context)

                # Get contextual understanding of user input (single call, reuse result)
                contextual_info = (
                    await self.conversation_manager.get_contextual_understanding(
                        user_input
                    )
                )

                # Get conversation context if needed
                if contextual_info.get("needs_history", False):
                    conversation_context = (
                        await self.conversation_manager.get_conversation_context(
                            max_turns=3
                        )
                    )

            # Use current session context if none provided
            if context is None:
                if DEBUG_MODE: print("🔍 DEBUG: No context provided, checking current_session")
                context = self.context_manager.current_session
                if context is None:
                    if DEBUG_MODE: print("🔍 DEBUG: No current_session, attempting auto-load")
                    # Try to auto-load recent session first
                    context = await self.context_manager.auto_load_recent_session(
                        max_age_minutes=60
                    )
                    if context is None:
                        if DEBUG_MODE: print("🔍 DEBUG: Auto-load failed, starting new chat")
                        context = await self.context_manager.start_new_chat()
                    else:
                        if DEBUG_MODE: print(
                            f"🔍 DEBUG: Auto-load successful with {len(context.messages)} messages"
                        )
                else:
                    if DEBUG_MODE: print(
                        f"🔍 DEBUG: Using existing current_session with {len(context.messages)} messages"
                    )

            # Add user message to context
            await self.context_manager.add_message(context, "user", user_input)

            # Step 1: Recognize intent with enhanced context
            enhanced_user_input = user_input
            if conversation_context:
                enhanced_user_input = (
                    f"{conversation_context}\n\nCurrent Request: {user_input}"
                )

            # Add location context if available (reuse contextual_info from above)
            if contextual_info.get("inferred_location") and contextual_info.get(
                "location_inherited"
            ):
                location_hint = f"\n\nIMPORTANT CONTEXT: User's previous command was in {contextual_info['inferred_location']}. This request likely refers to the same location."
                enhanced_user_input += location_hint

            recognition_result = await self.intent_recognizer.recognize_intent(
                enhanced_user_input, context
            )

            import os
            if os.getenv("AII_DEBUG"):
                tokens = recognition_result.intent_recognition_tokens or {}
                print(f"🔍 DEBUG: Engine received recognition result - tokens={tokens}")

            # Determine output mode early to decide whether to show header
            # Priority: CLI flag override > config.yaml override > function default > STANDARD fallback
            if output_mode_override is not None:
                output_mode = output_mode_override
            else:
                # Check config.yaml for per-function override
                config_mode_str = None
                if self.config_manager:
                    config_mode_str = self.config_manager.get_output_mode(recognition_result.function_name)

                if config_mode_str:
                    # Convert string to OutputMode enum
                    output_mode = OutputMode(config_mode_str)
                else:
                    # Use function default
                    function_plugin = self.function_registry.plugins.get(recognition_result.function_name)
                    output_mode = function_plugin.default_output_mode if function_plugin else OutputMode.STANDARD

            # Show session header ONLY in THINKING mode (not CLEAN or STANDARD)
            if output_mode == OutputMode.THINKING:
                # Stop spinner temporarily to show header cleanly
                if status_display:
                    status_display.stop_loading()

                function_count = len(self.function_registry.list_functions()) if self.function_registry else 24
                self.header_manager.show_session_header(
                    user_input=user_input,
                    session_id=session.session_id,
                    llm_provider=getattr(self.llm_provider, 'provider_name', None) if self.llm_provider else None,
                    function_count=function_count
                )

                # Restart processing indicator
                if status_display:
                    status_display.start_loading("Processing your request...", "spinner")

            # Step 2: Handle confirmation if needed
            if recognition_result.requires_confirmation:
                # Stop spinner before showing any confirmation
                if status_display:
                    status_display.stop_loading()

                # For git commit, execute first to get thinking mode data, then show confirmation
                if recognition_result.function_name == "git_commit":
                    # Setup streaming for git commit execution
                    streaming_enabled = self.config.get("streaming", {}).get("enabled", True)
                    streaming_formatter = None

                    if streaming_enabled and self.llm_provider:
                        from ..cli.response_streaming_formatter import ResponseStreamingFormatter
                        enable_markdown = self.config.get("streaming", {}).get("enable_markdown", True)
                        show_cursor = self.config.get("streaming", {}).get("show_cursor", True)
                        streaming_formatter = ResponseStreamingFormatter(
                            enable_markdown=enable_markdown,
                            show_cursor=show_cursor
                        )
                        self.llm_provider._streaming_callback = streaming_formatter.update

                    try:
                        # Execute the git commit function first to generate the thinking mode data
                        execution_result = await self.execution_engine.execute_function(
                            recognition_result=recognition_result,
                            user_input=user_input,
                            chat_context=context,
                            config=self.config,
                            llm_provider=self.llm_provider,
                            web_client=self.web_client,
                            mcp_client=self.mcp_client,
                            offline_mode=offline_mode,
                        )
                    finally:
                        if streaming_formatter:
                            streaming_formatter.stop()
                        if self.llm_provider and hasattr(self.llm_provider, '_streaming_callback'):
                            delattr(self.llm_provider, '_streaming_callback')

                    # If execution failed (e.g., no staged changes), return the error
                    if not execution_result.success:
                        return self.output_formatter.format_execution_result(
                            execution_result.message,
                            recognition_result.function_name,
                            execution_result.success,
                        )

                    # If execution succeeded and has thinking mode data, show it with confirmation
                    if (
                        execution_result.success
                        and execution_result.data
                        and execution_result.data.get("thinking_mode")
                    ):

                        # Check if this requires commit/PR/branch confirmation
                        if execution_result.data.get("requires_commit_confirmation"):
                            # Store recognition state for git commit confirmation
                            self._last_recognition_result = recognition_result
                            self._last_user_input = user_input
                            self._last_context = context
                            self._last_offline_mode = offline_mode
                            # Store the commit message and thinking data for later execution
                            self._pending_git_commit_message = (
                                execution_result.data.get("commit_message")
                            )
                            self._pending_git_thinking_data = execution_result.data

                            # Display the git commit thinking mode with confirmation prompt
                            output = self.output_formatter.format_git_commit_thinking_mode(
                                context="git_commit mode",
                                git_diff=execution_result.data.get("git_diff", ""),
                                commit_message=execution_result.data.get("commit_message", ""),
                                reasoning=execution_result.data.get("reasoning", "Processing request..."),
                                confidence=execution_result.data.get("confidence"),
                                input_tokens=execution_result.data.get("input_tokens"),
                                output_tokens=execution_result.data.get("output_tokens"),
                                provider=execution_result.data.get("provider"),
                            )
                            return output
                        elif execution_result.data.get("requires_pr_confirmation"):
                            # Store recognition state for PR confirmation
                            self._last_recognition_result = recognition_result
                            self._last_user_input = user_input
                            self._last_context = context
                            self._last_offline_mode = offline_mode
                            # Display the PR preview with confirmation prompt
                            # The message already contains the formatted PR display
                            from datetime import datetime
                            segment = OutputSegment(content=execution_result.message, type=OutputType.TEXT)
                            output = FormattedOutput(
                                segments=[segment],
                                timestamp=datetime.now()
                            )
                            return output
                        elif execution_result.data.get("requires_branch_confirmation"):
                            # Store recognition state for branch confirmation
                            self._last_recognition_result = recognition_result
                            self._last_user_input = user_input
                            self._last_context = context
                            self._last_offline_mode = offline_mode

                            # Use git commit thinking mode formatter
                            output = (
                                self.output_formatter.format_git_commit_thinking_mode(
                                    context=f"{recognition_result.function_name} mode",
                                    git_diff=execution_result.data.get("git_diff", ""),
                                    commit_message=execution_result.data.get(
                                        "commit_message", ""
                                    ),
                                    reasoning=execution_result.data.get(
                                        "reasoning", "Processing request..."
                                    ),
                                    confidence=execution_result.data.get("confidence"),
                                    input_tokens=execution_result.data.get(
                                        "input_tokens"
                                    ),
                                    output_tokens=execution_result.data.get(
                                        "output_tokens"
                                    ),
                                    provider=execution_result.data.get("provider"),
                                )
                            )
                            return output

                # For other functions, use normal confirmation flow
                # Store recognition state for later execution
                self._last_recognition_result = recognition_result
                self._last_user_input = user_input
                self._last_context = context
                self._last_offline_mode = offline_mode

                confirmation_output = self.output_formatter.format_intent_recognition(
                    recognition_result.intent, recognition_result.confidence, True
                )
                return confirmation_output

            # Step 3: Execute function with streaming support
            # Check if streaming is enabled
            streaming_enabled = self.config.get("streaming", {}).get("enabled", True)
            streaming_formatter = None

            if DEBUG_MODE:
                print(f"🔍 DEBUG: Streaming enabled: {streaming_enabled}, has LLM provider: {self.llm_provider is not None}")

            if streaming_enabled and self.llm_provider:
                # Import streaming formatter
                from ..cli.response_streaming_formatter import ResponseStreamingFormatter

                # Create streaming formatter and pass status_display so it can stop the spinner
                enable_markdown = self.config.get("streaming", {}).get("enable_markdown", True)
                show_cursor = self.config.get("streaming", {}).get("show_cursor", True)
                streaming_formatter = ResponseStreamingFormatter(
                    enable_markdown=enable_markdown,
                    show_cursor=show_cursor,
                    status_display=status_display  # Pass spinner so formatter can stop it
                )

                if DEBUG_MODE:
                    print(f"🔍 DEBUG: Created streaming formatter, starting stream...")

                # Attach streaming callback to LLM provider
                # We store it as a temporary attribute so functions can access it
                self.llm_provider._streaming_callback = streaming_formatter.update

            # Stop the "Processing your request..." spinner before function execution
            # This prevents overlap with function-specific progress indicators (e.g., git commit)
            if status_display:
                status_display.stop_loading()

            try:
                execution_result = await self.execution_engine.execute_function(
                    recognition_result=recognition_result,
                    user_input=user_input,
                    chat_context=context,
                    config=self.config,
                    llm_provider=self.llm_provider,
                    web_client=self.web_client,
                    mcp_client=self.mcp_client,
                    offline_mode=offline_mode,
                )
            finally:
                # Clean up streaming callback
                # Note: streaming_formatter.complete() is called later if execution succeeds
                # Only stop here if there was an error
                if self.llm_provider and hasattr(self.llm_provider, '_streaming_callback'):
                    delattr(self.llm_provider, '_streaming_callback')

            # Step 4: Add assistant response to context
            # Include executed command in the message for context preservation
            assistant_message = execution_result.message
            if (
                execution_result.data
                and recognition_result.function_name in ["shell_command"]
                and execution_result.data.get("command")
            ):
                command = execution_result.data.get("command")
                assistant_message = (
                    f"{execution_result.message}\nExecuted command: {command}"
                )

            await self.context_manager.add_message(
                context,
                "assistant",
                assistant_message,
                {
                    "function": recognition_result.function_name,
                    "success": execution_result.success,
                    "executed_command": (
                        execution_result.data.get("command")
                        if execution_result.data
                        else None
                    ),
                },
            )

            # Step 4.4: Log execution to database (v0.4.7)
            await self._log_execution(
                chat_id=context.chat_id if context else session_id,
                function_name=recognition_result.function_name,
                parameters=recognition_result.parameters,
                result=execution_result,
                success=execution_result.success
            )

            # Step 4.4.1: Log execution metrics for analytics (v0.9.0)
            try:
                from .models import ExecutionContext as AnalyticsContext

                # Create execution context for analytics
                analytics_context = AnalyticsContext(
                    chat_context=context,
                    user_input=user_input,
                    function_name=recognition_result.function_name,
                    parameters=recognition_result.parameters,
                    llm_provider=self.llm_provider,
                    web_client=self.web_client,
                )

                # Log execution (non-blocking, <5ms)
                execution_time_ms = int(execution_result.execution_time * 1000) if execution_result.execution_time else 0
                await self.execution_logger.log_execution(
                    result=execution_result,
                    context=analytics_context,
                    execution_time_ms=execution_time_ms,
                    ttft_ms=None,  # TTFT not currently tracked
                )
            except Exception as e:
                # Don't fail the request if analytics logging fails
                logger.warning(f"Failed to log execution metrics: {e}")

            # Step 4.5: Add conversation turn if conversation manager is available
            if self.conversation_manager:
                try:
                    command_executed = None
                    execution_output = None
                    tokens_consumed = {}

                    # Extract command and output for shell functions
                    if execution_result.data and recognition_result.function_name in [
                        "shell_command",
                                "streaming_shell",
                    ]:
                        command_executed = execution_result.data.get("command")
                        execution_output = execution_result.data.get("execution_output")

                    # Extract token information
                    if execution_result.data:
                        input_tokens = execution_result.data.get("input_tokens")
                        output_tokens = execution_result.data.get("output_tokens")
                        if input_tokens is not None or output_tokens is not None:
                            tokens_consumed = {
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                            }

                    await self.conversation_manager.add_turn(
                        user_input=user_input,
                        ai_response=execution_result.message,
                        command_executed=command_executed,
                        execution_result=execution_output,
                        tokens_consumed=tokens_consumed,
                    )
                except Exception as e:
                    # If conversation manager fails, continue without it
                    pass

            # Step 5: Format output
            # Note: output_mode already determined earlier (after intent recognition)

            # Handle shell command confirmation state (must happen BEFORE output formatting)
            # This needs to work in ALL output modes (CLEAN, STANDARD, THINKING)
            if recognition_result.function_name in ["shell_command"]:
                if execution_result.data and execution_result.data.get("requires_execution_confirmation"):
                    # Store recognition state for shell command confirmation
                    self._last_recognition_result = recognition_result
                    self._last_user_input = user_input
                    self._last_context = context
                    self._last_offline_mode = offline_mode
                    self._last_output_mode_override = output_mode_override  # Store original output mode!
                    self._pending_shell_command = execution_result.data.get("command", "")
                    # Store token usage: combine intent recognition tokens + function execution tokens
                    intent_tokens = recognition_result.intent_recognition_tokens or {}
                    exec_tokens_input = execution_result.data.get("input_tokens", 0) or 0
                    exec_tokens_output = execution_result.data.get("output_tokens", 0) or 0

                    import os
                    if os.getenv("AII_DEBUG"):
                        print(f"🔍 DEBUG: Token tracking - intent_tokens={intent_tokens}, exec_tokens=({exec_tokens_input}, {exec_tokens_output})")

                    self._pending_shell_tokens = {
                        "input_tokens": intent_tokens.get("input_tokens", 0) + exec_tokens_input,
                        "output_tokens": intent_tokens.get("output_tokens", 0) + exec_tokens_output,
                    }

                    # v0.4.13: For shell confirmation, we need to continue to normal formatting
                    # so that main.py can detect and handle the confirmation prompt
                    # Just ensure we stop the spinner before displaying
                    if status_display:
                        status_display.stop_loading()

            # Determine if we should use full thinking mode display
            # Use thinking mode if: output_mode is THINKING OR requires confirmation (git commit/PR/branch)
            should_show_thinking = (
                execution_result.success
                and execution_result.data
                and execution_result.data.get("thinking_mode")
                and (
                    output_mode == OutputMode.THINKING
                    or execution_result.data.get("requires_commit_confirmation")
                    or execution_result.data.get("requires_pr_confirmation")
                    or execution_result.data.get("requires_branch_confirmation")
                )
            )

            if output_mode == OutputMode.CLEAN:
                # CLEAN mode: Just the result, no metadata
                if status_display:
                    status_display.stop_loading()

                formatted_result = self.output_mode_formatter.format_result(
                    execution_result,
                    output_mode,
                    recognition_result.function_name
                )

                from datetime import datetime
                segment = OutputSegment(content=formatted_result, type=OutputType.TEXT)
                output = FormattedOutput(
                    segments=[segment],
                    timestamp=datetime.now()
                )
            elif should_show_thinking:
                # Clear processing indicator
                if status_display:
                    status_display.stop_loading()

                # Check if this is git commit/PR/branch thinking mode
                if execution_result.data.get("requires_commit_confirmation"):
                    # Store recognition state for git commit confirmation
                    self._last_recognition_result = recognition_result
                    self._last_user_input = user_input
                    self._last_context = context
                    self._last_offline_mode = offline_mode
                    # Store the commit message and thinking data for later execution
                    self._pending_git_commit_message = execution_result.data.get(
                        "commit_message"
                    )
                    self._pending_git_thinking_data = execution_result.data

                    # Display the git commit thinking mode with confirmation prompt
                    output = self.output_formatter.format_git_commit_thinking_mode(
                        context="git_commit mode",
                        git_diff=execution_result.data.get("git_diff", ""),
                        commit_message=execution_result.data.get("commit_message", ""),
                        reasoning=execution_result.data.get("reasoning", "Processing request..."),
                        confidence=execution_result.data.get("confidence"),
                        input_tokens=execution_result.data.get("input_tokens"),
                        output_tokens=execution_result.data.get("output_tokens"),
                        provider=execution_result.data.get("provider"),
                    )
                    return output
                elif execution_result.data.get("requires_pr_confirmation"):
                    # Store recognition state for PR confirmation
                    self._last_recognition_result = recognition_result
                    self._last_user_input = user_input
                    self._last_context = context
                    self._last_offline_mode = offline_mode

                    # Display the PR preview with confirmation prompt
                    from datetime import datetime
                    segment = OutputSegment(content=execution_result.message, type=OutputType.TEXT)
                    output = FormattedOutput(
                        segments=[segment],
                        timestamp=datetime.now()
                    )
                    return output

                elif execution_result.data.get("requires_branch_confirmation"):
                    # Store recognition state for branch confirmation
                    self._last_recognition_result = recognition_result
                    self._last_user_input = user_input
                    self._last_context = context
                    self._last_offline_mode = offline_mode
                    # Store the commit message and thinking data for later execution
                    self._pending_git_commit_message = execution_result.data.get(
                        "commit_message"
                    )
                    self._pending_git_thinking_data = execution_result.data

                    # Use git commit thinking mode formatter
                    output = self.output_formatter.format_git_commit_thinking_mode(
                        context=f"{recognition_result.function_name} mode",
                        git_diff=execution_result.data.get("git_diff", ""),
                        commit_message=execution_result.data.get("commit_message", ""),
                        reasoning=execution_result.data.get(
                            "reasoning", "Processing request..."
                        ),
                        confidence=execution_result.data.get("confidence"),
                        input_tokens=execution_result.data.get("input_tokens"),
                        output_tokens=execution_result.data.get("output_tokens"),
                        provider=execution_result.data.get("provider"),
                    )
                elif execution_result.data.get("content_type"):
                    # Use universal thinking mode formatter for content generation
                    output = self.output_formatter.format_universal_thinking_mode(
                        context=f"Universal {execution_result.data.get('content_type', 'content')} generation",
                        request=user_input,
                        reasoning=execution_result.data.get(
                            "reasoning", "Processing request..."
                        ),
                        content=execution_result.data.get(
                            "content", execution_result.message
                        ),
                        content_type=execution_result.data.get(
                            "content_type", "content"
                        ),
                        confidence=execution_result.data.get("confidence"),
                        input_tokens=execution_result.data.get("input_tokens"),
                        output_tokens=execution_result.data.get("output_tokens"),
                        provider=execution_result.data.get("provider"),
                        context_used=execution_result.data.get("context_used", False),
                        context_summary=execution_result.data.get("context_summary"),
                    )
                elif recognition_result.function_name in [
                    "shell_command",
                    ]:
                    # Confirmation state already stored above (works for all output modes)
                    if execution_result.data.get("requires_execution_confirmation"):
                        # Use shell thinking mode formatter with confirmation prompt
                        output = self.output_formatter.format_shell_thinking_mode(
                            context="Shell command generation",
                            request=user_input,
                            command=execution_result.data.get("command", ""),
                            explanation=execution_result.data.get(
                                "explanation",
                                execution_result.data.get(
                                    "reasoning", "Processing request..."
                                ),
                            ),
                            safety_notes=execution_result.data.get("safety_notes", []),
                            confidence=execution_result.data.get("confidence"),
                            input_tokens=execution_result.data.get("input_tokens"),
                            output_tokens=execution_result.data.get("output_tokens"),
                            provider=execution_result.data.get("provider"),
                            execution_output=execution_result.data.get(
                                "execution_output", ""
                            ),
                        )
                    else:
                        # Use shell thinking mode formatter for shell commands
                        output = self.output_formatter.format_shell_thinking_mode(
                            context="Shell command generation",
                            request=user_input,
                            command=execution_result.data.get("command", ""),
                            explanation=execution_result.data.get(
                                "explanation",
                                execution_result.data.get(
                                    "reasoning", "Processing request..."
                                ),
                            ),
                            safety_notes=execution_result.data.get("safety_notes", []),
                            confidence=execution_result.data.get("confidence"),
                            input_tokens=execution_result.data.get("input_tokens"),
                            output_tokens=execution_result.data.get("output_tokens"),
                            provider=execution_result.data.get("provider"),
                            execution_output=execution_result.data.get(
                                "execution_output", ""
                            ),
                        )
                else:
                    # Use regular thinking mode formatter (for translation, etc.)
                    output = self.output_formatter.format_thinking_mode(
                        context=f"{recognition_result.function_name} to {execution_result.data.get('target_language', 'target')}",
                        request=execution_result.data.get(
                            "original_text", "user input"
                        ),
                        reasoning=execution_result.data.get(
                            "reasoning", "Processing request..."
                        ),
                        result=execution_result.data.get("translated_text", "result"),
                        confidence=execution_result.data.get("confidence"),
                        input_tokens=execution_result.data.get("input_tokens"),
                        output_tokens=execution_result.data.get("output_tokens"),
                        provider=execution_result.data.get("provider"),
                    )
            elif output_mode == OutputMode.STANDARD:
                # STANDARD mode: Result + basic metrics (no full reasoning)
                if status_display:
                    status_display.stop_loading()

                # Check if this is a shell command confirmation (don't use streaming for this)
                is_shell_confirmation = (
                    recognition_result.function_name in ["shell_command"]
                    and execution_result.data
                    and execution_result.data.get("requires_execution_confirmation")
                )

                # If streaming was used AND not a shell confirmation, let streaming handle display
                # Check if streaming actually occurred by checking if any tokens were used
                streaming_actually_used = (
                    streaming_formatter
                    and not is_shell_confirmation
                    and execution_result.data
                    and (execution_result.data.get("output_tokens", 0) > 0 or execution_result.data.get("input_tokens", 0) > 0)
                )

                if streaming_actually_used:
                    # Don't call streaming_formatter.complete() here - we'll format the result properly below
                    # The streaming formatter is only for actual token-by-token streaming

                    # Format the result content for display
                    formatted_result = self.output_mode_formatter.format_result(
                        execution_result,
                        output_mode,
                        recognition_result.function_name
                    )

                    # Create output with the actual result
                    from datetime import datetime
                    segment = OutputSegment(content=formatted_result, type=OutputType.TEXT)
                    output = FormattedOutput(
                        segments=[segment],
                        timestamp=datetime.now()
                    )
                else:
                    # No streaming OR shell confirmation - use formatter to display
                    formatted_result = self.output_mode_formatter.format_result(
                        execution_result,
                        output_mode,
                        recognition_result.function_name
                    )

                    from datetime import datetime
                    segment = OutputSegment(content=formatted_result, type=OutputType.TEXT)
                    output = FormattedOutput(
                        segments=[segment],
                        timestamp=datetime.now()
                    )
            else:
                # Default/legacy path (for streaming or functions without specific mode)
                # Clear processing indicator (only if streaming wasn't used)
                if status_display and not streaming_formatter:
                    status_display.stop_loading()

                # If streaming formatter exists but wasn't used for actual streaming,
                # just format the output normally
                if streaming_formatter:
                    # Don't call streaming_formatter.complete() - it's only for actual token streaming
                    # Just format the result content for display
                    formatted_result = self.output_mode_formatter.format_result(
                        execution_result,
                        output_mode,
                        recognition_result.function_name
                    )

                    # Create output with the actual result
                    from datetime import datetime
                    segment = OutputSegment(content=formatted_result, type=OutputType.TEXT)
                    output = FormattedOutput(
                        segments=[segment],
                        timestamp=datetime.now()
                    )
                else:
                    # Use output mode formatter for fallback
                    formatted_result = self.output_mode_formatter.format_result(
                        execution_result,
                        OutputMode.STANDARD,  # Default to standard
                        recognition_result.function_name
                    )

                    # Create output segment
                    from datetime import datetime
                    segment = OutputSegment(content=formatted_result, type=OutputType.TEXT)
                    output = FormattedOutput(
                        segments=[segment],
                        timestamp=datetime.now()
                    )

            # Only finalize session if there's no pending confirmation
            has_pending_confirmation = (
                execution_result.data and
                execution_result.data.get("requires_execution_confirmation", False)
            )

            if not has_pending_confirmation:
                # Finalize session and generate footer
                finalized_session = finalize_session()

                # Only show session summary if the output mode requests it
                if finalized_session and self.output_mode_formatter.should_show_session_summary(output_mode):
                    # THINKING mode: Use intelligent footer with LLM semantic analysis
                    # STANDARD mode: Use simple footer without LLM (saves money!)
                    if output_mode == OutputMode.THINKING and self.semantic_analyzer:
                        # Show subtle "Generating summary..." status (if available)
                        if status_display:
                            status_display.start_loading("Generating session summary...")
                        try:
                            footer = await self.footer_formatter.format_intelligent_footer(
                                finalized_session, user_input, self.verbosity_level
                            )
                        finally:
                            if status_display:
                                status_display.stop_loading()
                    else:
                        # STANDARD mode or no semantic analyzer: use simple footer
                        footer = self.footer_formatter.format_session_footer(
                            finalized_session, self.verbosity_level
                        )

                    # Calculate total wall-clock time AFTER footer generation
                    # This includes semantic analysis time
                    total_duration = time.time() - total_start_time

                    # Update footer with total duration if significantly different
                    if total_duration > finalized_session.session_duration + 0.5:
                        # Replace the timing line in the footer
                        footer = self._update_footer_with_total_time(footer, finalized_session, total_duration)
                    # Add footer to output with single blank line separator
                    output.segments.append(OutputSegment("", OutputType.TEXT))
                    output.segments.append(OutputSegment(footer, OutputType.INFO))

            return output

        except Exception as e:
            # Stop spinner on error
            if status_display:
                status_display.stop_loading()

            # Finalize session even on error
            finalized_session = finalize_session()

            # Handle unexpected errors
            error_output = self.output_formatter.format_error(
                f"Unexpected error: {str(e)}"
            )

            # Add error session footer if we have session data
            if finalized_session:
                # Use basic footer for error cases (no semantic analysis needed)
                footer = self.footer_formatter.format_session_footer(
                    finalized_session, self.verbosity_level
                )
                error_output.segments.append(OutputSegment("", OutputType.TEXT))
                error_output.segments.append(OutputSegment(footer, OutputType.ERROR))

            return error_output

    async def start_new_chat(self, title: str | None = None) -> ChatContext:
        """Start a new chat session"""
        return await self.context_manager.start_new_chat(title=title)

    async def continue_chat(self, chat_id: str) -> ChatContext:
        """Continue an existing chat session"""
        return await self.context_manager.continue_chat(chat_id)

    async def list_chat_history(
        self, limit: int = 50, archived: bool = False
    ) -> FormattedOutput:
        """List chat history"""
        chats = await self.context_manager.list_chats(limit=limit, archived=archived)

        return self.output_formatter.format_chat_history_list(chats)

    async def search_chats(
        self, query: str, search_content: bool = False, tag_filter: str | None = None
    ) -> FormattedOutput:
        """Search chat history"""
        matching_chats = await self.context_manager.search_chats(
            query=query, search_content=search_content, tag_filter=tag_filter
        )

        return self.output_formatter.format_chat_history_list(matching_chats)

    async def export_chat(self, chat_id: str, format: str = "json") -> str | None:
        """Export a chat"""
        return await self.context_manager.export_chat(chat_id, format)

    async def import_chat(self, data: str, format: str = "json") -> ChatContext | None:
        """Import a chat"""
        return await self.context_manager.import_chat(data, format)

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat"""
        return await self.context_manager.delete_chat(chat_id)

    async def archive_chat(self, chat_id: str) -> bool:
        """Archive a chat"""
        return await self.context_manager.archive_chat(chat_id)

    async def update_chat_metadata(
        self, chat_id: str, title: str | None = None, tags: list[str] | None = None
    ) -> bool:
        """Update chat metadata"""
        return await self.context_manager.update_chat_metadata(
            chat_id=chat_id, title=title, tags=tags
        )

    def register_function(self, function_plugin: Any) -> bool:
        """Register a function plugin"""
        return self.function_registry.register_plugin(function_plugin)

    def list_functions(self, category: str | None = None) -> list[dict[str, Any]]:
        """List available functions"""
        from .models import FunctionCategory

        # Convert string category to enum if provided
        category_enum = None
        if category:
            try:
                category_enum = FunctionCategory(category.lower())
            except ValueError:
                pass

        functions = self.function_registry.list_functions(category=category_enum)

        return [
            {
                "name": func.name,
                "description": func.description,
                "category": func.category.value,
                "examples": func.examples,
                "requires_web": func.requires_web,
                "requires_mcp": func.requires_mcp,
                "confirmation_required": func.confirmation_required,
            }
            for func in functions
        ]

    def get_function_help(self, function_name: str) -> str | None:
        """Get help for a specific function"""
        return self.function_registry.get_function_help(function_name)

    async def get_performance_stats(
        self, function_name: str | None = None
    ) -> dict[str, Any]:
        """Get performance statistics"""
        return await self.execution_engine.get_performance_stats(function_name)

    async def get_function_suggestions(self, user_input: str) -> list[dict[str, Any]]:
        """Get function suggestions based on input"""
        return await self.execution_engine.get_function_suggestions(user_input)

    def get_current_context(self) -> ChatContext | None:
        """Get current chat context"""
        return self.context_manager.current_session

    async def generate_help(self) -> FormattedOutput:
        """Generate comprehensive help for all available functions"""
        functions = self.function_registry.list_functions()

        if not functions:
            return self.output_formatter.format_help({"functions": []})

        # Convert function definitions to dictionary format expected by formatter
        function_data = []
        for func_def in functions:
            function_data.append(
                {
                    "name": func_def.name,
                    "description": func_def.description,
                    "category": func_def.category.value,
                }
            )

        help_data = {
            "functions": function_data,
            "categories": list({func.category.value for func in functions}),
        }

        return self.output_formatter.format_help(help_data)

    async def execute_function(
        self, function_name: str, parameters: dict[str, Any], client_type: str = "cli"
    ) -> ExecutionResult:
        """Execute a function directly by name"""
        # Create a minimal execution context
        context = ExecutionContext(
            chat_context=self.context_manager.current_session,
            user_input="",
            function_name=function_name,
            parameters=parameters,
            client_type=client_type,
            llm_provider=self.llm_provider,
            web_client=self.web_client,
            mcp_client=self.mcp_client,
            config=self.config,
            offline_mode=False,
        )

        return await self.function_registry.execute(function_name, parameters, context)

    async def confirm_and_execute(
        self,
        recognition_result: RecognitionResult,
        user_input: str,
        confirmed: bool = True,
    ) -> FormattedOutput:
        """Execute a function after user confirmation"""
        if not confirmed:
            return self.output_formatter.format_error("Operation cancelled by user")

        context = self.context_manager.current_session
        if not context:
            context = await self.context_manager.start_new_chat()

        # Setup streaming for execution
        streaming_enabled = self.config.get("streaming", {}).get("enabled", True)
        streaming_formatter = None

        if streaming_enabled and self.llm_provider:
            from ..cli.response_streaming_formatter import ResponseStreamingFormatter
            enable_markdown = self.config.get("streaming", {}).get("enable_markdown", True)
            show_cursor = self.config.get("streaming", {}).get("show_cursor", True)
            streaming_formatter = ResponseStreamingFormatter(
                enable_markdown=enable_markdown,
                show_cursor=show_cursor
            )
            self.llm_provider._streaming_callback = streaming_formatter.update

        try:
            # Execute the function
            execution_result = await self.execution_engine.execute_function(
                recognition_result=recognition_result,
                user_input=user_input,
                chat_context=context,
                config=self.config,
                llm_provider=self.llm_provider,
                web_client=self.web_client,
                mcp_client=self.mcp_client,
            )
        finally:
            if streaming_formatter:
                streaming_formatter.stop()
            if self.llm_provider and hasattr(self.llm_provider, '_streaming_callback'):
                delattr(self.llm_provider, '_streaming_callback')

        # Add to chat context
        await self.context_manager.add_message(
            context,
            "assistant",
            execution_result.message,
            {
                "function": recognition_result.function_name,
                "success": execution_result.success,
            },
        )

        # Format output
        return self.output_formatter.format_execution_result(
            execution_result.message,
            recognition_result.function_name,
            execution_result.success,
        )

    async def confirm_and_execute_last_recognition(
        self, confirmed: bool = True, status_display: Any = None
    ) -> FormattedOutput:
        """Execute the last recognition result after user confirmation"""
        if not self._last_recognition_result:
            return self.output_formatter.format_error(
                "No pending confirmation to execute"
            )

        if not confirmed:
            return self.output_formatter.format_error("Operation cancelled by user")

        # Execute the stored recognition result
        recognition_result = self._last_recognition_result
        user_input = self._last_user_input or ""
        context = self._last_context
        offline_mode = self._last_offline_mode
        output_mode_override = self._last_output_mode_override  # Restore original output mode!

        try:
            # Check if this is a shell command execution confirmation
            pending_cmd = getattr(self, "_pending_shell_command", None)
            is_shell_func = recognition_result.function_name in [
                "shell_command",
            ]

            # Check if this is a git commit execution confirmation
            pending_git_commit = getattr(self, "_pending_git_commit_message", None)
            is_git_commit_func = recognition_result.function_name == "git_commit"

            # Check if this is a git PR/branch execution confirmation
            is_git_pr_func = recognition_result.function_name == "git_pr"
            is_git_branch_func = recognition_result.function_name == "git_branch"

            if is_shell_func and pending_cmd:
                # Get the shell command plugin instance and execute the stored command
                plugin = self.function_registry.plugins.get(
                    recognition_result.function_name
                )
                if plugin and hasattr(plugin, "execute_confirmed_command"):
                    # Get the stored command from the last execution
                    command = self._pending_shell_command

                    # Create execution context for the shell command execution
                    shell_context = ExecutionContext(
                        chat_context=context,
                        user_input=user_input,
                        function_name=recognition_result.function_name,
                        parameters=recognition_result.parameters,
                        client_type=client_type,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        config=self.config or {},
                        offline_mode=offline_mode,
                    )
                    # Execute the confirmed shell command
                    execution_result = await plugin.execute_confirmed_command(
                        command, shell_context, self._pending_shell_tokens
                    )
                else:
                    execution_result = ExecutionResult(
                        success=False,
                        message="Shell command function not found",
                        function_name=recognition_result.function_name,
                    )
            elif is_git_commit_func and pending_git_commit:
                # Get the git commit plugin instance and execute the stored commit
                plugin = self.function_registry.plugins.get("git_commit")
                if plugin and hasattr(plugin, "execute_confirmed_commit"):
                    # Create execution context for the git commit execution
                    git_context = ExecutionContext(
                        chat_context=context,
                        user_input=user_input,
                        function_name=recognition_result.function_name,
                        parameters=recognition_result.parameters,
                        client_type=client_type,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        config=self.config or {},
                        offline_mode=offline_mode,
                    )
                    # Execute the confirmed git commit
                    execution_result = await plugin.execute_confirmed_commit(
                        recognition_result.parameters, git_context
                    )
                    # Clear the pending commit data
                    self._pending_git_commit_message = None
                    self._pending_git_thinking_data = None
                else:
                    execution_result = ExecutionResult(
                        success=False,
                        message="Git commit function not found",
                        function_name=recognition_result.function_name,
                    )
            elif is_git_pr_func:
                # Get the git PR plugin instance and execute the confirmed PR creation
                plugin = self.function_registry.plugins.get("git_pr")
                if plugin and hasattr(plugin, "execute_confirmed_pr"):
                    # Create execution context for the git PR execution
                    pr_context = ExecutionContext(
                        chat_context=context,
                        user_input=user_input,
                        function_name=recognition_result.function_name,
                        parameters=recognition_result.parameters,
                        client_type=client_type,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        config=self.config or {},
                        offline_mode=offline_mode,
                    )
                    # Execute the confirmed PR creation
                    execution_result = await plugin.execute_confirmed_pr(
                        recognition_result.parameters, pr_context
                    )
                else:
                    execution_result = ExecutionResult(
                        success=False,
                        message="Git PR function not found",
                        function_name=recognition_result.function_name,
                    )
            elif is_git_branch_func:
                # Get the git branch plugin instance and execute the confirmed branch creation
                plugin = self.function_registry.plugins.get("git_branch")
                if plugin and hasattr(plugin, "execute_confirmed_branch"):
                    # Create execution context for the git branch execution
                    branch_context = ExecutionContext(
                        chat_context=context,
                        user_input=user_input,
                        function_name=recognition_result.function_name,
                        parameters=recognition_result.parameters,
                        client_type=client_type,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        config=self.config or {},
                        offline_mode=offline_mode,
                    )
                    # Execute the confirmed branch creation
                    execution_result = await plugin.execute_confirmed_branch(
                        recognition_result.parameters, branch_context
                    )
                else:
                    execution_result = ExecutionResult(
                        success=False,
                        message="Git branch function not found",
                        function_name=recognition_result.function_name,
                    )
            else:
                # Setup streaming for normal execution
                streaming_enabled = self.config.get("streaming", {}).get("enabled", True)
                streaming_formatter = None

                if streaming_enabled and self.llm_provider:
                    from ..cli.response_streaming_formatter import ResponseStreamingFormatter
                    enable_markdown = self.config.get("streaming", {}).get("enable_markdown", True)
                    show_cursor = self.config.get("streaming", {}).get("show_cursor", True)
                    streaming_formatter = ResponseStreamingFormatter(
                        enable_markdown=enable_markdown,
                        show_cursor=show_cursor
                    )
                    self.llm_provider._streaming_callback = streaming_formatter.update

                try:
                    # Execute function normally
                    execution_result = await self.execution_engine.execute_function(
                        recognition_result=recognition_result,
                        user_input=user_input,
                        chat_context=context,
                        config=self.config,
                        llm_provider=self.llm_provider,
                        web_client=self.web_client,
                        mcp_client=self.mcp_client,
                        offline_mode=offline_mode,
                    )
                finally:
                    if streaming_formatter:
                        streaming_formatter.stop()
                    if self.llm_provider and hasattr(self.llm_provider, '_streaming_callback'):
                        delattr(self.llm_provider, '_streaming_callback')

            # Add assistant response to context
            if context:
                # Include executed command in the message for context preservation
                assistant_message = execution_result.message
                if (
                    execution_result.data
                    and recognition_result.function_name
                    in ["shell_command"]
                    and execution_result.data.get("command")
                ):
                    command = execution_result.data.get("command")
                    assistant_message = (
                        f"{execution_result.message}\nExecuted command: {command}"
                    )

                await self.context_manager.add_message(
                    context,
                    "assistant",
                    assistant_message,
                    {
                        "function": recognition_result.function_name,
                        "success": execution_result.success,
                        "executed_command": (
                            execution_result.data.get("command")
                            if execution_result.data
                            else None
                        ),
                    },
                )

            # Clear the stored state
            self._last_recognition_result = None
            self._last_user_input = None
            self._last_context = None
            self._last_offline_mode = False
            self._last_output_mode_override = None  # Clear output mode override too
            self._pending_shell_command = None
            self._pending_shell_tokens = None

            # Determine output mode for confirmed execution (same logic as process_input)
            # Priority: CLI flag override > config.yaml override > function default > STANDARD fallback
            if output_mode_override is not None:
                output_mode = output_mode_override
            else:
                # Check config.yaml for per-function override
                config_mode_str = None
                if self.config_manager:
                    config_mode_str = self.config_manager.get_output_mode(recognition_result.function_name)

                if config_mode_str:
                    # Convert string to OutputMode enum
                    output_mode = OutputMode(config_mode_str)
                else:
                    # Use function default
                    function_plugin = self.function_registry.plugins.get(recognition_result.function_name)
                    output_mode = function_plugin.default_output_mode if function_plugin else OutputMode.STANDARD

            # Finalize session and generate footer for confirmed execution
            # Respect output mode for session summary display
            finalized_session = finalize_session()
            footer = None

            # Only show session summary if output mode allows it
            if finalized_session and self.output_mode_formatter.should_show_session_summary(output_mode):
                # THINKING mode: Use intelligent footer with LLM semantic analysis
                # STANDARD mode: Use simple footer without LLM (saves money!)
                # CLEAN mode: No session summary at all (this branch won't execute)
                if output_mode == OutputMode.THINKING and self.semantic_analyzer:
                    footer = await self.footer_formatter.format_intelligent_footer(
                        finalized_session, user_input, self.verbosity_level
                    )
                else:
                    # STANDARD mode or no semantic analyzer
                    footer = self.footer_formatter.format_session_footer(
                        finalized_session, self.verbosity_level
                    )

            # Format output for shell commands with execution results
            if (
                recognition_result.function_name in ["shell_command"]
                and execution_result.data
                and execution_result.data.get("execution_output") is not None
            ):
                # Use the new shell execution result formatter
                execution_time_str = execution_result.data.get("execution_time")

                output = self.output_formatter.format_shell_execution_result(
                    command=execution_result.data.get("command", ""),
                    output=execution_result.data.get("execution_output", ""),
                    success=execution_result.success,
                    execution_time=execution_time_str,
                    input_tokens=execution_result.data.get("input_tokens"),
                    output_tokens=execution_result.data.get("output_tokens"),
                    output_mode=output_mode,  # Pass output mode for CLEAN formatting
                )

                # Add footer to shell execution output (only if not CLEAN mode)
                if footer:
                    output.segments.append(OutputSegment("", OutputType.TEXT))
                    output.segments.append(OutputSegment(footer, OutputType.INFO))

                return output
            else:
                # Check if this is thinking mode output (same logic as main process_input)

                if (
                    execution_result.success
                    and execution_result.data
                    and execution_result.data.get("thinking_mode")
                ):

                    # Check if this is git commit execution result (after confirmation)
                    if execution_result.data.get("commit_executed"):
                        # Use git commit thinking mode formatter for the execution result
                        output = self.output_formatter.format_git_commit_thinking_mode(
                            context=f"{recognition_result.function_name} executed",
                            git_diff=execution_result.data.get("git_diff", ""),
                            commit_message=execution_result.data.get(
                                "commit_message", ""
                            ),
                            reasoning=execution_result.data.get(
                                "reasoning", "Commit executed successfully"
                            ),
                            confidence=execution_result.data.get("confidence"),
                            input_tokens=execution_result.data.get("input_tokens"),
                            output_tokens=execution_result.data.get("output_tokens"),
                            provider=execution_result.data.get("provider"),
                        )
                        # Add footer to git commit thinking mode output
                        if footer:
                            output.segments.append(OutputSegment("", OutputType.TEXT))
                            output.segments.append(OutputSegment(footer, OutputType.INFO))
                        return output
                    elif execution_result.data.get("content_type"):
                        # Use universal thinking mode formatter for content generation
                        output = self.output_formatter.format_universal_thinking_mode(
                            context=f"{recognition_result.function_name} mode",
                            request=execution_result.data.get("request", user_input),
                            response=execution_result.data.get(
                                "response", execution_result.message
                            ),
                            reasoning=execution_result.data.get(
                                "reasoning", "Processing request..."
                            ),
                            confidence=execution_result.data.get("confidence"),
                            input_tokens=execution_result.data.get("input_tokens"),
                            output_tokens=execution_result.data.get("output_tokens"),
                            provider=execution_result.data.get("provider"),
                            content_type=execution_result.data.get("content_type"),
                        )
                        # Add footer to universal thinking mode output
                        if footer:
                            output.segments.append(OutputSegment("", OutputType.TEXT))
                            output.segments.append(OutputSegment(footer, OutputType.INFO))
                        return output

                # Format regular output
                output = self.output_formatter.format_execution_result(
                    execution_result.message,
                    recognition_result.function_name,
                    execution_result.success,
                )
                # Add footer to regular output
                if footer:
                    output.segments.append(OutputSegment("", OutputType.TEXT))
                    output.segments.append(OutputSegment(footer, OutputType.INFO))
                return output

        except Exception as e:
            # Clear the stored state on error
            self._last_recognition_result = None
            self._last_user_input = None
            self._last_context = None
            self._last_offline_mode = False
            self._pending_shell_command = None

            return self.output_formatter.format_error(f"Execution failed: {str(e)}")

    # Enhanced Context Management Methods

    async def start_conversation_session(self, session_id: str | None = None) -> str:
        """Start or continue a conversation session"""
        if not self.conversation_manager:
            raise ValueError("Conversation manager not initialized")

        if session_id:
            session = await self.conversation_manager.continue_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            return session.session_id
        else:
            exec_context = ExecutionContext(
                chat_context=None,
                user_input="",
                function_name="",
                parameters={},
                client_type="cli",  # Default to CLI for create_session
                llm_provider=self.llm_provider,
                web_client=self.web_client,
                mcp_client=self.mcp_client,
                config=self.config,
                offline_mode=False,
            )
            session = await self.conversation_manager.start_new_session(exec_context)
            return session.session_id

    async def list_conversation_sessions(self, limit: int = 10) -> FormattedOutput:
        """List recent conversation sessions"""
        if not self.conversation_manager:
            return self.output_formatter.format_error(
                "Enhanced context management not available"
            )

        sessions = await self.conversation_manager.list_recent_sessions(limit=limit)

        segments = [
            OutputSegment("🎯 Recent Conversation Sessions:", OutputType.INFO),
            OutputSegment("", OutputType.TEXT),
        ]

        if not sessions:
            segments.append(
                OutputSegment("No conversation sessions found.", OutputType.TEXT)
            )
        else:
            for session in sessions:
                session_info = (
                    f"📝 {session['title']} ({session['session_id'][:8]}...)\n"
                    f"   💬 {session['turn_count']} turns • 📅 {session['created_at'][:10]}\n"
                    f"   📋 {session['summary'][:50]}{'...' if len(session['summary']) > 50 else ''}"
                )
                segments.append(OutputSegment(session_info, OutputType.TEXT))
                segments.append(OutputSegment("", OutputType.TEXT))

        segments.append(
            OutputSegment(
                "💡 Use session ID to continue: aii --session <session_id> 'your command'",
                OutputType.SUCCESS,
            )
        )

        return FormattedOutput(segments=segments)

    async def search_conversation_history(
        self, query: str, limit: int = 5
    ) -> FormattedOutput:
        """Search conversation history"""
        if not self.conversation_manager:
            return self.output_formatter.format_error(
                "Enhanced context management not available"
            )

        results = await self.conversation_manager.search_conversations(
            query, limit=limit
        )

        segments = [
            OutputSegment(f"🔍 Search results for: '{query}'", OutputType.INFO),
            OutputSegment("", OutputType.TEXT),
        ]

        if not results:
            segments.append(
                OutputSegment("No matching conversations found.", OutputType.TEXT)
            )
        else:
            for result in results:
                result_info = (
                    f"📝 {result['title']} ({result['session_id'][:8]}...)\n"
                    f"   🎯 Match: {result['matching_input'][:80]}{'...' if len(result['matching_input']) > 80 else ''}\n"
                    f"   📅 {result['timestamp'][:10]}"
                )
                segments.append(OutputSegment(result_info, OutputType.TEXT))
                segments.append(OutputSegment("", OutputType.TEXT))

        return FormattedOutput(segments=segments)

    async def get_quick_action_suggestions(self, limit: int = 3) -> FormattedOutput:
        """Get AI-powered quick action suggestions based on conversation history"""
        if not self.conversation_manager:
            return self.output_formatter.format_error(
                "Enhanced context management not available"
            )

        suggestions = await self.conversation_manager.get_quick_action_suggestions(
            limit=limit
        )

        segments = [
            OutputSegment("💡 Quick Action Suggestions:", OutputType.INFO),
            OutputSegment("", OutputType.TEXT),
        ]

        if not suggestions:
            segments.append(
                OutputSegment(
                    "No suggestions available yet. Start a conversation to get personalized suggestions!",
                    OutputType.TEXT,
                )
            )
        else:
            for i, suggestion in enumerate(suggestions, 1):
                priority_emoji = {"high": "🔥", "medium": "⭐", "low": "💭"}.get(
                    suggestion.get("priority", "medium"), "⭐"
                )

                suggestion_text = (
                    f"{priority_emoji} {i}. {suggestion['action']}\n"
                    f"   💻 Command: `{suggestion['command']}`\n"
                    f"   🎯 Why: {suggestion['rationale']}"
                )
                segments.append(OutputSegment(suggestion_text, OutputType.TEXT))
                segments.append(OutputSegment("", OutputType.TEXT))

        segments.append(
            OutputSegment(
                "💡 Use: aii '<suggested command>' to execute", OutputType.SUCCESS
            )
        )

        return FormattedOutput(segments=segments)

    def get_conversation_context_status(self) -> dict[str, Any]:
        """Get status of conversation context management"""
        if not self.conversation_manager:
            return {"enabled": False, "reason": "Not initialized"}

        current_session = self.conversation_manager.get_current_session()
        return {
            "enabled": True,
            "current_session": {
                "id": current_session.session_id if current_session else None,
                "title": current_session.title if current_session else None,
                "turn_count": len(current_session.turns) if current_session else 0,
                "active_commands": (
                    current_session.active_commands if current_session else []
                ),
            },
        }

    def _update_footer_with_total_time(self, footer: str, session: SessionMetrics, total_duration: float) -> str:
        """Update footer to show both processing and total time"""
        import re

        # Find the timing line and replace it
        time_pattern = r"(⚡|\\[TIME\\]) Total time: ([\d.]+)s"

        # Calculate the replacement
        replacement = f"\\1 Processing: {session.session_duration:.1f}s • Total: {total_duration:.1f}s"

        updated_footer = re.sub(time_pattern, replacement, footer)
        return updated_footer

    async def cleanup(self) -> None:
        """Clean up resources and close connections"""
        await self.shutdown()

    async def _log_execution(
        self,
        chat_id: str,
        function_name: str,
        parameters: dict[str, Any],
        result: Any,
        success: bool
    ) -> None:
        """Log function execution to database for analytics (v0.4.7)"""
        try:
            # Initialize database if not already done
            await self.chat_storage.initialize()

            # Prepare execution data
            import json
            from datetime import datetime

            # Convert result to JSON-serializable format
            result_data = {}
            if hasattr(result, 'data') and result.data:
                result_data = result.data
            elif hasattr(result, '__dict__'):
                result_data = {k: v for k, v in result.__dict__.items() if not k.startswith('_')}

            # Insert execution record
            import aiosqlite
            async with aiosqlite.connect(str(self.chat_storage.db_path)) as db:
                await db.execute(
                    """
                    INSERT INTO executions (chat_id, function_name, parameters, result, timestamp, success)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chat_id,
                        function_name,
                        json.dumps(parameters),
                        json.dumps(result_data),
                        datetime.now().isoformat(),
                        success
                    )
                )
                await db.commit()

        except Exception as e:
            # Don't fail the execution if logging fails
            if DEBUG_MODE:
                print(f"⚠️ Failed to log execution: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown the engine"""
        # Save current session if exists
        if self.context_manager.current_session:
            await self.context_manager.save_chat(self.context_manager.current_session)

        # Close any external connections
        if hasattr(self.llm_provider, "close"):
            await self.llm_provider.close()

        if hasattr(self.web_client, "close"):
            await self.web_client.close()

        if hasattr(self.mcp_client, "shutdown"):
            await self.mcp_client.shutdown()
