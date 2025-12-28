# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
MCP Streaming Adapter - Progressive display for MCP tool results

Adapts MCP tool responses (which are complete) to streaming format
for better UX. Provides token-by-token display similar to LLM responses.

Challenge: MCP tools return complete responses, not token streams.
Solution: Intelligently chunk responses and simulate streaming.
"""


import asyncio
import json
import logging
import re
from typing import Any, AsyncIterator, Dict, List, Optional

from .response_streaming_formatter import ResponseStreamingFormatter

logger = logging.getLogger(__name__)


class MCPStreamingAdapter:
    """
    Adapts MCP tool results to streaming format.

    Features:
    - Smart chunking (sentence-aware for text)
    - Progressive JSON display (show items as they're "processed")
    - Progress indicators for lists
    - Natural typing delays
    """

    def __init__(self, response_streaming_formatter: ResponseStreamingFormatter):
        """
        Initialize streaming adapter.

        Args:
            response_streaming_formatter: The formatter to stream to
        """
        self.formatter = response_streaming_formatter
        self.chunk_delay = 0.01  # 10ms between chunks (natural typing speed)

    async def stream_tool_result(
        self,
        tool_result: Any,
        tool_name: str,
        success: bool = True,
    ) -> None:
        """
        Stream MCP tool result progressively.

        Args:
            tool_result: The MCP tool result (complete)
            tool_name: Name of the tool
            success: Whether the tool execution succeeded
        """
        # Extract text content from tool result
        result_text = self._extract_text(tool_result)

        if not result_text:
            # No content to stream
            self.formatter.complete(
                final_text="(no output)",
                function_name=tool_name,
                success=success,
            )
            return

        # Determine content type and stream accordingly
        if self._is_json(result_text):
            await self._stream_json(result_text)
        elif self._is_list(result_text):
            await self._stream_list(result_text)
        else:
            await self._stream_text(result_text)

        # Complete streaming
        self.formatter.complete(
            final_text=result_text,
            function_name=f"mcp:{tool_name}",
            success=success,
        )

    def _extract_text(self, tool_result: Any) -> str:
        """
        Extract text content from MCP tool result.

        Args:
            tool_result: MCP tool result (various formats)

        Returns:
            Text content as string
        """
        if isinstance(tool_result, str):
            return tool_result

        if isinstance(tool_result, dict):
            # Try common keys
            for key in ["content", "text", "result", "output", "data"]:
                if key in tool_result:
                    value = tool_result[key]
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, (dict, list)):
                        return json.dumps(value, indent=2)

            # If content is a list of objects (MCP format)
            if "content" in tool_result and isinstance(tool_result["content"], list):
                contents = []
                for item in tool_result["content"]:
                    if isinstance(item, dict) and "text" in item:
                        contents.append(item["text"])
                    elif isinstance(item, str):
                        contents.append(item)
                return "\n".join(contents)

            # Fallback: stringify entire dict
            return json.dumps(tool_result, indent=2)

        # Fallback: convert to string
        return str(tool_result)

    def _is_json(self, text: str) -> bool:
        """Check if text is valid JSON"""
        text_stripped = text.strip()
        if not text_stripped:
            return False

        if text_stripped.startswith(("{", "[")):
            try:
                json.loads(text_stripped)
                return True
            except json.JSONDecodeError:
                return False

        return False

    def _is_list(self, text: str) -> bool:
        """
        Check if text is a list (line-by-line format).

        Examples:
        - "1. Item one\n2. Item two"
        - "- Item one\n- Item two"
        - Multiple lines with similar structure
        """
        lines = text.strip().split("\n")

        if len(lines) < 3:
            return False

        # Check for numbered lists
        numbered_pattern = re.compile(r"^\s*\d+[.)]\s+")
        numbered_count = sum(1 for line in lines if numbered_pattern.match(line))
        if numbered_count > len(lines) * 0.6:  # 60% threshold
            return True

        # Check for bullet lists
        bullet_pattern = re.compile(r"^\s*[-•*]\s+")
        bullet_count = sum(1 for line in lines if bullet_pattern.match(line))
        if bullet_count > len(lines) * 0.6:
            return True

        return False

    async def _stream_json(self, json_text: str) -> None:
        """
        Stream JSON with smart formatting.

        Args:
            json_text: JSON string
        """
        try:
            data = json.loads(json_text)

            # For lists, show progressive counts
            if isinstance(data, list):
                await self._stream_json_list(data)

            # For objects, show key-by-key
            elif isinstance(data, dict):
                await self._stream_json_dict(data)

        except json.JSONDecodeError:
            # Fallback to text streaming
            await self._stream_text(json_text)

    async def _stream_json_list(self, data_list: List[Any]) -> None:
        """Stream JSON list with progress indicators"""
        total = len(data_list)

        # Show header
        header = f"📊 Processing {total} item{'s' if total != 1 else ''}...\n\n"
        self.formatter.update(header)
        await asyncio.sleep(self.chunk_delay * 5)  # Brief pause

        # Stream items
        for i, item in enumerate(data_list, 1):
            # Format item
            if isinstance(item, dict):
                item_str = self._format_dict_compact(item)
            else:
                item_str = str(item)

            # Show item with index
            line = f"{i}. {item_str}\n"
            self.formatter.update(line)
            await asyncio.sleep(self.chunk_delay * 2)

            # Progress marker every 5 items
            if i % 5 == 0 and i < total:
                progress = f"   ({i}/{total} items processed)\n"
                self.formatter.update(progress)
                await asyncio.sleep(self.chunk_delay * 3)

    async def _stream_json_dict(self, data_dict: Dict[str, Any]) -> None:
        """Stream JSON dict key-by-key"""
        for key, value in data_dict.items():
            # Format value
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)

            # Show key-value pair
            line = f"**{key}**: {value_str}\n"
            self.formatter.update(line)
            await asyncio.sleep(self.chunk_delay * 2)

    def _format_dict_compact(self, d: Dict[str, Any], max_length: int = 80) -> str:
        """Format dict compactly for list display"""
        if not d:
            return "{}"

        # Try to extract meaningful fields
        if "name" in d:
            return d["name"]
        elif "title" in d:
            return d["title"]
        elif "id" in d:
            return f"ID: {d['id']}"

        # Fallback: show first key-value pair
        first_key = next(iter(d))
        first_value = d[first_key]
        result = f"{first_key}: {first_value}"

        if len(result) > max_length:
            result = result[:max_length - 3] + "..."

        return result

    async def _stream_list(self, list_text: str) -> None:
        """
        Stream list items progressively.

        Args:
            list_text: Multi-line list text
        """
        lines = list_text.strip().split("\n")
        total = len(lines)

        for i, line in enumerate(lines, 1):
            self.formatter.update(f"{line}\n")
            await asyncio.sleep(self.chunk_delay)

            # Show progress every 10 lines
            if i % 10 == 0 and i < total:
                progress = f"   [{i}/{total} items...]\n"
                self.formatter.update(progress)
                await asyncio.sleep(self.chunk_delay * 3)

    async def _stream_text(self, text: str) -> None:
        """
        Stream plain text with smart chunking.

        Args:
            text: Plain text to stream
        """
        # Split into sentences for natural pacing
        sentences = self._split_sentences(text)

        for sentence in sentences:
            # Stream sentence word-by-word for very natural feel
            words = sentence.split()

            for word in words:
                self.formatter.update(f"{word} ")
                await asyncio.sleep(self.chunk_delay)

            # Brief pause at sentence end
            await asyncio.sleep(self.chunk_delay * 2)

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Simple sentence splitter (handles . ! ?)
        # More sophisticated than just split('.') to handle abbreviations
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s'
        sentences = re.split(pattern, text)

        # Clean up
        sentences = [s.strip() for s in sentences if s.strip()]

        # If no sentences found (no punctuation), split by newlines
        if len(sentences) <= 1 and "\n" in text:
            sentences = [line.strip() for line in text.split("\n") if line.strip()]

        # Fallback: treat entire text as one sentence
        if not sentences:
            sentences = [text]

        return sentences


class ProgressiveIndicator:
    """
    Shows progress for long-running MCP operations.

    Features:
    - Elapsed time tracking
    - Rate-limited updates (no spam)
    - Unicode progress indicators
    """

    def __init__(self, operation: str):
        """
        Initialize progress indicator.

        Args:
            operation: Description of operation (e.g., "Searching GitHub")
        """
        self.operation = operation
        self.start_time = None
        self.last_update = 0
        self.min_update_interval = 0.5  # Update at most every 500ms

    def start(self) -> None:
        """Start progress tracking"""
        import time
        self.start_time = time.time()
        self.last_update = self.start_time
        self._show_progress()

    def update(self, status: Optional[str] = None) -> None:
        """
        Show progress update.

        Args:
            status: Optional status message
        """
        if self.start_time is None:
            self.start()
            return

        import time
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Rate limit updates
        if current_time - self.last_update < self.min_update_interval:
            return

        self._show_progress(status, elapsed)
        self.last_update = current_time

    def _show_progress(self, status: Optional[str] = None, elapsed: Optional[float] = None) -> None:
        """Display progress line"""
        if elapsed is not None:
            time_str = f"({elapsed:.1f}s)"
        else:
            time_str = ""

        if status:
            print(f"\r🔍 {self.operation}... {status} {time_str}", end="", flush=True)
        else:
            print(f"\r🔍 {self.operation}... {time_str}", end="", flush=True)

    def complete(self, final_status: str) -> None:
        """
        Show completion status.

        Args:
            final_status: Final status message
        """
        import time

        if self.start_time:
            elapsed = time.time() - self.start_time
            time_str = f"({elapsed:.1f}s)"
        else:
            time_str = ""

        # Clear line and show completion
        print(f"\r✓ {final_status} {time_str}          ")
