# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Stream Handler - Token buffering and stream processing"""


import asyncio
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Optional


@dataclass
class StreamConfig:
    """Configuration for stream handling

    Attributes:
        buffer_size: Number of tokens to buffer before flushing
        flush_interval: Maximum time to wait before flushing (seconds)
        show_cursor: Whether to show typing cursor during streaming
        enable_markdown: Whether to render markdown during streaming
    """
    buffer_size: int = 10
    flush_interval: float = 0.05  # 50ms
    show_cursor: bool = True
    enable_markdown: bool = True


class StreamHandler:
    """Handle token streaming with buffering and formatting

    This handler processes streaming tokens with smart buffering to balance
    responsiveness and UI smoothness. Tokens are buffered and flushed either
    when the buffer reaches a size limit or when a time interval elapses.
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        """Initialize stream handler

        Args:
            config: Stream configuration (uses defaults if None)
        """
        self.config = config or StreamConfig()
        self.buffer: list[str] = []
        self.last_flush: float = time.time()
        self.full_response: list[str] = []

    async def process_stream(
        self,
        stream: AsyncIterator[str],
        on_token: Callable[[str], None],
        on_complete: Callable[[str], None]
    ) -> None:
        """Process token stream with buffering and callbacks

        Args:
            stream: Async iterator of tokens
            on_token: Callback for buffered tokens (called periodically)
            on_complete: Callback for complete response (called once at end)

        Raises:
            Exception: Re-raises exceptions from stream after cleanup
        """
        try:
            async for token in stream:
                # Accumulate for final response
                self.full_response.append(token)

                # Add to buffer
                self.buffer.append(token)

                # Flush if buffer full or time elapsed
                if self._should_flush():
                    await self._flush_buffer(on_token)

            # Final flush for any remaining tokens
            if self.buffer:
                await self._flush_buffer(on_token)

            # Completion callback with full response
            complete_text = "".join(self.full_response)
            on_complete(complete_text)

        except Exception as e:
            # On error, flush partial response and re-raise
            partial_text = "".join(self.full_response)
            if partial_text:
                # Call completion with partial response and error indicator
                error_msg = f"\n\n⚠️ Stream interrupted: {str(e)}"
                on_complete(partial_text + error_msg)
            raise

    async def _flush_buffer(self, on_token: Callable[[str], None]) -> None:
        """Flush buffered tokens and call callback

        Args:
            on_token: Callback to invoke with buffered text
        """
        if not self.buffer:
            return

        buffered_text = "".join(self.buffer)
        on_token(buffered_text)

        # Clear buffer and update timestamp
        self.buffer.clear()
        self.last_flush = time.time()

    def _should_flush(self) -> bool:
        """Determine if buffer should be flushed

        Returns:
            True if buffer should be flushed, False otherwise
        """
        # Check buffer size
        if len(self.buffer) >= self.config.buffer_size:
            return True

        # Check time elapsed
        current_time = time.time()
        time_elapsed = current_time - self.last_flush
        if time_elapsed >= self.config.flush_interval:
            return True

        return False

    def reset(self) -> None:
        """Reset handler state for reuse"""
        self.buffer.clear()
        self.full_response.clear()
        self.last_flush = time.time()
