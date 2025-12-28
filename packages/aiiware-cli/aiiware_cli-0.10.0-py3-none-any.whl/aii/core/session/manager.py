# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Global session manager for thread-safe session lifecycle management"""


import threading
import time
import uuid
from typing import Optional

from .models import SessionMetrics, FunctionExecution


class SessionManager:
    """Global session manager with thread-safe operations"""

    _current_session: Optional[SessionMetrics] = None
    _session_lock = threading.Lock()
    _session_history: list[SessionMetrics] = []
    _max_history = 100  # Keep last 100 sessions for analysis

    @classmethod
    def start_new_session(cls, user_input: str, session_id: str = None) -> SessionMetrics:
        """Initialize new global session with automatic ID generation"""
        with cls._session_lock:
            # Finalize any existing session first
            if cls._current_session and not cls._current_session.is_finalized:
                cls._finalize_session_internal(cls._current_session)

            # Generate session ID if not provided
            if session_id is None:
                session_id = f"session_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Create new session
            cls._current_session = SessionMetrics(
                session_id=session_id,
                user_input=user_input,
                start_time=time.time()
            )

            return cls._current_session

    @classmethod
    def get_current_session(cls) -> Optional[SessionMetrics]:
        """Get current active session (thread-safe read)"""
        with cls._session_lock:
            return cls._current_session

    @classmethod
    def add_function_execution(cls, execution: FunctionExecution) -> bool:
        """Add function execution to current session"""
        with cls._session_lock:
            if cls._current_session is None:
                return False

            cls._current_session.add_function_execution(execution)
            return True

    @classmethod
    def finalize_current_session(cls) -> Optional[SessionMetrics]:
        """Finalize and return current session, store in history"""
        with cls._session_lock:
            if cls._current_session is None:
                return None

            session = cls._current_session
            cls._finalize_session_internal(session)

            # Move to history and clear current
            cls._add_to_history(session)
            cls._current_session = None

            return session

    @classmethod
    def _finalize_session_internal(cls, session: SessionMetrics) -> None:
        """Internal method to finalize a session (assumes lock is held)"""
        if not session.is_finalized:
            session.finalize_session()

    @classmethod
    def _add_to_history(cls, session: SessionMetrics) -> None:
        """Add session to history with size limit (assumes lock is held)"""
        cls._session_history.append(session)

        # Maintain history size limit
        if len(cls._session_history) > cls._max_history:
            cls._session_history.pop(0)

    @classmethod
    def get_session_history(cls, limit: int = 10) -> list[SessionMetrics]:
        """Get recent session history"""
        with cls._session_lock:
            return cls._session_history[-limit:].copy() if cls._session_history else []

    @classmethod
    def _get_session_stats_internal(cls) -> dict:
        """Internal method to get stats without acquiring lock (lock must be held by caller)"""
        if not cls._session_history:
            return {
                "total_sessions": 0,
                "total_functions": 0,
                "total_tokens": 0,
                "average_success_rate": 0.0,
                "average_session_duration": 0.0
            }

        total_sessions = len(cls._session_history)
        total_functions = sum(s.total_functions for s in cls._session_history)
        total_tokens = sum(s.total_tokens for s in cls._session_history)
        total_success_rate = sum(s.success_rate for s in cls._session_history)
        total_duration = sum(s.session_duration for s in cls._session_history)

        return {
            "total_sessions": total_sessions,
            "total_functions": total_functions,
            "total_tokens": total_tokens,
            "average_success_rate": total_success_rate / total_sessions,
            "average_session_duration": total_duration / total_sessions,
            "current_session_active": cls._current_session is not None
        }

    @classmethod
    def get_session_stats(cls) -> dict:
        """Get aggregate statistics across all sessions"""
        with cls._session_lock:
            return cls._get_session_stats_internal()

    @classmethod
    def clear_history(cls) -> int:
        """Clear session history and return number of cleared sessions"""
        with cls._session_lock:
            count = len(cls._session_history)
            cls._session_history.clear()
            return count

    @classmethod
    def force_clear_current_session(cls) -> Optional[SessionMetrics]:
        """Force clear current session without finalization (for error recovery)"""
        with cls._session_lock:
            session = cls._current_session
            cls._current_session = None
            return session

    @classmethod
    def is_session_active(cls) -> bool:
        """Check if there's an active session"""
        with cls._session_lock:
            return cls._current_session is not None

    @classmethod
    def get_session_summary(cls) -> dict:
        """Get comprehensive summary of current session and history"""
        with cls._session_lock:
            current_summary = None
            if cls._current_session:
                current_summary = cls._current_session.to_summary_dict()

            # Use internal method to avoid double-locking
            stats = cls._get_session_stats_internal()

            recent_sessions = [s.to_summary_dict() for s in cls._session_history[-5:]]

            return {
                "current_session": current_summary,
                "history_stats": stats,
                "recent_sessions": recent_sessions
            }


# Convenience functions for easier usage
def start_session(user_input: str, session_id: str = None) -> SessionMetrics:
    """Convenience function to start a new session"""
    return SessionManager.start_new_session(user_input, session_id)


def get_session() -> Optional[SessionMetrics]:
    """Convenience function to get current session"""
    return SessionManager.get_current_session()


def add_execution(execution: FunctionExecution) -> bool:
    """Convenience function to add function execution"""
    return SessionManager.add_function_execution(execution)


def finalize_session() -> Optional[SessionMetrics]:
    """Convenience function to finalize current session"""
    return SessionManager.finalize_current_session()


def is_active() -> bool:
    """Convenience function to check if session is active"""
    return SessionManager.is_session_active()
