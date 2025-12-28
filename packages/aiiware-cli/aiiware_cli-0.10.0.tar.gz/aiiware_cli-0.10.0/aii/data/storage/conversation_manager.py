# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Enhanced Context Management with Pydantic AI Conversation History"""


import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from ...core.models import ExecutionContext

# Note: Using basic conversation tracking without pydantic_ai messages for now
from ..providers.llm_provider import LLMProvider


class ConversationTurn(BaseModel):
    """Single turn in a conversation"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    user_input: str
    ai_response: str
    command_executed: str | None = None
    execution_result: str | None = None
    context_used: dict[str, Any] = Field(default_factory=dict)
    tokens_consumed: dict[str, int] = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """A conversation session with context"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    title: str = ""  # Generated from first interaction
    turns: list[ConversationTurn] = Field(default_factory=list)
    context_summary: str = ""  # AI-generated summary of conversation
    active_commands: list[str] = Field(default_factory=list)  # Recently used commands
    working_directory: str = ""
    environment_info: dict[str, Any] = Field(default_factory=dict)


class ConversationManager:
    """Manages conversation history and context using Pydantic AI"""

    # Configuration constants for session management
    MAX_TURNS_IN_MEMORY = 100  # Maximum turns to keep in memory before archiving
    MAX_TURNS_IN_ACTIVE_SESSION = 200  # Maximum turns before forcing archival
    TURN_DATA_SIZE_LIMIT = 1_000_000  # 1MB limit for turns_data JSON blob

    def __init__(self, storage_path: Path, llm_provider: LLMProvider | None = None):
        self.storage_path = storage_path
        self.db_path = storage_path / "conversations.db"
        self.llm_provider = llm_provider
        self._current_session: ConversationSession | None = None
        self._context_agent: Agent | None = None
        self._archived_turn_count = 0  # Track archived turns for current session

        # Initialize database
        self._init_database()

        # Initialize Pydantic AI agent for context understanding
        if llm_provider and hasattr(llm_provider, "_model"):
            self._context_agent = Agent(
                model=llm_provider._model,
                system_prompt=(
                    "You are an AI assistant that helps understand conversational context. "
                    "Your job is to:\n"
                    "1. Identify when users refer to previous commands or results\n"
                    "2. Extract contextual references like 'the largest file', 'second one', 'that command'\n"
                    "3. Generate concise summaries of conversation context\n"
                    "4. Suggest follow-up actions based on conversation history\n"
                    "5. Identify safety risks when users reference previous dangerous operations\n\n"
                    "Always be precise and helpful in understanding user intent."
                ),
            )

    def _init_database(self):
        """Initialize SQLite database for conversation storage"""
        self.storage_path.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    updated_at TEXT,
                    title TEXT,
                    context_summary TEXT,
                    active_commands TEXT,
                    working_directory TEXT,
                    environment_info TEXT,
                    turns_data TEXT,
                    is_archived BOOLEAN DEFAULT 0,
                    total_turn_count INTEGER DEFAULT 0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS conversation_turns (
                    turn_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    timestamp TEXT,
                    user_input TEXT,
                    ai_response TEXT,
                    command_executed TEXT,
                    execution_result TEXT,
                    context_used TEXT,
                    tokens_consumed TEXT,
                    is_archived BOOLEAN DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES conversations (session_id)
                )
            """
            )

            # Create index for faster archived turn queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_turns_session_archived
                ON conversation_turns(session_id, is_archived)
            """
            )

            # Create index for timestamp-based queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_turns_timestamp
                ON conversation_turns(session_id, timestamp)
            """
            )

    async def start_new_session(
        self, context: ExecutionContext = None
    ) -> ConversationSession:
        """Start a new conversation session"""
        session = ConversationSession(
            working_directory=str(Path.cwd()),
            environment_info={
                "platform": "macos",
                "shell": "bash",
                "timestamp": datetime.now().isoformat(),
            },
        )

        self._current_session = session
        await self._save_session(session)
        return session

    async def continue_session(self, session_id: str) -> ConversationSession | None:
        """Continue an existing conversation session"""
        session = await self._load_session(session_id)
        if session:
            self._current_session = session
            session.updated_at = datetime.now()
            await self._save_session(session)
        return session

    async def add_turn(
        self,
        user_input: str,
        ai_response: str,
        command_executed: str | None = None,
        execution_result: str | None = None,
        tokens_consumed: dict[str, int] | None = None,
    ) -> ConversationTurn:
        """Add a new turn to the current session with automatic archival for large conversations"""
        if not self._current_session:
            raise ValueError("No active session. Start a new session first.")

        # Extract context from previous turns for this input
        context_used = await self._extract_contextual_info(user_input)

        turn = ConversationTurn(
            user_input=user_input,
            ai_response=ai_response,
            command_executed=command_executed,
            execution_result=execution_result,
            context_used=context_used,
            tokens_consumed=tokens_consumed or {},
        )

        self._current_session.turns.append(turn)
        self._current_session.updated_at = datetime.now()

        # Update active commands
        if command_executed:
            self._current_session.active_commands.append(command_executed)
            # Keep only last 5 commands
            self._current_session.active_commands = (
                self._current_session.active_commands[-5:]
            )

        # Generate title for first turn
        if len(self._current_session.turns) == 1 and not self._current_session.title:
            self._current_session.title = await self._generate_session_title(user_input)

        # Update context summary periodically
        if len(self._current_session.turns) % 3 == 0:  # Every 3 turns
            self._current_session.context_summary = (
                await self._generate_context_summary()
            )

        # Check if we need to archive old turns to prevent memory/storage issues
        total_turns = len(self._current_session.turns) + self._archived_turn_count

        if len(self._current_session.turns) >= self.MAX_TURNS_IN_MEMORY:
            # Archive older turns, keep recent ones in memory
            await self._archive_old_turns()
        elif total_turns >= self.MAX_TURNS_IN_ACTIVE_SESSION:
            # Session is getting too large, warn user
            print(
                f"⚠️  Warning: Session has {total_turns} turns. "
                "Consider starting a new session for better performance."
            )

        # Check if turns_data size is approaching limit
        try:
            turns_json = json.dumps(
                [t.model_dump(mode="json") for t in self._current_session.turns]
            )
            if len(turns_json) > self.TURN_DATA_SIZE_LIMIT:
                # Force archival due to size
                await self._archive_old_turns(keep_recent=50)
        except Exception:
            # If serialization fails, try archiving to reduce size
            await self._archive_old_turns(keep_recent=50)

        await self._save_session(self._current_session)
        return turn

    async def get_contextual_understanding(self, user_input: str) -> dict[str, Any]:
        """Analyze user input for contextual references and safety concerns"""
        if not self._current_session or not self._context_agent:
            return {
                "contextual_references": [],
                "needs_history": False,
                "safety_warnings": [],
            }

        try:
            # Build conversation history for context
            history_context = self._build_history_context()

            # Check for dangerous command patterns
            safety_analysis = self._analyze_safety_concerns(user_input, history_context)

            prompt = f"""
            Analyze this user input for contextual references to previous conversation:

            User Input: "{user_input}"

            Recent Conversation History:
            {history_context}

            Safety Analysis: {safety_analysis}

            IMPORTANT: Pay special attention to LOCATION CONTEXT. If the user says "second largest", "next one", etc., they likely mean in the SAME LOCATION as the previous command.

            Please identify:
            1. Any references to previous commands, files, or results
            2. Implicit context (like "the largest", "that file", "second one")
            3. Whether this input requires conversation history to understand
            4. Any safety concerns if this relates to previous dangerous operations
            5. If user is referencing previous file operations, what specific files/directories/locations
            6. LOCATION INHERITANCE: If previous command used ~/Downloads, ~/Documents, etc., should this command use the same location?

            Respond with JSON containing:
            - contextual_references: list of specific references found
            - needs_history: boolean indicating if history is needed
            - safety_warnings: list of any safety concerns with specific warnings
            - suggested_context: string with relevant context to include
            - referenced_files: list of files/directories that may be referenced
            - inferred_location: the directory/path that should be used based on context (e.g., "~/Downloads")
            - location_inherited: boolean indicating if location should be inherited from previous command
            - risk_level: "low", "medium", or "high" based on potential danger
            """

            result = await self._context_agent.run(prompt)

            try:
                parsed_result = json.loads(result.output)
                # Merge with safety analysis
                parsed_result["safety_warnings"].extend(
                    safety_analysis.get("warnings", [])
                )
                parsed_result["risk_level"] = max(
                    parsed_result.get("risk_level", "low"),
                    safety_analysis.get("risk_level", "low"),
                    key=lambda x: {"low": 0, "medium": 1, "high": 2}[x],
                )
                return parsed_result
            except json.JSONDecodeError:
                contextual_info = await self._extract_contextual_info(user_input)
                return {
                    "contextual_references": self._simple_context_detection(user_input),
                    "needs_history": any(
                        word in user_input.lower()
                        for word in [
                            "previous",
                            "last",
                            "that",
                            "it",
                            "them",
                            "second",
                            "third",
                            "again",
                        ]
                    ),
                    "safety_warnings": safety_analysis.get("warnings", []),
                    "suggested_context": "",
                    "referenced_files": [],
                    "inferred_location": contextual_info.get("inferred_location", ""),
                    "location_inherited": bool(
                        contextual_info.get("inferred_location")
                    ),
                    "risk_level": safety_analysis.get("risk_level", "low"),
                }

        except Exception:
            # Fallback context detection with safety analysis and location inference
            safety_analysis = self._analyze_safety_concerns(user_input, "")
            contextual_info = await self._extract_contextual_info(user_input)

            return {
                "contextual_references": self._simple_context_detection(user_input),
                "needs_history": any(
                    word in user_input.lower()
                    for word in [
                        "previous",
                        "last",
                        "that",
                        "it",
                        "them",
                        "second",
                        "third",
                        "again",
                    ]
                ),
                "safety_warnings": safety_analysis.get("warnings", []),
                "suggested_context": "",
                "referenced_files": [],
                "inferred_location": contextual_info.get("inferred_location", ""),
                "location_inherited": bool(contextual_info.get("inferred_location")),
                "risk_level": safety_analysis.get("risk_level", "low"),
            }

    def _simple_context_detection(self, user_input: str) -> list[str]:
        """Simple fallback context detection"""
        contextual_words = [
            "previous",
            "last",
            "that",
            "it",
            "them",
            "second",
            "third",
            "again",
            "same",
        ]
        return [word for word in contextual_words if word in user_input.lower()]

    def _analyze_safety_concerns(
        self, user_input: str, history_context: str
    ) -> dict[str, Any]:
        """Analyze user input and history for safety concerns"""
        user_input_lower = user_input.lower()
        history_lower = history_context.lower()

        safety_analysis = {"warnings": [], "risk_level": "low"}

        # High-risk destructive commands
        high_risk_patterns = [
            "rm -rf",
            "rm -r",
            "rmdir",
            "delete",
            "remove",
            "unlink",
            "format",
            "mkfs",
            "dd if=",
            ">/dev/null",
            "truncate",
            "shred",
            "wipe",
            "erase",
        ]

        # Medium-risk commands
        medium_risk_patterns = [
            "mv",
            "move",
            "cp -r",
            "copy",
            "chmod",
            "chown",
            "sudo",
            "su -",
            "kill",
            "killall",
            "pkill",
        ]

        # Check for high-risk patterns
        for pattern in high_risk_patterns:
            if pattern in user_input_lower:
                safety_analysis["risk_level"] = "high"
                if any(
                    ref in user_input_lower
                    for ref in ["that", "it", "them", "largest", "previous"]
                ):
                    safety_analysis["warnings"].append(
                        f"⚠️ HIGH RISK: '{pattern}' command with contextual reference - "
                        "please verify what files/directories will be affected"
                    )
                else:
                    safety_analysis["warnings"].append(
                        f"⚠️ HIGH RISK: '{pattern}' command detected - use with extreme caution"
                    )
                break

        # Check for medium-risk patterns
        if safety_analysis["risk_level"] == "low":
            for pattern in medium_risk_patterns:
                if pattern in user_input_lower:
                    safety_analysis["risk_level"] = "medium"
                    if any(
                        ref in user_input_lower
                        for ref in ["that", "it", "them", "largest", "previous"]
                    ):
                        safety_analysis["warnings"].append(
                            f"⚠️ MEDIUM RISK: '{pattern}' command with contextual reference - "
                            "please confirm target files/directories"
                        )
                    break

        # Check for contextual references to previous dangerous operations
        if any(
            cmd in history_lower for cmd in high_risk_patterns + medium_risk_patterns
        ):
            if any(
                ref in user_input_lower
                for ref in ["that", "it", "them", "same", "again"]
            ):
                safety_analysis["warnings"].append(
                    "⚠️ CONTEXTUAL SAFETY: You're referencing a previous potentially dangerous operation"
                )
                if safety_analysis["risk_level"] == "low":
                    safety_analysis["risk_level"] = "medium"

        # Check for file system operations on system directories
        system_dirs = [
            "/",
            "/bin",
            "/usr",
            "/etc",
            "/boot",
            "/lib",
            "/sbin",
            "/sys",
            "/dev",
        ]
        for sys_dir in system_dirs:
            if sys_dir in user_input_lower and any(
                cmd in user_input_lower
                for cmd in high_risk_patterns + medium_risk_patterns
            ):
                safety_analysis["warnings"].append(
                    f"⚠️ CRITICAL: Operation targeting system directory '{sys_dir}' - EXTREMELY DANGEROUS"
                )
                safety_analysis["risk_level"] = "high"

        return safety_analysis

    async def get_conversation_context(self, max_turns: int = 5) -> str:
        """Get formatted conversation context for AI prompts"""
        if not self._current_session:
            return ""

        recent_turns = self._current_session.turns[-max_turns:]
        context_parts = []

        context_parts.append(
            f"Session Context: {self._current_session.context_summary}"
        )
        context_parts.append(
            f"Working Directory: {self._current_session.working_directory}"
        )
        context_parts.append(
            f"Recent Commands: {', '.join(self._current_session.active_commands[-3:])}"
        )

        context_parts.append("\nRecent Conversation:")
        for turn in recent_turns:
            context_parts.append(f"User: {turn.user_input}")
            if turn.command_executed:
                context_parts.append(f"Command: {turn.command_executed}")
                if turn.execution_result:
                    # Truncate long results
                    result = (
                        turn.execution_result[:200] + "..."
                        if len(turn.execution_result) > 200
                        else turn.execution_result
                    )
                    context_parts.append(f"Result: {result}")

        return "\n".join(context_parts)

    async def list_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent conversation sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT session_id, created_at, title, context_summary,
                       (SELECT COUNT(*) FROM conversation_turns WHERE session_id = conversations.session_id) as turn_count
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
            """,
                (limit,),
            )

            sessions = []
            for row in cursor.fetchall():
                sessions.append(
                    {
                        "session_id": row[0],
                        "created_at": row[1],
                        "title": row[2] or "Untitled Session",
                        "summary": row[3] or "",
                        "turn_count": row[4],
                    }
                )

            return sessions

    async def search_conversations(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Search through conversation history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT c.session_id, c.title, c.context_summary, t.user_input, t.timestamp
                FROM conversations c
                JOIN conversation_turns t ON c.session_id = t.session_id
                WHERE t.user_input LIKE ? OR t.command_executed LIKE ? OR c.title LIKE ?
                ORDER BY t.timestamp DESC
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", f"%{query}%", limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "session_id": row[0],
                        "title": row[1] or "Untitled Session",
                        "summary": row[2] or "",
                        "matching_input": row[3],
                        "timestamp": row[4],
                    }
                )

            return results

    async def get_quick_action_suggestions(
        self, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get quick action suggestions based on conversation history"""
        if not self._current_session or not self._context_agent:
            return []

        try:
            # Build recent context
            recent_context = self._build_history_context(max_turns=5)
            active_commands = (
                self._current_session.active_commands[-3:]
                if self._current_session.active_commands
                else []
            )

            prompt = f"""
            Based on this conversation history, suggest {limit} practical quick actions the user might want to do next:

            Recent Conversation:
            {recent_context}

            Recent Commands: {', '.join(active_commands)}

            Suggest actions as JSON array with this format:
            [
                {{
                    "action": "Brief description",
                    "command": "suggested shell command",
                    "rationale": "Why this makes sense based on history",
                    "priority": "high/medium/low"
                }}
            ]

            Focus on:
            - Logical follow-up actions based on what was just done
            - Common workflows (e.g., after finding large files, user might want to delete them)
            - Checking results of previous operations
            - Related operations in the same domain
            - Safety checks (like backing up before deleting)

            Only suggest safe, practical actions that make sense in context.
            """

            result = await self._context_agent.run(prompt)

            try:
                suggestions = json.loads(result.output)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                return self._generate_fallback_suggestions()

        except Exception:
            return self._generate_fallback_suggestions()

    def _generate_fallback_suggestions(self) -> list[dict[str, Any]]:
        """Generate fallback suggestions when AI analysis fails"""
        if not self._current_session:
            return []

        suggestions = []
        recent_commands = (
            self._current_session.active_commands[-3:]
            if self._current_session.active_commands
            else []
        )

        # Pattern-based suggestions
        for cmd in recent_commands:
            cmd_lower = cmd.lower()

            if "find" in cmd_lower and "largest" in cmd_lower:
                suggestions.append(
                    {
                        "action": "Check disk usage of current directory",
                        "command": "du -sh .",
                        "rationale": "After finding large files, checking overall disk usage is common",
                        "priority": "medium",
                    }
                )
                suggestions.append(
                    {
                        "action": "List files by size in current directory",
                        "command": "ls -lahS",
                        "rationale": "Follow up to see all files sorted by size",
                        "priority": "low",
                    }
                )

            if "ls" in cmd_lower or "dir" in cmd_lower:
                suggestions.append(
                    {
                        "action": "Show hidden files and details",
                        "command": "ls -la",
                        "rationale": "After basic listing, often want to see hidden files and permissions",
                        "priority": "medium",
                    }
                )

            if "git" in cmd_lower:
                suggestions.append(
                    {
                        "action": "Check git status",
                        "command": "git status",
                        "rationale": "Common to check git status after git operations",
                        "priority": "high",
                    }
                )

        # Generic suggestions if no specific patterns
        if not suggestions:
            suggestions = [
                {
                    "action": "Check current directory contents",
                    "command": "ls -la",
                    "rationale": "Good way to understand current context",
                    "priority": "medium",
                },
                {
                    "action": "Show current directory path",
                    "command": "pwd",
                    "rationale": "Useful to know where you are",
                    "priority": "low",
                },
            ]

        return suggestions[:3]  # Limit to 3 fallback suggestions

    def get_current_session(self) -> ConversationSession | None:
        """Get the current active session"""
        return self._current_session

    async def _extract_contextual_info(self, user_input: str) -> dict[str, Any]:
        """Extract contextual information from user input with enhanced location memory"""
        context = {}

        if self._current_session and self._current_session.turns:
            # Extract information from recent turns
            recent_turn = self._current_session.turns[-1]
            context["previous_command"] = recent_turn.command_executed
            context["previous_result"] = recent_turn.execution_result

            # Enhanced location context extraction
            if recent_turn.command_executed:
                context["previous_locations"] = self._extract_locations_from_command(
                    recent_turn.command_executed
                )

            # Look for contextual patterns
            if any(
                word in user_input.lower() for word in ["largest", "biggest", "first"]
            ):
                context["reference_type"] = "size_superlative"
            elif any(
                word in user_input.lower()
                for word in ["second", "next", "another", "third"]
            ):
                context["reference_type"] = "sequence"
                # For sequence references, preserve the location from previous command
                if (
                    recent_turn.command_executed
                    and "Downloads" in recent_turn.command_executed
                ):
                    context["inferred_location"] = "~/Downloads"
                elif recent_turn.command_executed and any(
                    path in recent_turn.command_executed
                    for path in ["~/Documents", "~/Desktop", "~/"]
                ):
                    import re

                    paths = re.findall(r"~/[\w/]*", recent_turn.command_executed)
                    if paths:
                        context["inferred_location"] = paths[0]
            elif any(word in user_input.lower() for word in ["that", "it", "same"]):
                context["reference_type"] = "direct_reference"

        return context

    def _extract_locations_from_command(self, command: str) -> list[str]:
        """Extract file/directory locations from a command"""
        import re

        locations = []

        # Common path patterns
        path_patterns = [
            r"~/[\w/]+",  # Home-relative paths
            r"/[\w/]+",  # Absolute paths
            r"\.[\w/]*",  # Relative paths starting with .
        ]

        for pattern in path_patterns:
            matches = re.findall(pattern, command)
            locations.extend(matches)

        return list(set(locations))  # Remove duplicates

    async def _generate_session_title(self, first_input: str) -> str:
        """Generate a title for the conversation session"""
        if not self._context_agent:
            # Simple fallback title generation
            words = first_input.split()[:4]
            return " ".join(words).title()

        try:
            prompt = f"Generate a concise 3-5 word title for a conversation that starts with: '{first_input}'"
            result = await self._context_agent.run(prompt)
            return result.output.strip().replace('"', "")
        except Exception:
            # Fallback
            words = first_input.split()[:3]
            return " ".join(words).title()

    async def _generate_context_summary(self) -> str:
        """Generate a summary of the conversation context"""
        if not self._context_agent or not self._current_session:
            return "Interactive session"

        try:
            history = self._build_history_context(max_turns=5)
            prompt = f"Create a 1-2 sentence summary of this conversation context:\n{history}"
            result = await self._context_agent.run(prompt)
            return result.output.strip()
        except Exception:
            return f"Session with {len(self._current_session.turns)} interactions"

    def _build_history_context(self, max_turns: int = 5) -> str:
        """Build conversation history for context"""
        if not self._current_session:
            return ""

        recent_turns = self._current_session.turns[-max_turns:]
        context_lines = []

        for i, turn in enumerate(recent_turns, 1):
            context_lines.append(f"{i}. User: {turn.user_input}")
            if turn.command_executed:
                context_lines.append(f"   Command: {turn.command_executed}")
            if turn.execution_result:
                result = (
                    turn.execution_result[:100] + "..."
                    if len(turn.execution_result) > 100
                    else turn.execution_result
                )
                context_lines.append(f"   Result: {result}")

        return "\n".join(context_lines)

    async def _archive_old_turns(self, keep_recent: int = 50):
        """Archive older turns to individual turn storage, keeping only recent ones in memory"""
        if not self._current_session or len(self._current_session.turns) <= keep_recent:
            return

        # Calculate how many turns to archive
        turns_to_archive = self._current_session.turns[:-keep_recent]
        remaining_turns = self._current_session.turns[-keep_recent:]

        with sqlite3.connect(self.db_path) as conn:
            # Mark archived turns in the database
            for turn in turns_to_archive:
                conn.execute(
                    """
                    UPDATE conversation_turns
                    SET is_archived = 1
                    WHERE turn_id = ? AND session_id = ?
                """,
                    (turn.id, self._current_session.session_id),
                )

            # Update archived count
            self._archived_turn_count += len(turns_to_archive)

            # Update total turn count in conversations table
            conn.execute(
                """
                UPDATE conversations
                SET total_turn_count = ?
                WHERE session_id = ?
            """,
                (self._archived_turn_count + len(remaining_turns), self._current_session.session_id),
            )

        # Update session to keep only recent turns in memory
        self._current_session.turns = remaining_turns

        print(
            f"ℹ️  Archived {len(turns_to_archive)} old turns. "
            f"Keeping {len(remaining_turns)} recent turns in memory."
        )

    async def _detect_corruption(self, session: ConversationSession) -> bool:
        """Detect potential corruption in session data"""
        try:
            # Check if session data can be serialized
            json.dumps(session.model_dump(mode="json"))

            # Check for invalid turn data
            for turn in session.turns:
                if not turn.id or not turn.timestamp:
                    return True
                # Verify turn can be serialized
                json.dumps(turn.model_dump(mode="json"))

            # Check for duplicate turn IDs
            turn_ids = [t.id for t in session.turns]
            if len(turn_ids) != len(set(turn_ids)):
                return True

            return False
        except Exception:
            return True

    async def _recover_corrupted_session(self, session_id: str) -> ConversationSession | None:
        """Attempt to recover a corrupted session from individual turn records"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load session metadata
                cursor = conn.execute(
                    """
                    SELECT session_id, created_at, updated_at, title, context_summary,
                           active_commands, working_directory, environment_info
                    FROM conversations WHERE session_id = ?
                """,
                    (session_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                # Load individual turns from conversation_turns table
                turns_cursor = conn.execute(
                    """
                    SELECT turn_id, timestamp, user_input, ai_response,
                           command_executed, execution_result, context_used, tokens_consumed,
                           is_archived
                    FROM conversation_turns
                    WHERE session_id = ?
                    ORDER BY timestamp ASC
                """,
                    (session_id,),
                )

                turns = []
                archived_count = 0
                for turn_row in turns_cursor.fetchall():
                    try:
                        turn = ConversationTurn(
                            id=turn_row[0],
                            timestamp=datetime.fromisoformat(turn_row[1]),
                            user_input=turn_row[2] or "",
                            ai_response=turn_row[3] or "",
                            command_executed=turn_row[4],
                            execution_result=turn_row[5],
                            context_used=json.loads(turn_row[6]) if turn_row[6] else {},
                            tokens_consumed=json.loads(turn_row[7]) if turn_row[7] else {},
                        )

                        # Only load non-archived turns into memory
                        if not turn_row[8]:  # is_archived
                            turns.append(turn)
                        else:
                            archived_count += 1

                    except Exception as turn_error:
                        # Skip corrupted turns but continue recovery
                        print(f"Warning: Skipped corrupted turn {turn_row[0]}: {turn_error}")
                        continue

                # Reconstruct session
                session = ConversationSession(
                    session_id=row[0],
                    created_at=datetime.fromisoformat(row[1]),
                    updated_at=datetime.fromisoformat(row[2]),
                    title=row[3] or "Recovered Session",
                    context_summary=row[4] or "Session recovered from corruption",
                    active_commands=json.loads(row[5]) if row[5] else [],
                    working_directory=row[6] or str(Path.cwd()),
                    environment_info=json.loads(row[7]) if row[7] else {},
                    turns=turns,
                )

                self._archived_turn_count = archived_count

                print(
                    f"✅ Successfully recovered session with {len(turns)} turns "
                    f"({archived_count} archived)"
                )

                return session

        except Exception as e:
            print(f"❌ Failed to recover session: {e}")
            return None

    async def _save_session(self, session: ConversationSession):
        """Save session to database with corruption detection"""
        # Detect corruption before saving
        if await self._detect_corruption(session):
            print("⚠️  Warning: Corruption detected in session data. Attempting recovery...")
            # Try to save individual turns at least
            with sqlite3.connect(self.db_path) as conn:
                for turn in session.turns:
                    try:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO conversation_turns
                            (turn_id, session_id, timestamp, user_input, ai_response,
                             command_executed, execution_result, context_used, tokens_consumed, is_archived)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """,
                            (
                                turn.id,
                                session.session_id,
                                turn.timestamp.isoformat(),
                                turn.user_input,
                                turn.ai_response,
                                turn.command_executed,
                                turn.execution_result,
                                json.dumps(turn.context_used),
                                json.dumps(turn.tokens_consumed),
                            ),
                        )
                    except Exception as turn_error:
                        print(f"Warning: Failed to save turn {turn.id}: {turn_error}")
            return

        total_turns = len(session.turns) + self._archived_turn_count

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO conversations
                (session_id, created_at, updated_at, title, context_summary,
                 active_commands, working_directory, environment_info, turns_data,
                 is_archived, total_turn_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
                (
                    session.session_id,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                    session.title,
                    session.context_summary,
                    json.dumps(session.active_commands),
                    session.working_directory,
                    json.dumps(session.environment_info),
                    json.dumps(
                        [turn.model_dump(mode="json") for turn in session.turns]
                    ),
                    total_turns,
                ),
            )

            # Save individual turns
            for turn in session.turns:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO conversation_turns
                    (turn_id, session_id, timestamp, user_input, ai_response,
                     command_executed, execution_result, context_used, tokens_consumed, is_archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                    (
                        turn.id,
                        session.session_id,
                        turn.timestamp.isoformat(),
                        turn.user_input,
                        turn.ai_response,
                        turn.command_executed,
                        turn.execution_result,
                        json.dumps(turn.context_used),
                        json.dumps(turn.tokens_consumed),
                    ),
                )

    async def _load_session(self, session_id: str) -> ConversationSession | None:
        """Load session from database with corruption recovery"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT session_id, created_at, updated_at, title, context_summary,
                           active_commands, working_directory, environment_info, turns_data,
                           is_archived, total_turn_count
                    FROM conversations WHERE session_id = ?
                """,
                    (session_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                # Try to parse the turns_data JSON blob
                turns = []
                try:
                    turns_data = json.loads(row[8]) if row[8] else []
                    turns = [ConversationTurn(**turn_data) for turn_data in turns_data]

                    # Load total turn count and calculate archived count
                    total_count = row[10] or 0
                    self._archived_turn_count = total_count - len(turns)

                except (json.JSONDecodeError, TypeError, ValueError) as parse_error:
                    print(f"⚠️  Corruption detected in turns_data: {parse_error}")
                    print("Attempting recovery from individual turn records...")

                    # Attempt recovery from individual turn records
                    recovered_session = await self._recover_corrupted_session(session_id)
                    if recovered_session:
                        return recovered_session
                    else:
                        print("❌ Recovery failed. Creating empty session.")
                        turns = []
                        self._archived_turn_count = 0

                session = ConversationSession(
                    session_id=row[0],
                    created_at=datetime.fromisoformat(row[1]),
                    updated_at=datetime.fromisoformat(row[2]),
                    title=row[3] or "",
                    context_summary=row[4] or "",
                    active_commands=json.loads(row[5]) if row[5] else [],
                    working_directory=row[6] or "",
                    environment_info=json.loads(row[7]) if row[7] else {},
                    turns=turns,
                )

                # Verify loaded session integrity
                if await self._detect_corruption(session):
                    print("⚠️  Loaded session failed integrity check. Attempting recovery...")
                    recovered_session = await self._recover_corrupted_session(session_id)
                    return recovered_session if recovered_session else session

                return session

        except Exception as e:
            print(f"❌ Error loading session {session_id}: {e}")
            print("Attempting recovery...")
            return await self._recover_corrupted_session(session_id)
