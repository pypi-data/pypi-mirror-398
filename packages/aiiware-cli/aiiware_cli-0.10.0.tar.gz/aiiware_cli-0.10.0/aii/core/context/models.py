# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Context-related data models"""


import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class ChatMessage:
    """Individual message in a chat"""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        """Validate role"""
        if self.role not in ("user", "assistant", "system"):
            raise ValueError(f"Invalid role: {self.role}")


@dataclass
class ChatContext:
    """Chat conversation context with pending action management"""

    chat_id: str = field(
        default_factory=lambda: f"chat-{datetime.now().strftime('%Y-%m-%d')}-{uuid.uuid4().hex[:8]}"
    )
    title: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: list[ChatMessage] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    archived: bool = False

    # Pending action management (v0.4.13)
    _pending_actions: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _action_timeout: int = field(default=300, init=False, repr=False)  # 5 minutes
    _action_history: list[dict[str, Any]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        """Set default title if not provided"""
        if not self.title:
            self.title = f"Chat {self.chat_id[-8:]}"

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Add a message to the conversation"""
        message = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message

    def add_user_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Add a user message"""
        return self.add_message("user", content, metadata)

    def add_assistant_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Add an assistant message"""
        return self.add_message("assistant", content, metadata)

    def add_system_message(
        self, content: str, metadata: dict[str, Any] | None = None
    ) -> ChatMessage:
        """Add a system message"""
        return self.add_message("system", content, metadata)

    def get_recent_messages(self, limit: int = 20) -> list[ChatMessage]:
        """Get recent messages up to limit"""
        return self.messages[-limit:] if limit > 0 else self.messages

    def get_messages_by_role(self, role: str) -> list[ChatMessage]:
        """Get all messages by specific role"""
        return [msg for msg in self.messages if msg.role == role]

    @property
    def message_count(self) -> int:
        """Get total message count"""
        return len(self.messages)

    @property
    def last_message(self) -> ChatMessage | None:
        """Get the last message"""
        return self.messages[-1] if self.messages else None

    @property
    def last_user_message(self) -> ChatMessage | None:
        """Get the last user message"""
        user_messages = self.get_messages_by_role("user")
        return user_messages[-1] if user_messages else None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "chat_id": self.chat_id,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                    "message_id": msg.message_id,
                }
                for msg in self.messages
            ],
            "metadata": self.metadata,
            "tags": self.tags,
            "archived": self.archived,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChatContext":
        """Create ChatContext from dictionary"""
        # Parse messages
        messages = []
        for msg_data in data.get("messages", []):
            message = ChatMessage(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {}),
                message_id=msg_data.get("message_id", str(uuid.uuid4())),
            )
            messages.append(message)

        # Create context
        context = cls(
            chat_id=data["chat_id"],
            title=data.get("title", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=messages,
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            archived=data.get("archived", False),
        )

        return context

    # Pending Action Management Methods (v0.4.13)

    def set_pending_action(self, action_type: str, data: dict[str, Any]) -> None:
        """
        Set pending action with timestamp for confirmation workflows.

        Args:
            action_type: Type of action (e.g., "shell_command", "git_commit")
            data: Action data (must include command, analysis, etc.)
        """
        self._pending_actions[action_type] = {
            **data,
            "timestamp": time.time()
        }

        # Debug logging
        if os.getenv("AII_DEBUG"):
            print(f"[ChatContext] Pending action set: {action_type}")

    def get_pending_action(self, action_type: str) -> Optional[dict[str, Any]]:
        """
        Get pending action, checking timeout.

        Args:
            action_type: Type of action to retrieve

        Returns:
            Action data if exists and not expired, None otherwise
        """
        if action_type not in self._pending_actions:
            return None

        action = self._pending_actions[action_type]

        # Check timeout
        if time.time() - action["timestamp"] > self._action_timeout:
            # Expired - clear and return None
            self.clear_pending_action(action_type)
            if os.getenv("AII_DEBUG"):
                print(f"[ChatContext] Pending action expired: {action_type}")
            return None

        return action

    def has_pending_action(self, action_type: str) -> bool:
        """
        Check if action is pending and not expired.

        Args:
            action_type: Type of action to check

        Returns:
            True if action exists and not expired, False otherwise
        """
        return self.get_pending_action(action_type) is not None

    def clear_pending_action(self, action_type: Optional[str] = None) -> None:
        """
        Clear pending action(s).

        Args:
            action_type: Specific action type to clear, or None to clear all
        """
        if action_type:
            action = self._pending_actions.pop(action_type, None)
            if action and os.getenv("AII_DEBUG"):
                print(f"[ChatContext] Pending action cleared: {action_type}")
        else:
            self._pending_actions.clear()
            if os.getenv("AII_DEBUG"):
                print(f"[ChatContext] All pending actions cleared")

    def record_action(self, action_type: str, result: str) -> None:
        """
        Record completed action for history.

        Args:
            action_type: Type of action completed
            result: Result of the action (e.g., "executed", "cancelled")
        """
        self._action_history.append({
            "type": action_type,
            "result": result,
            "timestamp": time.time()
        })

        if os.getenv("AII_DEBUG"):
            print(f"[ChatContext] Action recorded: {action_type} -> {result}")

    def get_action_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent action history.

        Args:
            limit: Maximum number of actions to return

        Returns:
            List of recent actions
        """
        return self._action_history[-limit:] if limit > 0 else self._action_history
