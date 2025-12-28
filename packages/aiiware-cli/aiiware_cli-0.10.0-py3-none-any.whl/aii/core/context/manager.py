# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Context Manager - Manage chat history, session state, and context persistence"""


import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ChatContext, ChatMessage


class ContextManager:
    """Manages chat contexts and session state"""

    def __init__(self, storage_path: Path | None = None):
        """Initialize context manager with storage configuration"""
        # Use the provided storage path directly, don't add /chats subdirectory
        # This matches where files are actually being saved
        self.storage_path = storage_path or Path.home() / ".aii"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory cache for recent chats
        self._cache: dict[str, ChatContext] = {}
        self._cache_size_limit = 50

        # Current session state - will be loaded from storage if available
        self.current_session: ChatContext | None = None
        self._session_auto_loaded = False

    async def start_new_chat(
        self, initial_message: str | None = None, title: str | None = None
    ) -> ChatContext:
        """Create a new chat session"""
        context = ChatContext(title=title or "")

        if initial_message:
            context.add_user_message(initial_message, {"type": "initial"})

        self.current_session = context
        await self._cache_context(context)

        return context

    async def continue_chat(self, chat_id: str, message_limit: int = 20) -> ChatContext:
        """Load and continue existing chat session"""
        # Try cache first
        context: ChatContext | None
        if chat_id in self._cache:
            context = self._cache[chat_id]
        else:
            # Load from storage
            context = await self.load_chat(chat_id, message_limit)
            if context is None:
                raise ValueError(f"Chat {chat_id} not found")

        self.current_session = context
        return context

    async def save_chat(self, context: ChatContext) -> bool:
        """Save chat context to persistent storage"""
        try:
            # Save to file
            chat_file = self.storage_path / f"{context.chat_id}.json"
            chat_data = context.to_dict()

            with open(chat_file, "w", encoding="utf-8") as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)

            # Update cache
            await self._cache_context(context)

            return True
        except Exception as e:
            print(f"Error saving chat {context.chat_id}: {e}")
            return False

    async def load_chat(
        self, chat_id: str, message_limit: int = 0
    ) -> ChatContext | None:
        """Load chat from storage"""
        try:
            chat_file = self.storage_path / f"{chat_id}.json"

            if not chat_file.exists():
                return None

            with open(chat_file, encoding="utf-8") as f:
                chat_data = json.load(f)

            context = ChatContext.from_dict(chat_data)

            # Apply message limit if specified
            if message_limit > 0 and len(context.messages) > message_limit:
                # Keep recent messages and create summary of older ones
                older_messages = context.messages[:-message_limit]
                context.messages = context.messages[-message_limit:]

                # Add context summary
                summary = await self._create_context_summary(older_messages)
                if summary:
                    context.metadata["context_summary"] = summary

            await self._cache_context(context)
            return context

        except Exception as e:
            print(f"Error loading chat {chat_id}: {e}")
            return None

    async def list_chats(
        self, limit: int = 50, since: datetime | None = None, archived: bool = False
    ) -> list[dict[str, Any]]:
        """List available chats with metadata"""
        chats = []

        try:
            for chat_file in self.storage_path.glob("*.json"):
                try:
                    with open(chat_file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Filter by archived status
                    if data.get("archived", False) != archived:
                        continue

                    # Filter by date if specified
                    if since:
                        updated_at = datetime.fromisoformat(data["updated_at"])
                        if updated_at < since:
                            continue

                    # Extract metadata
                    chat_info = {
                        "id": data["chat_id"],
                        "title": data["title"],
                        "message_count": len(data.get("messages", [])),
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "tags": data.get("tags", []),
                        "archived": data.get("archived", False),
                    }

                    chats.append(chat_info)

                except Exception as e:
                    print(f"Error reading chat file {chat_file}: {e}")
                    continue

            # Sort by updated_at descending
            chats.sort(key=lambda x: x["updated_at"], reverse=True)

            # Apply limit
            return chats[:limit] if limit > 0 else chats

        except Exception as e:
            print(f"Error listing chats: {e}")
            return []

    async def auto_load_recent_session(
        self, max_age_minutes: int = 60
    ) -> ChatContext | None:
        """Auto-load the most recent session if it's not too old and merge with current session"""
        if self._session_auto_loaded:
            return self.current_session

        try:
            chats = await self.list_chats(limit=1)
            if not chats:
                return None

            most_recent = chats[0]
            updated_at = datetime.fromisoformat(most_recent["updated_at"])
            age_minutes = (datetime.now() - updated_at).total_seconds() / 60

            # Only auto-load if the session is recent enough
            if age_minutes <= max_age_minutes:
                recent_context = await self.load_chat(
                    most_recent["id"], message_limit=10
                )
                if recent_context:
                    # If we already have a current session, merge the messages
                    if (
                        self.current_session
                        and recent_context.chat_id != self.current_session.chat_id
                    ):
                        # Add recent messages to current session for context
                        for message in recent_context.messages:
                            # Only add if it's not already present (avoid duplicates)
                            if not any(
                                m.message_id == message.message_id
                                for m in self.current_session.messages
                            ):
                                self.current_session.messages.insert(
                                    -1, message
                                )  # Insert before current message
                        print(
                            f"🔍 DEBUG: Merged {len(recent_context.messages)} messages from recent session"
                        )
                    else:
                        # No current session, use the loaded one
                        self.current_session = recent_context
                        print(
                            f"🔍 DEBUG: Auto-loaded recent session with {len(recent_context.messages)} messages"
                        )

                    self._session_auto_loaded = True
                    return self.current_session

        except Exception as e:
            print(f"Error auto-loading recent session: {e}")

        return self.current_session

    async def search_chats(
        self, query: str, search_content: bool = False, tag_filter: str | None = None
    ) -> list[dict[str, Any]]:
        """Search chats by title, content, or tags"""
        matching_chats = []
        query_lower = query.lower()

        try:
            for chat_file in self.storage_path.glob("*.json"):
                try:
                    with open(chat_file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Check tag filter first
                    if tag_filter and tag_filter not in data.get("tags", []):
                        continue

                    match_found = False
                    match_reason = []

                    # Search in title
                    if query_lower in data["title"].lower():
                        match_found = True
                        match_reason.append("title")

                    # Search in tags
                    if any(query_lower in tag.lower() for tag in data.get("tags", [])):
                        match_found = True
                        match_reason.append("tags")

                    # Search in content if requested
                    if search_content and not match_found:
                        for message in data.get("messages", []):
                            if query_lower in message["content"].lower():
                                match_found = True
                                match_reason.append("content")
                                break

                    if match_found:
                        chat_info = {
                            "id": data["chat_id"],
                            "title": data["title"],
                            "message_count": len(data.get("messages", [])),
                            "created_at": data["created_at"],
                            "updated_at": data["updated_at"],
                            "tags": data.get("tags", []),
                            "match_reason": match_reason,
                        }
                        matching_chats.append(chat_info)

                except Exception as e:
                    print(f"Error searching chat file {chat_file}: {e}")
                    continue

            # Sort by relevance (title matches first, then by updated date)
            matching_chats.sort(
                key=lambda x: (
                    "title" not in x["match_reason"],  # Title matches first
                    -datetime.fromisoformat(x["updated_at"]).timestamp(),
                )
            )

            return matching_chats

        except Exception as e:
            print(f"Error searching chats: {e}")
            return []

    async def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat permanently"""
        try:
            chat_file = self.storage_path / f"{chat_id}.json"

            if chat_file.exists():
                chat_file.unlink()

                # Remove from cache
                if chat_id in self._cache:
                    del self._cache[chat_id]

                # Clear current session if it's the deleted chat
                if self.current_session and self.current_session.chat_id == chat_id:
                    self.current_session = None

                return True

            return False

        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return False

    async def archive_chat(self, chat_id: str) -> bool:
        """Archive a chat (hide from default listing)"""
        try:
            context = await self.load_chat(chat_id)
            if context:
                context.archived = True
                return await self.save_chat(context)
            return False
        except Exception as e:
            print(f"Error archiving chat {chat_id}: {e}")
            return False

    async def update_chat_metadata(
        self,
        chat_id: str,
        title: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Update chat metadata"""
        try:
            context = await self.load_chat(chat_id)
            if not context:
                return False

            if title is not None:
                context.title = title

            if tags is not None:
                context.tags = tags

            if metadata is not None:
                context.metadata.update(metadata)

            context.updated_at = datetime.now()
            return await self.save_chat(context)

        except Exception as e:
            print(f"Error updating chat metadata {chat_id}: {e}")
            return False

    async def add_message(
        self,
        context: ChatContext,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ChatMessage:
        """Add message to context and save"""
        message = context.add_message(role, content, metadata)

        # Auto-save if this is the current session
        if self.current_session and self.current_session.chat_id == context.chat_id:
            await self.save_chat(context)

        return message

    async def export_chat(self, chat_id: str, format: str = "json") -> str | None:
        """Export chat in specified format"""
        context = await self.load_chat(chat_id)
        if not context:
            return None

        if format == "json":
            return json.dumps(context.to_dict(), indent=2, ensure_ascii=False)
        elif format == "markdown":
            return self._export_as_markdown(context)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    async def import_chat(self, data: str, format: str = "json") -> ChatContext | None:
        """Import chat from data"""
        try:
            if format == "json":
                chat_data = json.loads(data)
                context = ChatContext.from_dict(chat_data)

                # Ensure unique chat_id
                if await self.load_chat(context.chat_id):
                    context.chat_id = f"{context.chat_id}-imported-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                await self.save_chat(context)
                return context
            else:
                raise ValueError(f"Unsupported import format: {format}")

        except Exception as e:
            print(f"Error importing chat: {e}")
            return None

    # Private helper methods

    async def _cache_context(self, context: ChatContext) -> None:
        """Add context to cache with size management"""
        # Add to cache
        self._cache[context.chat_id] = context

        # Manage cache size
        if len(self._cache) > self._cache_size_limit:
            # Remove oldest entries
            sorted_items = sorted(self._cache.items(), key=lambda x: x[1].updated_at)

            # Keep only the most recent entries
            self._cache = dict(sorted_items[-self._cache_size_limit :])

    async def _create_context_summary(self, messages: list[ChatMessage]) -> str | None:
        """Create a summary of older messages (placeholder for LLM-based summarization)"""
        if not messages:
            return None

        # Simple summarization - count messages by role
        user_count = sum(1 for msg in messages if msg.role == "user")
        assistant_count = sum(1 for msg in messages if msg.role == "assistant")

        return f"Earlier discussion: {user_count} user messages, {assistant_count} assistant responses"

    def _export_as_markdown(self, context: ChatContext) -> str:
        """Export chat as markdown"""
        lines = [
            f"# {context.title}",
            "",
            f"**Chat ID:** {context.chat_id}",
            f"**Created:** {context.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Updated:** {context.updated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if context.tags:
            lines.extend(
                [
                    f"**Tags:** {', '.join(context.tags)}",
                ]
            )

        lines.extend(["", "## Messages", ""])

        for message in context.messages:
            role_icon = (
                "👤"
                if message.role == "user"
                else "🤖" if message.role == "assistant" else "⚙️"
            )
            timestamp = message.timestamp.strftime("%H:%M:%S")

            lines.extend(
                [
                    f"### {role_icon} {message.role.title()} ({timestamp})",
                    "",
                    message.content,
                    "",
                ]
            )

        return "\\n".join(lines)
