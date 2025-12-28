# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Interactive Chat Mode (v0.6.0 - Conversation-style like Claude.ai)"""


import asyncio
import readline  # Enable command history with arrow keys
import sys
import time
from typing import Any, List, Dict

from .client import AiiCLIClient
from ..config.manager import ConfigManager


class InteractiveChatSession:
    """
    WebSocket-based interactive chat with conversation context.

    Mimics Claude.ai/ChatGPT/Gemini behavior:
    - Maintains conversation history across turns
    - Each message includes full context
    - Supports multi-turn conversations
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.client = AiiCLIClient(config_manager)
        self.running = False

        # Conversation history (like Claude.ai)
        self.conversation_history: List[Dict[str, str]] = []
        # Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

        # Session tracking
        self.session_start_time: float | None = None
        self.total_requests: int = 0
        self.cumulative_tokens: int = 0
        self.cumulative_cost: float = 0.0

        # Setup readline for command history
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Configure readline for command history and editing"""
        try:
            from pathlib import Path

            history_file = Path.home() / ".aii" / ".aii_history"
            history_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing history
            if history_file.exists():
                readline.read_history_file(str(history_file))

            # Configure history
            readline.set_history_length(1000)
            self.history_file = history_file
        except Exception:
            self.history_file = None

    async def start(self) -> int:
        """Start interactive chat session"""
        self.running = True
        self.session_start_time = time.time()

        # Display welcome message
        self._display_welcome()

        try:
            # Main interaction loop
            while self.running:
                try:
                    # Get user input
                    user_input = await self._get_user_input()

                    if not user_input.strip():
                        continue

                    # Handle special commands
                    if await self._handle_special_commands(user_input):
                        continue

                    # Add user message to conversation
                    self.conversation_history.append({
                        "role": "user",
                        "content": user_input
                    })

                    # Process request with full conversation context
                    await self._process_with_context(user_input)

                except KeyboardInterrupt:
                    print("\n⚠️  Interrupted. Type 'exit' to quit or continue chatting.")
                    continue
                except EOFError:
                    print()  # Newline after Ctrl+D
                    break
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
                    # Don't add failed message to history
                    if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                        self.conversation_history.pop()  # Remove last user message on error
                    continue

        finally:
            await self._cleanup()

        return 0

    def _display_welcome(self) -> None:
        """Display welcome message"""
        print("🤖 Entering interactive mode.")
        print()
        print("Controls:")
        print("  • Enter       - New line (multi-line input)")
        print("  • Empty line  - Send message")
        print("  • Ctrl+D      - Send message")
        print("  • /exit       - Quit chat")
        print("  • /help       - Show all commands")
        print()

    async def _get_user_input(self) -> str:
        """
        Get multi-line input from user.

        Controls:
        - Enter: New line
        - Empty line + Enter: Send message
        - Ctrl+D: Send message
        - Ctrl+C: Cancel current input
        """
        loop = asyncio.get_event_loop()

        try:
            lines = []

            # First line with "> " prompt
            first_line = await loop.run_in_executor(None, input, "> ")

            # If first line is a command, return immediately
            if first_line.strip().startswith('/'):
                return first_line.strip()

            lines.append(first_line)

            # If first line is not empty, allow multi-line input
            if first_line.strip():
                while True:
                    try:
                        # Continuation lines with "  " prompt
                        line = await loop.run_in_executor(None, input, "  ")

                        # Empty line = send message
                        if not line.strip():
                            break

                        lines.append(line)

                    except EOFError:
                        # Ctrl+D = send message
                        break

            user_input = "\n".join(lines).strip()

            # Save to history
            if self.history_file and user_input:
                try:
                    readline.write_history_file(str(self.history_file))
                except Exception:
                    pass

            return user_input

        except (EOFError, KeyboardInterrupt):
            raise

    async def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special interactive commands. Returns True if handled."""
        command = user_input.strip().lower()

        # Support both with and without "/" prefix
        if command.startswith("/"):
            command = command[1:]

        if command == "exit" or command == "quit":
            await self._handle_exit()
            return True

        elif command == "help":
            self._display_help()
            return True

        elif command == "clear" or command == "new":
            self._clear_conversation()
            return True

        elif command == "history":
            self._display_conversation_history()
            return True

        elif command == "stats":
            self._display_stats()
            return True

        elif command == "version":
            self._display_version()
            return True

        return False

    async def _process_with_context(self, user_input: str) -> None:
        """
        Process user request with full conversation context.

        v0.6.0: Pure chat mode - bypasses intent recognition entirely.
        Directly calls LLM with conversation history.
        """
        try:
            # Track request
            self.total_requests += 1

            # Show animated spinner
            from .spinner import Spinner
            spinner = Spinner("", stream=sys.stdout)  # Empty message, just show spinner
            await spinner.start()

            # v0.6.0: Direct LLM call with conversation history (no intent recognition)
            assistant_response, was_streamed, metadata = await self._direct_llm_chat(user_input, spinner)

            # Ensure spinner is stopped
            await spinner.stop(clear=True)

            # Display response (if not already shown via streaming)
            if assistant_response:
                # Only print if response was NOT streamed
                # Streaming responses are already printed token-by-token in _direct_llm_chat
                if not was_streamed:
                    print(assistant_response)
                    print()  # Blank line after non-streamed response

                # Display execution summary
                self._display_execution_summary(metadata)

                # Add to conversation history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_response
                })
            else:
                print()  # Blank line even if no response

        except Exception as e:
            print(f"\n❌ Error processing request: {str(e)}\n")
            # Remove user message from history on error
            if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                self.conversation_history.pop()

    async def _direct_llm_chat(self, user_input: str, spinner: Any) -> tuple[str, bool, dict]:
        """
        Chat via Aii Server using 'universal_generate' function with conversation history.

        v0.6.0 Architecture (2025-10-22) - Matching Aii VSCode Implementation:
        Sends conversation history to server via universal_generate function.
        This is the same approach used in aii-vscode/src/ui/chatViewProvider.ts:406-410.

        Why this approach:
        1. Uses Aii Server for consistency (all LLM calls through server)
        2. Uses universal_generate function (can handle any type of request)
        3. Passes conversation_history parameter (enables multi-turn conversations)
        4. Matches VSCode implementation (consistent architecture across products)
        """
        try:
            # Build conversation history for server (exclude current user message)
            conversation_hist = []
            if len(self.conversation_history) > 1:
                # Send last 10 messages (20 total including user/assistant pairs)
                recent_history = self.conversation_history[-21:-1]
                for msg in recent_history:
                    conversation_hist.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })

            # Call universal_generate function directly via WebSocket
            # This matches aii-vscode implementation exactly
            from .websocket_client import create_websocket_client

            # Ensure WebSocket client is connected
            if not self.client.ws_client or not self.client.ws_client.is_connected():
                self.client.ws_client = create_websocket_client(
                    self.client.api_url,
                    self.client.api_key,
                    self.client.mcp_client
                )
                await self.client.ws_client.connect()

            # Track if loading cleared
            loading_cleared = [False]

            def on_token_callback(token: str):
                """Print token and clear loading on first token"""
                if not loading_cleared[0]:
                    import sys
                    if spinner:
                        spinner.stop_sync(clear=True)
                    sys.stdout.write('\r')  # Clear loading indicator
                    sys.stdout.flush()
                    loading_cleared[0] = True

                # Print token immediately
                print(token, end='', flush=True)

            # Send WebSocket message with function and parameters
            request = {
                "function": "universal_generate",
                "params": {
                    "request": user_input,
                    "conversation_history": conversation_hist
                },
                "output_mode": "CLEAN"
            }

            result = await self.client.ws_client.execute_request(
                request,
                on_token=on_token_callback
            )

            # Stop spinner if still running
            if spinner and not loading_cleared[0]:
                await spinner.stop(clear=True)

            # Extract response and metadata
            if result.get("success"):
                data = result.get("data", {})
                response = data.get("clean_output") or data.get("response") or data.get("result") or ""
                metadata = result.get("metadata", {})

                # If tokens were streamed, response was already printed
                # Just return it for history storage along with streaming flag and metadata
                if loading_cleared[0]:
                    print()  # New line after streaming
                    return response, True, metadata  # (response, was_streamed=True, metadata)
                else:
                    # No streaming occurred - return for printing in caller
                    return response, False, metadata  # (response, was_streamed=False, metadata)
            else:
                error_msg = result.get("error", "Unknown error")
                raise RuntimeError(f"Chat failed: {error_msg}")

        except Exception as e:
            await spinner.stop(clear=True)
            raise RuntimeError(f"Chat error: {str(e)}") from e

    def _clear_conversation(self) -> None:
        """Clear conversation history and start fresh"""
        self.conversation_history = []
        print("🆕 Conversation cleared! Starting fresh.")
        print()

    def _display_execution_summary(self, metadata: dict) -> None:
        """
        Display execution summary after each response.

        Format: ✓ <function> • ⚡ Total time: X.Xs • 🔢 Tokens: XXX↗ YYY↘ (ZZZ total) • 💰 $X.XXXX • 🤖 <model>

        Args:
            metadata: Execution metadata from server (tokens, cost, time, model, etc.)
        """
        if not metadata:
            return

        # Extract metadata fields
        function_name = metadata.get("function_name", "chat")
        execution_time = metadata.get("execution_time", 0.0)
        tokens = metadata.get("tokens", {})
        cost = metadata.get("cost", 0.0)
        model = metadata.get("model", "unknown")

        # Extract token counts
        input_tokens = tokens.get("input", 0) if isinstance(tokens, dict) else 0
        output_tokens = tokens.get("output", 0) if isinstance(tokens, dict) else 0
        total_tokens = input_tokens + output_tokens

        # Update session cumulative stats
        self.cumulative_tokens += total_tokens
        self.cumulative_cost += cost

        # Format execution summary
        summary_parts = [
            f"✓ {function_name}",
            f"⚡ Total time: {execution_time:.1f}s",
            f"🔢 Tokens: {input_tokens}↗ {output_tokens}↘ ({total_tokens} total)",
            f"💰 ${cost:.6f}",
            f"🤖 {model}"
        ]

        # Print with blank line before for spacing
        print()
        print(" • ".join(summary_parts))
        print()

    def _display_conversation_history(self) -> None:
        """Display full conversation history"""
        if not self.conversation_history:
            print("\n💬 No conversation history yet\n")
            return

        print("\n💬 Conversation History:")
        print("─" * 60)
        for i, msg in enumerate(self.conversation_history, 1):
            role = "You" if msg["role"] == "user" else "Aii"
            content = msg["content"]
            # Truncate long messages for display
            if len(content) > 150:
                content = content[:150] + "..."
            print(f"{i}. {role}: {content}")
        print("─" * 60)
        print()

    async def _handle_exit(self) -> None:
        """Handle exit command"""
        duration = time.time() - self.session_start_time if self.session_start_time else 0

        if self.total_requests > 0:
            print(f"\n📊 Session Summary:")
            print(f"   • Messages: {len(self.conversation_history)}")
            print(f"   • Requests: {self.total_requests}")
            print(f"   • Total Tokens: {self.cumulative_tokens:,}")
            if self.cumulative_cost > 0:
                print(f"   • Total Cost: ${self.cumulative_cost:.6f}")

            minutes = int(duration // 60)
            seconds = int(duration % 60)
            if minutes > 0:
                print(f"   • Duration: {minutes}m {seconds}s")
            else:
                print(f"   • Duration: {seconds}s")
            print()

        print("👋 Goodbye!")
        self.running = False

    def _display_help(self) -> None:
        """Display help for interactive commands"""
        print("\n📖 Interactive Chat Commands:")
        print("   /help          - Show this help message")
        print("   /exit, /quit   - Exit chat mode")
        print("   /clear, /new   - Clear conversation and start fresh")
        print("   /history       - Show conversation history")
        print("   /stats         - Show session statistics")
        print("   /version       - Show Aii version")
        print()
        print("💡 How it works:")
        print("   • Chat naturally - context is preserved across messages")
        print("   • Ask follow-up questions without repeating context")
        print("   • Just like Claude.ai, ChatGPT, or Gemini")
        print()
        print("💡 Examples:")
        print('   You: What is Python?')
        print('   Aii: Python is a programming language...')
        print('   You: Show me an example')
        print('   Aii: [Aii knows you mean Python example]')
        print()

    def _display_stats(self) -> None:
        """Display session statistics"""
        duration = time.time() - self.session_start_time if self.session_start_time else 0

        print("\n📊 Session Statistics:")
        print(f"   • Messages: {len(self.conversation_history)}")
        print(f"   • Requests: {self.total_requests}")
        print(f"   • Total Tokens: {self.cumulative_tokens:,}")

        if self.cumulative_cost > 0:
            print(f"   • Total Cost: ${self.cumulative_cost:.6f}")

        minutes = int(duration // 60)
        seconds = int(duration % 60)
        if minutes > 0:
            print(f"   • Duration: {minutes}m {seconds}s")
        else:
            print(f"   • Duration: {seconds}s")
        print()

    def _display_version(self) -> None:
        """Display Aii version"""
        try:
            from importlib.metadata import version
            aii_version = version("aiiware-cli")
            print(f"\n🤖 Aii CLI v{aii_version}")
        except Exception:
            print("\n🤖 Aii CLI v0.6.0")
        print()

    async def _cleanup(self) -> None:
        """Cleanup resources"""
        # Save conversation history if needed (future feature)
        # For now, just close WebSocket connection
        try:
            if hasattr(self.client, 'disconnect'):
                await self.client.disconnect()
        except Exception:
            pass
