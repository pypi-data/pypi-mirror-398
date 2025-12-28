# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Execution Engine - Function orchestration and workflow management"""


import time
from typing import Any, Optional

from ..context.models import ChatContext
from ..models import (
    ErrorContext,
    ExecutionContext,
    ExecutionResult,
    PerformanceMetrics,
    RecognitionResult,
)
from ..registry.function_registry import FunctionRegistry
from ..session import SessionManager, FunctionExecution
from ..cost.calculator import CostCalculator


class ExecutionEngine:
    """Orchestrates function execution with monitoring and error handling"""

    def __init__(
        self,
        function_registry: FunctionRegistry,
        cost_calculator: CostCalculator | None = None,
        execution_logger: Any = None  # ExecutionLogger (v0.9.0)
    ):
        """Initialize execution engine"""
        self.function_registry = function_registry
        self.cost_calculator = cost_calculator
        self.execution_logger = execution_logger
        self.performance_metrics: list[PerformanceMetrics] = []
        self.max_metrics_history = 1000

    async def execute_function(
        self,
        recognition_result: RecognitionResult,
        user_input: str,
        chat_context: ChatContext,
        config: dict[str, Any] | None = None,
        llm_provider: Any = None,
        web_client: Any = None,
        mcp_client: Any = None,
        offline_mode: bool = False,
        streaming_callback: Any = None,  # Optional[Callable[[str], Awaitable[None]]]
        websocket_handler: Any = None,  # v0.6.0: WebSocket handler for MCP client delegation
        client_type: str = "cli",  # v0.9.2: Track client source
    ) -> ExecutionResult:
        """Execute a function based on recognition result"""
        start_time = time.time()

        # If streaming callback provided, attach it to LLM provider for function access
        if streaming_callback and llm_provider:
            llm_provider._streaming_callback = streaming_callback

        # Create execution context
        # v0.6.2: Use intent for actual function execution, function_name for display
        actual_function_name = recognition_result.intent
        display_name = recognition_result.function_name

        context = ExecutionContext(
            chat_context=chat_context,
            user_input=user_input,
            function_name=actual_function_name,  # Use intent for execution
            parameters=recognition_result.parameters,
            client_type=client_type,  # v0.9.2: Track client source
            llm_provider=llm_provider,
            web_client=web_client,
            mcp_client=mcp_client,
            config=config or {},
            offline_mode=offline_mode,
            streaming_callback=streaming_callback,  # Pass streaming callback through
            websocket_handler=websocket_handler,  # v0.6.0: For MCP client-side execution
        )

        try:
            # Check if function exists (use intent, not display name)
            function_def = self.function_registry.get_function(actual_function_name)
            if not function_def:
                return ExecutionResult(
                    success=False,
                    message=f"Function '{display_name}' not found",  # Show display name in error
                    function_name=display_name,  # v0.6.2: Use display name in result
                )

            # Check prerequisites
            prereq_check = await self._check_prerequisites(function_def, context)
            if not prereq_check.success:
                return prereq_check

            # Execute the function (use intent, not display name)
            result = await self.function_registry.execute(
                actual_function_name, recognition_result.parameters, context
            )

            # Record performance metrics
            execution_time = time.time() - start_time
            await self._record_metrics(
                function_name=recognition_result.function_name,
                execution_time=execution_time,
                success=result.success,
                confidence=recognition_result.confidence,
            )

            # Extract token data from result (v0.5.1 fix - moved outside session block)
            # This ensures token metadata is available even in API mode (no session)
            input_tokens = 0
            output_tokens = 0
            reasoning_tokens = 0
            artifacts = []
            confidence = recognition_result.confidence

            # Add intent recognition tokens to the total
            import os
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG [Layer 3B - executor.execute_unified]: Token aggregation starting")
                print(f"🔍 DEBUG [Layer 3B]: recognition_result.intent_recognition_tokens = {getattr(recognition_result, 'intent_recognition_tokens', None)}")

            if hasattr(recognition_result, 'intent_recognition_tokens') and recognition_result.intent_recognition_tokens:
                intent_tokens = recognition_result.intent_recognition_tokens
                input_tokens += intent_tokens.get('input_tokens', 0)
                output_tokens += intent_tokens.get('output_tokens', 0)
                reasoning_tokens += intent_tokens.get('reasoning_tokens', 0)
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [Layer 3B]: Intent tokens ADDED - input={intent_tokens.get('input_tokens', 0)}, output={intent_tokens.get('output_tokens', 0)}")
            else:
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG [Layer 3B]: NO intent tokens - hasattr={hasattr(recognition_result, 'intent_recognition_tokens')}, value={getattr(recognition_result, 'intent_recognition_tokens', None)}")

            if result.data:
                # Ensure we get integer values, never None
                function_input_tokens = result.data.get('input_tokens') or 0
                function_output_tokens = result.data.get('output_tokens') or 0
                function_reasoning_tokens = result.data.get('reasoning_tokens') or 0
                confidence = result.data.get('confidence') or recognition_result.confidence

                # Add function tokens to intent recognition tokens
                input_tokens += int(function_input_tokens) if function_input_tokens is not None else 0
                output_tokens += int(function_output_tokens) if function_output_tokens is not None else 0
                reasoning_tokens += int(function_reasoning_tokens) if function_reasoning_tokens is not None else 0

                # Extract artifacts from result data
                if 'artifacts' in result.data:
                    artifacts = result.data['artifacts'] or []
                elif 'command' in result.data:
                    artifacts = [f"command:{result.data['command']}"]
                elif 'commit_hash' in result.data:
                    artifacts = [f"commit:{result.data['commit_hash']}"]

            # Calculate cost if cost calculator is available
            # SINGLE SOURCE OF TRUTH: Cost Calculation
            # This is the ONLY place where LLM costs are calculated for execution tracking
            # All downstream components (ExecutionLogger, stats functions, API endpoints) use this value
            # Never recalculate cost from tokens elsewhere - this ensures 100% consistency
            cost = 0.0
            provider_name = None
            model_name = None
            if self.cost_calculator and llm_provider:
                try:
                    # Extract provider info
                    provider_name = getattr(llm_provider, 'provider_name', 'unknown')
                    model_name = getattr(llm_provider, 'model_name', 'unknown')

                    # Calculate cost using CostCalculator (single source of truth)
                    cost_breakdown = self.cost_calculator.calculate_cost(
                        provider=provider_name,
                        model=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        reasoning_tokens=reasoning_tokens
                    )
                    cost = cost_breakdown.total_cost
                except Exception as e:
                    # Silently ignore cost calculation errors (optional feature)
                    cost = 0.0

            # Store aggregated token data back in result for API response (v0.5.1 fix)
            # This ensures REST and WebSocket APIs can access token metadata
            if not result.data:
                result.data = {}

            # v0.6.0: ALWAYS add token data (even if 0) because unified endpoint uses LLM for intent recognition
            # Intent recognition tokens should always be present, even if function execution bypasses LLM
            result.data['input_tokens'] = input_tokens
            result.data['output_tokens'] = output_tokens
            if reasoning_tokens > 0:
                result.data['reasoning_tokens'] = reasoning_tokens

            # v0.6.0: Always add cost (even if 0) for consistent session summary display
            # Store cost in result.data for downstream consumption (ExecutionLogger, stats, API)
            # This is the authoritative cost value - downstream components must never recalculate
            result.data['cost'] = cost

            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG [Layer 3B - executor.execute_unified]: FINAL token aggregation complete")
                print(f"🔍 DEBUG [Layer 3B]: result.data['input_tokens'] = {result.data.get('input_tokens')}")
                print(f"🔍 DEBUG [Layer 3B]: result.data['output_tokens'] = {result.data.get('output_tokens')}")
                print(f"🔍 DEBUG [Layer 3B]: result.data['cost'] = {result.data.get('cost')}")

            # Add model info
            if model_name:
                result.data['model'] = model_name

            # Add function execution to global session (if available)
            session = SessionManager.get_current_session()
            if session:
                # Create function execution record
                function_execution = FunctionExecution(
                    function_name=recognition_result.function_name,
                    start_time=start_time,
                    end_time=time.time(),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    reasoning_tokens=reasoning_tokens,
                    success=result.success,
                    confidence=confidence,
                    artifacts=artifacts or [],
                    cost=cost,
                    provider=provider_name,
                    model=model_name
                )

                # Add to session
                session.add_function_execution(function_execution)

            # Log execution to database (v0.9.0 - non-blocking)
            if self.execution_logger:
                try:
                    await self.execution_logger.log_execution(
                        result=result,
                        context=context,
                        execution_time_ms=int(execution_time * 1000),
                        ttft_ms=None,  # TODO: Track TTFT in streaming callback
                        client_type=context.client_type  # v0.9.2: Track client source
                    )
                except Exception as e:
                    # Don't crash on logging errors
                    import logging
                    logging.getLogger(__name__).error(f"Failed to log execution: {e}")

            result.execution_time = execution_time
            return result

        except Exception as e:
            # Handle execution errors
            execution_time = time.time() - start_time
            await self._record_metrics(
                function_name=recognition_result.function_name,
                execution_time=execution_time,
                success=False,
                confidence=recognition_result.confidence,
            )

            # Add failed function execution to global session
            session = SessionManager.get_current_session()
            if session:
                function_execution = FunctionExecution(
                    function_name=recognition_result.function_name,
                    start_time=start_time,
                    end_time=time.time(),
                    input_tokens=0,
                    output_tokens=0,
                    reasoning_tokens=0,
                    success=False,
                    confidence=recognition_result.confidence or 0.0,
                    artifacts=[]
                )
                session.add_function_execution(function_execution)

            # Create error result for logging
            error_result = ExecutionResult(
                success=False,
                message=str(e),
                function_name=recognition_result.function_name,
                data={
                    "error_code": type(e).__name__,
                    "error_message": str(e),
                }
            )

            # Log failed execution to database (v0.9.0 - non-blocking)
            if self.execution_logger:
                try:
                    await self.execution_logger.log_execution(
                        result=error_result,
                        context=context,
                        execution_time_ms=int(execution_time * 1000),
                        ttft_ms=None,
                        client_type=context.client_type  # v0.9.2: Track client source
                    )
                except Exception as log_err:
                    # Don't crash on logging errors
                    import logging
                    logging.getLogger(__name__).error(f"Failed to log execution: {log_err}")

            # Create error context for detailed error handling
            error_context = ErrorContext(
                function_name=recognition_result.function_name,
                user_input=user_input,
                error_type=type(e).__name__,
                error_message=str(e),
                context={
                    "parameters": recognition_result.parameters,
                    "confidence": recognition_result.confidence,
                },
            )

            return await self._handle_execution_error(error_context)

    async def execute_pipeline(
        self,
        pipeline_steps: list[dict[str, Any]],
        user_input: str,
        chat_context: ChatContext,
        **kwargs,
    ) -> list[ExecutionResult]:
        """Execute a pipeline of multiple functions"""
        results = []
        current_context = chat_context

        for i, step in enumerate(pipeline_steps):
            try:
                # Create recognition result for this step
                recognition_result = RecognitionResult(
                    intent=step.get("intent", "unknown"),
                    confidence=step.get("confidence", 1.0),
                    parameters=step.get("parameters", {}),
                    function_name=step.get("function_name", "unknown"),
                )

                # Execute step
                result = await self.execute_function(
                    recognition_result=recognition_result,
                    user_input=f"Pipeline step {i + 1}: {step.get('description', 'No description')}",
                    chat_context=current_context,
                    **kwargs,
                )

                results.append(result)

                # If step failed and is marked as critical, abort pipeline
                if not result.success and step.get("critical", True):
                    break

                # Update context with result data for next step
                if result.data:
                    current_context.add_assistant_message(
                        f"Pipeline step {i + 1} completed: {result.message}",
                        {"step_result": result.data},
                    )

            except Exception as e:
                error_result = ExecutionResult(
                    success=False,
                    message=f"Pipeline step {i + 1} failed: {str(e)}",
                    function_name=step.get("function_name", "unknown"),
                )
                results.append(error_result)

                # Abort on error if step is critical
                if step.get("critical", True):
                    break

        return results

    async def get_function_suggestions(
        self, user_input: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get function suggestions based on input"""
        suggestions = []

        # Get all functions and score them
        all_functions = self.function_registry.list_functions()
        scored_functions = []

        for func_def in all_functions:
            score = self._calculate_relevance_score(user_input, func_def)
            if score > 0:
                scored_functions.append((score, func_def))

        # Sort by score and return top suggestions
        scored_functions.sort(key=lambda x: x[0], reverse=True)

        for score, func_def in scored_functions[:limit]:
            suggestions.append(
                {
                    "name": func_def.name,
                    "description": func_def.description,
                    "category": func_def.category.value,
                    "relevance_score": score,
                    "examples": func_def.examples[:2],  # Limit examples
                }
            )

        return suggestions

    async def get_performance_stats(
        self, function_name: str | None = None
    ) -> dict[str, Any]:
        """Get performance statistics"""
        metrics = self.performance_metrics

        if function_name:
            metrics = [m for m in metrics if m.function_name == function_name]

        if not metrics:
            return {"error": "No metrics available"}

        total_calls = len(metrics)
        successful_calls = sum(1 for m in metrics if m.success)
        total_time = sum(m.execution_time for m in metrics)
        avg_time = total_time / total_calls if total_calls > 0 else 0
        avg_confidence = (
            sum(m.confidence for m in metrics) / total_calls if total_calls > 0 else 0
        )

        return {
            "function_name": function_name or "all",
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0,
            "average_execution_time": avg_time,
            "average_confidence": avg_confidence,
            "total_execution_time": total_time,
        }

    # Private helper methods

    async def _check_prerequisites(
        self, function_def: Any, context: ExecutionContext
    ) -> ExecutionResult:
        """Check if function prerequisites are met"""
        # Check web access requirement
        if (
            function_def.requires_web
            and not context.web_client
            and not context.offline_mode
        ):
            return ExecutionResult(
                success=False,
                message="This function requires web access, but web client is not available",
                function_name=function_def.name,
            )

        # Check MCP requirement
        if function_def.requires_mcp and not context.mcp_client:
            return ExecutionResult(
                success=False,
                message="This function requires MCP connection, but MCP client is not available",
                function_name=function_def.name,
            )

        # Check file access requirement
        if function_def.requires_files:
            # This would typically check file permissions, disk space, etc.
            pass

        return ExecutionResult(
            success=True, message="Prerequisites met", function_name=function_def.name
        )

    async def _record_metrics(
        self,
        function_name: str,
        execution_time: float,
        success: bool,
        confidence: float,
    ) -> None:
        """Record performance metrics"""
        metric = PerformanceMetrics(
            function_name=function_name,
            execution_time=execution_time,
            success=success,
            confidence=confidence,
        )

        self.performance_metrics.append(metric)

        # Maintain metrics history limit
        if len(self.performance_metrics) > self.max_metrics_history:
            # Remove oldest metrics
            self.performance_metrics = self.performance_metrics[
                -self.max_metrics_history :
            ]

    async def _handle_execution_error(
        self, error_context: ErrorContext
    ) -> ExecutionResult:
        """Handle execution errors with appropriate recovery strategies"""
        error_message = f"Execution failed: {error_context.error_message}"
        recovery_suggestions = []

        # Provide specific error recovery suggestions
        if "network" in error_context.error_message.lower():
            recovery_suggestions.append("Check your internet connection and try again")
            recovery_suggestions.append("Use --offline mode for local operations")

        elif "permission" in error_context.error_message.lower():
            recovery_suggestions.append("Check file permissions")
            recovery_suggestions.append("Try running with appropriate privileges")

        elif "not found" in error_context.error_message.lower():
            recovery_suggestions.append("Verify the file or resource exists")
            recovery_suggestions.append("Check the path and spelling")

        elif "api" in error_context.error_message.lower():
            recovery_suggestions.append("Check your API key configuration")
            recovery_suggestions.append("Verify API service availability")

        if recovery_suggestions:
            error_message += "\\n\\nSuggestions:\\n" + "\\n".join(
                f"- {s}" for s in recovery_suggestions
            )

        return ExecutionResult(
            success=False,
            message=error_message,
            function_name=error_context.function_name,
            data={"error_context": error_context.__dict__},
        )

    def _calculate_relevance_score(self, user_input: str, function_def: Any) -> float:
        """Calculate how relevant a function is to user input"""
        score = 0.0
        user_input_lower = user_input.lower()

        # Check function name match
        if function_def.name.lower() in user_input_lower:
            score += 0.4

        # Check description keywords
        description_words = function_def.description.lower().split()
        matching_words = sum(
            1 for word in description_words if word in user_input_lower
        )
        if matching_words > 0:
            score += 0.3 * (matching_words / len(description_words))

        # Check category relevance
        if function_def.category.value.lower() in user_input_lower:
            score += 0.2

        # Check tags
        tag_matches = sum(
            1 for tag in function_def.tags if tag.lower() in user_input_lower
        )
        if tag_matches > 0:
            score += 0.1 * tag_matches

        return min(1.0, score)
