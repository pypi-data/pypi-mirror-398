# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Interactive Shell - Interactive chat mode for continuous conversations"""


import asyncio
import readline  # Enable command history with arrow keys
from typing import TYPE_CHECKING

from ..core.context.models import ChatContext
from ..core.session import SessionManager

if TYPE_CHECKING:
    from ..core.engine import AIIEngine
from .output_formatter import OutputFormatter, OutputSegment, OutputType
from .status_display import StatusDisplay


class InteractiveShell:
    """Interactive shell for continuous chat sessions"""

    def __init__(self, engine: "AIIEngine", formatter: OutputFormatter):
        self.engine = engine
        self.formatter = formatter
        self.status_display = StatusDisplay(use_emojis=formatter.use_emojis)
        self.current_context: ChatContext | None = None
        self.running = False

        # Cumulative session tracking for interactive mode
        self.session_start_time: float | None = None
        self.cumulative_input_tokens: int = 0
        self.cumulative_output_tokens: int = 0
        self.cumulative_cost: float = 0.0
        self.function_execution_count: int = 0
        self.processed_session_ids: set[str] = set()  # Track which sessions we've counted

        # Configure readline for command history
        self._setup_readline()

    async def start(self, chat_id: str | None = None) -> None:
        """Start interactive shell session"""
        self.running = True

        # Initialize session tracking
        import time

        self.session_start_time = time.time()

        # Display welcome message
        self._display_welcome()

        try:
            # Load or create chat context
            if chat_id:
                self.current_context = await self.engine.continue_chat(chat_id)
                self.formatter.display_segments(
                    [
                        OutputSegment(
                            f"🤖 Resuming chat: {self.current_context.title}",
                            OutputType.INFO,
                        ),
                        OutputSegment(
                            f'   Last message: "{self._get_last_user_message()}"',
                            OutputType.INFO,
                        ),
                        OutputSegment("   Continue? (y/n): ", OutputType.INFO),
                    ]
                )

                if not await self._get_confirmation():
                    self.current_context = await self.engine.start_new_chat()
            else:
                self.current_context = await self.engine.start_new_chat()

            # Main interaction loop
            while self.running:
                try:
                    user_input = await self._get_user_input()

                    if not user_input:
                        continue

                    # Handle special commands
                    if await self._handle_special_commands(user_input):
                        continue

                    # Show loading status
                    self.status_display.start_loading(
                        "Processing your request...", "spinner"
                    )

                    try:
                        # Process user input through engine
                        result = await self.engine.process_input(
                            user_input,
                            context=self.current_context,
                            status_display=self.status_display,  # Pass status_display for spinner control
                            client_type="cli"  # v0.9.2: Track CLI usage
                        )

                        # Stop loading animation (only if streaming didn't stop it already)
                        self.status_display.stop_loading()

                        # Display result
                        if result:
                            self.formatter.display(result)

                        # Accumulate statistics from the last finalized session
                        # The session is finalized inside process_input, so we need to get it from history
                        session_history = SessionManager.get_session_history(limit=1)
                        if session_history:
                            last_session = session_history[0]

                            # Only count this session if we haven't processed it before
                            if last_session.session_id not in self.processed_session_ids:
                                self.cumulative_input_tokens += last_session.total_input_tokens
                                self.cumulative_output_tokens += last_session.total_output_tokens
                                self.cumulative_cost += last_session.total_cost
                                self.function_execution_count += len(last_session.function_executions)
                                self.processed_session_ids.add(last_session.session_id)

                    except Exception:
                        # Make sure to stop loading on error
                        self.status_display.stop_loading()
                        raise

                except KeyboardInterrupt:
                    self._display_interrupt_message()
                    break
                except EOFError:
                    break
                except Exception as e:
                    error_output = self.formatter.format_error(
                        f"Unexpected error: {str(e)}"
                    )
                    self.formatter.display(error_output)

        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop interactive shell"""
        self.running = False

    def _display_welcome(self) -> None:
        """Display welcome message"""
        welcome_segments = [
            OutputSegment(
                "🤖 Entering interactive mode. Type '/help' or 'help' for commands, '/exit' to quit.",
                OutputType.INFO,
            ),
            OutputSegment("", OutputType.TEXT),  # Empty line
        ]
        self.formatter.display_segments(welcome_segments)

    def _setup_readline(self) -> None:
        """Configure readline for command history and editing"""
        try:
            # Set history file location
            import os
            from pathlib import Path

            history_file = Path.home() / ".aii" / ".aii_history"
            history_file.parent.mkdir(parents=True, exist_ok=True)

            # Load existing history
            if history_file.exists():
                readline.read_history_file(str(history_file))

            # Configure history
            readline.set_history_length(1000)  # Keep last 1000 commands

            # Store history file path for saving later
            self.history_file = history_file

            # Enable tab completion (optional, for future enhancement)
            # readline.parse_and_bind("tab: complete")

        except Exception:
            # Readline might not be available on all platforms (e.g., Windows without pyreadline)
            self.history_file = None

    async def _get_user_input(self) -> str:
        """Get input from user with prompt and command history"""
        loop = asyncio.get_event_loop()
        user_input = await loop.run_in_executor(None, input, "> ")

        # Save history after each command
        if self.history_file and user_input.strip():
            try:
                readline.write_history_file(str(self.history_file))
            except Exception:
                pass  # Silently ignore history save errors

        return user_input

    async def _get_confirmation(self) -> bool:
        """Get yes/no confirmation from user"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, input)
        return response.lower().strip() in ("y", "yes")

    async def _handle_special_commands(self, user_input: str) -> bool:
        """Handle special interactive commands"""
        command = user_input.strip().lower()

        # Support both with and without "/" prefix
        if command.startswith("/"):
            command = command[1:]

        if command == "exit":
            await self._handle_exit()
            return True

        elif command == "help":
            self._display_help()
            return True

        elif command == "clear":
            self._clear_screen()
            return True

        elif command == "history":
            await self._display_current_chat_history()
            return True

        elif command == "context":
            self._display_context_info()
            return True

        elif command == "stats":
            self._display_session_stats()
            return True

        elif command == "init":
            await self._handle_init_command()
            return True

        elif command.startswith("save"):
            await self._handle_save_command(command)
            return True

        elif command.startswith("load"):
            await self._handle_load_command(command)
            return True

        return False

    async def _handle_exit(self) -> None:
        """Handle exit command"""
        if self.current_context and len(self.current_context.messages) > 1:
            self.formatter.display_segments(
                [OutputSegment("Save current chat? (y/n): ", OutputType.INFO)]
            )

            if await self._get_confirmation():
                # Save chat with a meaningful title if not already set
                if (
                    not self.current_context.title
                    or self.current_context.title.startswith("Chat")
                ):
                    title = await self._generate_chat_title()
                    self.current_context.title = title

                await self.engine.context_manager.save_chat(self.current_context)

                self.formatter.display_segments(
                    [
                        OutputSegment(
                            f"✓ Chat saved as: {self.current_context.title}",
                            OutputType.SUCCESS,
                        )
                    ]
                )

        self.formatter.display_segments(
            [OutputSegment("👋 Goodbye! Thanks for using AII.", OutputType.INFO)]
        )
        self.running = False

    def _display_help(self) -> None:
        """Display help for interactive commands"""
        help_segments = [
            OutputSegment("Interactive Commands (use with or without / prefix):", OutputType.INFO),
            OutputSegment("  /help        - Show this help message", OutputType.TEXT),
            OutputSegment("  /exit        - Exit interactive mode", OutputType.TEXT),
            OutputSegment("  /clear       - Clear screen", OutputType.TEXT),
            OutputSegment(
                "  /history     - Show current chat history", OutputType.TEXT
            ),
            OutputSegment(
                "  /context     - Show current chat context info", OutputType.TEXT
            ),
            OutputSegment(
                "  /stats       - Show session statistics (tokens, messages, duration)", OutputType.TEXT
            ),
            OutputSegment(
                "  /init        - Run setup wizard (first-time configuration)", OutputType.TEXT
            ),
            OutputSegment(
                "  /save [name] - Save current chat with optional name", OutputType.TEXT
            ),
            OutputSegment("  /load <id>   - Load chat by ID", OutputType.TEXT),
            OutputSegment("", OutputType.TEXT),  # Empty line
            OutputSegment(
                "You can also use any regular AII commands:", OutputType.INFO
            ),
            OutputSegment('  translate "hello" --to spanish', OutputType.TEXT),
            OutputSegment("  commit (generate git commit message)", OutputType.TEXT),
            OutputSegment('  explain "complex concept"', OutputType.TEXT),
            OutputSegment("", OutputType.TEXT),  # Empty line
        ]
        self.formatter.display_segments(help_segments)

    def _clear_screen(self) -> None:
        """Clear the screen"""
        import os

        os.system("cls" if os.name == "nt" else "clear")

    async def _display_current_chat_history(self) -> None:
        """Display current chat history"""
        if not self.current_context or not self.current_context.messages:
            self.formatter.display_segments(
                [OutputSegment("No messages in current chat.", OutputType.INFO)]
            )
            return

        history_segments = [
            OutputSegment(
                f"Current Chat: {self.current_context.title}", OutputType.INFO
            ),
            OutputSegment(
                f"Messages: {len(self.current_context.messages)}", OutputType.INFO
            ),
            OutputSegment("", OutputType.TEXT),  # Empty line
        ]

        # Show last few messages
        recent_messages = self.current_context.messages[-5:]  # Last 5 messages
        for message in recent_messages:
            role_indicator = "👤" if message.role == "user" else "🤖"
            content_preview = (
                message.content[:100] + "..."
                if len(message.content) > 100
                else message.content
            )

            history_segments.append(
                OutputSegment(
                    f"{role_indicator} {message.role}: {content_preview}",
                    OutputType.TEXT,
                )
            )

        if len(self.current_context.messages) > 5:
            history_segments.append(
                OutputSegment(
                    f"... and {len(self.current_context.messages) - 5} more messages",
                    OutputType.INFO,
                )
            )

        history_segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        self.formatter.display_segments(history_segments)

    def _display_context_info(self) -> None:
        """Display current context information"""
        if not self.current_context:
            self.formatter.display_segments(
                [OutputSegment("No active chat context.", OutputType.INFO)]
            )
            return

        info_segments = [
            OutputSegment("Current Context Info:", OutputType.INFO),
            OutputSegment(
                f"  Chat ID: {self.current_context.chat_id}", OutputType.TEXT
            ),
            OutputSegment(f"  Title: {self.current_context.title}", OutputType.TEXT),
            OutputSegment(
                f"  Messages: {len(self.current_context.messages)}", OutputType.TEXT
            ),
            OutputSegment(
                f"  Created: {self.current_context.created_at}", OutputType.TEXT
            ),
            OutputSegment(
                f"  Updated: {self.current_context.updated_at}", OutputType.TEXT
            ),
        ]

        if self.current_context.tags:
            info_segments.append(
                OutputSegment(
                    f"  Tags: {', '.join(self.current_context.tags)}", OutputType.TEXT
                )
            )

        info_segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        self.formatter.display_segments(info_segments)

    def _display_session_stats(self) -> None:
        """Display cumulative session statistics for interactive mode"""
        import time

        stats_segments = [
            OutputSegment("Session Statistics:", OutputType.INFO),
            OutputSegment("", OutputType.TEXT),  # Empty line
        ]

        # Session duration
        if self.session_start_time:
            duration_seconds = time.time() - self.session_start_time
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)

            if hours > 0:
                duration_str = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                duration_str = f"{minutes}m {seconds}s"
            else:
                duration_str = f"{seconds}s"

            stats_segments.append(
                OutputSegment(f"  Session Duration: {duration_str}", OutputType.TEXT)
            )

        # Use cumulative statistics tracked across all commands
        total_tokens = self.cumulative_input_tokens + self.cumulative_output_tokens

        # Function execution count
        stats_segments.append(
            OutputSegment(
                f"  Functions Executed: {self.function_execution_count}",
                OutputType.TEXT,
            )
        )

        # Token usage
        stats_segments.append(
            OutputSegment(
                f"  Total Tokens: {total_tokens:,} (Input: {self.cumulative_input_tokens:,}, Output: {self.cumulative_output_tokens:,})",
                OutputType.TEXT,
            )
        )

        # Cost (from actual cost calculator)
        if self.cumulative_cost > 0:
            stats_segments.append(
                OutputSegment(
                    f"  Total Cost: ${self.cumulative_cost:.6f}",
                    OutputType.TEXT,
                )
            )

        # Chat context info
        if self.current_context:
            stats_segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
            stats_segments.append(
                OutputSegment(
                    f"  Current Chat: {self.current_context.title}", OutputType.TEXT
                )
            )
            stats_segments.append(
                OutputSegment(
                    f"  Chat Messages: {len(self.current_context.messages)}",
                    OutputType.TEXT,
                )
            )

        stats_segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        self.formatter.display_segments(stats_segments)

    async def _handle_init_command(self) -> None:
        """Handle /init command - run setup wizard"""
        from aii.cli.setup import SetupWizard

        print()  # Blank line before wizard
        wizard = SetupWizard()
        success = await wizard.run()

        if success:
            # Wizard completed successfully
            # User can continue using interactive mode
            print()  # Blank line after wizard
        else:
            # Wizard was cancelled or failed
            # Don't exit interactive mode, let user continue
            pass

    async def _handle_save_command(self, command: str) -> None:
        """Handle save command"""
        parts = command.split(maxsplit=1)
        custom_name = parts[1] if len(parts) > 1 else None

        if not self.current_context:
            self.formatter.display_segments(
                [OutputSegment("No active chat to save.", OutputType.WARNING)]
            )
            return

        if custom_name:
            self.current_context.title = custom_name

        await self.engine.context_manager.save_chat(self.current_context)

        self.formatter.display_segments(
            [
                OutputSegment(
                    f"✓ Chat saved as: {self.current_context.title}", OutputType.SUCCESS
                )
            ]
        )

    async def _handle_load_command(self, command: str) -> None:
        """Handle load command"""
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            self.formatter.display_segments(
                [OutputSegment("Usage: load <chat_id>", OutputType.WARNING)]
            )
            return

        chat_id = parts[1]
        try:
            self.current_context = await self.engine.continue_chat(chat_id)
            self.formatter.display_segments(
                [
                    OutputSegment(
                        f"✓ Loaded chat: {self.current_context.title}",
                        OutputType.SUCCESS,
                    )
                ]
            )
        except Exception as e:
            error_output = self.formatter.format_error(
                f"Failed to load chat {chat_id}: {str(e)}"
            )
            self.formatter.display(error_output)

    def _get_last_user_message(self) -> str:
        """Get the last user message from current context"""
        if not self.current_context or not self.current_context.messages:
            return "No previous messages"

        user_messages = [
            msg for msg in self.current_context.messages if msg.role == "user"
        ]

        if user_messages:
            last_msg = user_messages[-1].content
            return last_msg[:50] + "..." if len(last_msg) > 50 else last_msg

        return "No user messages found"

    async def _generate_chat_title(self) -> str:
        """Generate a meaningful title for the current chat"""
        if not self.current_context or not self.current_context.messages:
            return f"Chat {self.current_context.chat_id[:8]}"

        # Get first user message for title generation
        user_messages = [
            msg for msg in self.current_context.messages if msg.role == "user"
        ]

        if user_messages:
            first_message = user_messages[0].content
            # Simple title generation - take first few words
            words = first_message.split()[:4]
            title = " ".join(words)
            if len(first_message) > 50:
                title += "..."
            return title

        return f"Chat {self.current_context.chat_id[:8]}"

    def _display_interrupt_message(self) -> None:
        """Display message when user interrupts with Ctrl+C"""
        self.formatter.display_segments(
            [
                OutputSegment(
                    "\\n⚠️  Interrupted. Type 'exit' to quit or continue chatting.",
                    OutputType.WARNING,
                )
            ]
        )

    async def _cleanup(self) -> None:
        """Cleanup resources when shell stops"""
        # Save current context if needed
        if self.current_context and hasattr(self.engine, "context_manager"):
            try:
                await self.engine.context_manager.save_chat(self.current_context)
            except Exception:
                pass  # Ignore save errors during cleanup
