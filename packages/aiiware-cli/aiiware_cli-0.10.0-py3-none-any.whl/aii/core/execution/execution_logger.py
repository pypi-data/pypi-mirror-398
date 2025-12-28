# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""ExecutionLogger - Non-blocking async execution logging with <5ms overhead"""


import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..models import ExecutionContext, ExecutionResult, FunctionCategory


logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for a single execution"""

    execution_id: str
    timestamp: datetime
    function_name: str
    function_category: str | None
    model: str | None
    provider: str | None
    success: bool
    error_code: str | None
    error_message: str | None
    time_to_first_token_ms: int | None
    total_execution_time_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    chat_id: str | None
    session_id: str | None
    user_id: str | None
    client_type: str  # "cli", "vscode", "chrome", or "api"
    parameters: dict[str, Any]
    result: dict[str, Any]


class ExecutionLogger:
    """
    Non-blocking async execution logger with <5ms overhead.

    Features:
    - Async queue for pending writes (non-blocking)
    - Background writer task with batching
    - <5ms overhead for log_execution() call
    - Automatic cost calculation
    - Graceful error handling (logs but doesn't crash)
    """

    def __init__(self, storage, batch_size: int = 10, batch_timeout_ms: int = 100):
        """
        Initialize execution logger.

        Args:
            storage: ChatStorage instance for database writes
            batch_size: Number of executions to batch before writing (default: 10)
            batch_timeout_ms: Max time to wait before writing batch (default: 100ms)
        """
        self.storage = storage
        self.batch_size = batch_size
        self.batch_timeout_ms = batch_timeout_ms / 1000.0  # Convert to seconds

        self._queue: asyncio.Queue[ExecutionMetrics] = asyncio.Queue()
        self._writer_task: asyncio.Task | None = None
        self._running = False
        self._pending_batch: list[ExecutionMetrics] = []
        self._last_write_time = time.time()

    async def start(self) -> None:
        """Start background writer task"""
        if self._running:
            logger.warning("ExecutionLogger already running")
            return

        self._running = True
        self._writer_task = asyncio.create_task(self._write_loop())
        logger.info("ExecutionLogger started")

    async def stop(self) -> None:
        """Stop background writer and flush pending writes"""
        if not self._running:
            return

        self._running = False

        # Flush remaining items
        await self._flush_pending()

        # Cancel writer task
        if self._writer_task:
            self._writer_task.cancel()
            try:
                await self._writer_task
            except asyncio.CancelledError:
                pass

        logger.info("ExecutionLogger stopped")

    async def log_execution(
        self,
        result: ExecutionResult,
        context: ExecutionContext,
        execution_time_ms: int,
        ttft_ms: int | None = None,
        client_type: str = "cli",
    ) -> None:
        """
        Queue execution for async write (non-blocking, <5ms).

        Args:
            result: Execution result
            context: Execution context
            execution_time_ms: Total execution time in milliseconds
            ttft_ms: Time to first token in milliseconds (optional)
            client_type: Client interface type ("cli", "vscode", "chrome", "api")
        """
        start = time.perf_counter()

        try:
            # Build metrics
            metrics = self._build_metrics(
                result, context, execution_time_ms, ttft_ms, client_type
            )

            # Queue for async write (non-blocking)
            await self._queue.put(metrics)

            # Measure overhead
            overhead_ms = (time.perf_counter() - start) * 1000
            if overhead_ms > 5:
                logger.warning(
                    f"ExecutionLogger overhead {overhead_ms:.2f}ms exceeds 5ms target"
                )

        except Exception as e:
            # Don't crash on logging errors
            logger.error(f"Error queueing execution log: {e}")

    def _build_metrics(
        self,
        result: ExecutionResult,
        context: ExecutionContext,
        execution_time_ms: int,
        ttft_ms: int | None,
        client_type: str = "cli",
    ) -> ExecutionMetrics:
        """
        Build execution metrics from result and context.

        Args:
            result: Execution result
            context: Execution context
            execution_time_ms: Total execution time
            ttft_ms: Time to first token
            client_type: Client interface type

        Returns:
            ExecutionMetrics object
        """
        # Generate execution ID
        execution_id = str(uuid.uuid4())

        # Extract model and provider info
        model = None
        provider = None
        if context.llm_provider:
            raw_model = getattr(context.llm_provider, "model", None)
            provider = getattr(context.llm_provider, "provider_name", None)

            # Strip provider prefix if present (e.g., "openai:gpt-4o-mini" -> "gpt-4o-mini")
            # This ensures consistent model names in the database
            if raw_model and ":" in raw_model:
                model = raw_model.split(":")[-1]
            else:
                model = raw_model

        # Extract token counts and cost from result data
        # SINGLE SOURCE OF TRUTH: Cost Tracking
        # Cost is ALWAYS calculated by executor.py using CostCalculator
        # We NEVER recalculate here - this maintains consistency across all clients
        input_tokens = 0
        output_tokens = 0
        cost_usd = 0.0

        if result.data:
            input_tokens = result.data.get("input_tokens", 0)
            output_tokens = result.data.get("output_tokens", 0)

            # Single source of truth: cost from executor's CostCalculator
            # If cost is missing, it's a bug in the function implementation
            if "cost" in result.data:
                cost_usd = result.data["cost"]
            elif input_tokens > 0 or output_tokens > 0:
                # Cost missing but tokens present - this is a bug
                logger.error(
                    f"Cost data missing from execution result. "
                    f"This indicates a bug - all functions must provide cost data. "
                    f"Function: {context.function_name or 'unknown'}, Model: {model or 'unknown'}, "
                    f"Tokens: {input_tokens} in / {output_tokens} out"
                )
                # Use 0.0 for now (graceful degradation)
                cost_usd = 0.0

        # Extract function category
        function_category = None
        if hasattr(context, "function_category"):
            function_category = context.function_category
        elif context.config:
            function_category = context.config.get("category")

        # Extract error info
        error_code = None
        error_message = None
        if not result.success and result.data:
            error_code = result.data.get("error_code")
            error_message = result.data.get("error_message", result.message)

        # Extract chat/session info
        chat_id = None
        if context.chat_context:
            chat_id = getattr(context.chat_context, "chat_id", None)

        session_id = context.config.get("session_id") if context.config else None
        user_id = context.config.get("user_id") if context.config else None

        return ExecutionMetrics(
            execution_id=execution_id,
            timestamp=datetime.now(),
            function_name=context.function_name,
            function_category=function_category,
            model=model,
            provider=provider,
            success=result.success,
            error_code=error_code,
            error_message=error_message,
            time_to_first_token_ms=ttft_ms,
            total_execution_time_ms=execution_time_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            chat_id=chat_id,
            session_id=session_id,
            user_id=user_id,
            client_type=client_type,
            parameters=context.parameters,
            result=result.data or {},
        )

    async def _write_loop(self) -> None:
        """
        Background task: batch writes every 100ms or 10 items.

        Runs continuously while logger is active, processing queued executions
        and writing them to database in batches for efficiency.
        """
        logger.debug("ExecutionLogger write loop started")

        while self._running:
            try:
                # Wait for item or timeout
                try:
                    metrics = await asyncio.wait_for(
                        self._queue.get(), timeout=self.batch_timeout_ms
                    )
                    self._pending_batch.append(metrics)
                except asyncio.TimeoutError:
                    # Timeout - write pending batch if any
                    if self._pending_batch:
                        await self._write_batch()
                    continue

                # Check if batch is full or timeout exceeded
                time_since_last_write = time.time() - self._last_write_time
                if (
                    len(self._pending_batch) >= self.batch_size
                    or time_since_last_write >= self.batch_timeout_ms
                ):
                    await self._write_batch()

            except Exception as e:
                logger.error(f"Error in ExecutionLogger write loop: {e}")
                # Continue running despite errors

        # Final flush on shutdown
        if self._pending_batch:
            await self._write_batch()

        logger.debug("ExecutionLogger write loop stopped")

    async def _write_batch(self) -> None:
        """Write pending batch to database"""
        if not self._pending_batch:
            return

        try:
            # Convert metrics to dict format for storage
            executions = [
                {
                    "execution_id": m.execution_id,
                    "timestamp": m.timestamp.isoformat(),
                    "function_name": m.function_name,
                    "function_category": m.function_category,
                    "model": m.model,
                    "provider": m.provider,
                    "success": m.success,
                    "error_code": m.error_code,
                    "error_message": m.error_message,
                    "time_to_first_token_ms": m.time_to_first_token_ms,
                    "total_execution_time_ms": m.total_execution_time_ms,
                    "input_tokens": m.input_tokens,
                    "output_tokens": m.output_tokens,
                    "cost_usd": m.cost_usd,
                    "chat_id": m.chat_id,
                    "session_id": m.session_id,
                    "user_id": m.user_id,
                    "client_type": m.client_type,
                    "parameters": m.parameters,
                    "result": m.result,
                }
                for m in self._pending_batch
            ]

            # Write batch to database
            result = await self.storage.log_executions_batch(executions)
            logger.debug(
                f"Wrote batch of {result['success']} executions "
                f"({result['failed']} failed)"
            )

            # Clear batch
            self._pending_batch.clear()
            self._last_write_time = time.time()

        except Exception as e:
            logger.error(f"Error writing execution batch: {e}")
            # Clear batch to avoid retrying forever
            self._pending_batch.clear()

    async def _flush_pending(self) -> None:
        """Flush all pending writes"""
        # Process remaining queue items
        while not self._queue.empty():
            try:
                metrics = self._queue.get_nowait()
                self._pending_batch.append(metrics)
            except asyncio.QueueEmpty:
                break

        # Write final batch
        if self._pending_batch:
            await self._write_batch()

    async def get_stats(self) -> dict[str, Any]:
        """
        Get logger statistics.

        Returns:
            Dict with queue size, pending batch size, running status
        """
        return {
            "running": self._running,
            "queue_size": self._queue.qsize(),
            "pending_batch_size": len(self._pending_batch),
            "batch_size": self.batch_size,
            "batch_timeout_ms": self.batch_timeout_ms * 1000,
        }
