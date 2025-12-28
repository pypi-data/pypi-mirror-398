# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Interactive confirmation flows for AII CLI"""


import sys
from typing import Any

from .output_formatter import OutputFormatter, OutputSegment, OutputType


class ConfirmationManager:
    """Manage interactive confirmations for potentially dangerous operations"""

    def __init__(self, formatter: OutputFormatter):
        """Initialize confirmation manager"""
        self.formatter = formatter
        self.auto_confirm = False
        self.never_confirm = False

    def set_auto_confirm(self, enabled: bool) -> None:
        """Enable/disable automatic confirmation for all operations"""
        self.auto_confirm = enabled

    def set_never_confirm(self, enabled: bool) -> None:
        """Enable/disable skipping all confirmations (dangerous!)"""
        self.never_confirm = enabled

    async def confirm_function_execution(
        self,
        function_name: str,
        parameters: dict[str, Any],
        description: str = "",
        risk_level: str = "medium",
    ) -> bool:
        """
        Confirm function execution with user

        Args:
            function_name: Name of function to execute
            parameters: Function parameters
            description: Human-readable description of what will happen
            risk_level: "low", "medium", "high", or "critical"

        Returns:
            True if user confirms, False otherwise
        """
        if self.never_confirm:
            return True

        if self.auto_confirm and risk_level in ["low", "medium"]:
            return True

        # Build confirmation message
        segments = [
            OutputSegment(
                f"🤔 Confirm {function_name} execution?",
                (
                    OutputType.WARNING
                    if risk_level in ["high", "critical"]
                    else OutputType.INFO
                ),
            )
        ]

        if description:
            segments.append(OutputSegment(f"   {description}", OutputType.TEXT))

        # Show parameters if not too sensitive
        safe_params = self._sanitize_parameters(parameters)
        if safe_params:
            segments.append(OutputSegment("   Parameters:", OutputType.TEXT))
            for key, value in safe_params.items():
                segments.append(OutputSegment(f"     {key}: {value}", OutputType.TEXT))

        # Risk warning for high-risk operations
        if risk_level == "critical":
            segments.append(
                OutputSegment(
                    "   ⚠️  WARNING: This is a potentially destructive operation!",
                    OutputType.ERROR,
                )
            )
        elif risk_level == "high":
            segments.append(
                OutputSegment(
                    "   ⚠️  This operation may make significant changes",
                    OutputType.WARNING,
                )
            )

        segments.append(OutputSegment("", OutputType.TEXT))  # Empty line

        # Show confirmation prompt
        if risk_level == "critical":
            segments.append(
                OutputSegment(
                    "   Type 'yes I understand' to confirm: ", OutputType.ERROR
                )
            )
            self.formatter.display_segments(segments)
            response = input().strip()
            return response.lower() == "yes i understand"
        else:
            segments.append(OutputSegment("   Continue? (y/N): ", OutputType.INFO))
            self.formatter.display_segments(segments)
            response = input().strip()
            return response.lower() in ("y", "yes")

    async def confirm_file_operation(
        self,
        operation: str,
        file_path: str,
        backup_created: bool = False,
    ) -> bool:
        """
        Confirm file operations (read, write, delete)

        Args:
            operation: "read", "write", "delete", or "modify"
            file_path: Path to the file
            backup_created: Whether a backup was created

        Returns:
            True if user confirms, False otherwise
        """
        if self.never_confirm:
            return True

        if self.auto_confirm and operation == "read":
            return True

        segments = [
            OutputSegment(
                f"📁 Confirm {operation} operation",
                OutputType.WARNING if operation == "delete" else OutputType.INFO,
            )
        ]

        segments.append(OutputSegment(f"   File: {file_path}", OutputType.TEXT))

        if backup_created:
            segments.append(
                OutputSegment(
                    "   ✓ Backup created before modification", OutputType.SUCCESS
                )
            )

        if operation == "delete":
            segments.append(
                OutputSegment(
                    "   ⚠️  File will be permanently deleted!", OutputType.ERROR
                )
            )
        elif operation == "write":
            segments.append(
                OutputSegment("   ⚠️  File will be overwritten", OutputType.WARNING)
            )

        segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        segments.append(OutputSegment("   Continue? (y/N): ", OutputType.INFO))

        self.formatter.display_segments(segments)
        response = input().strip()
        return response.lower() in ("y", "yes")

    async def confirm_web_request(
        self,
        url: str,
        method: str = "GET",
        data_size: int = 0,
    ) -> bool:
        """
        Confirm web requests for security

        Args:
            url: URL to request
            method: HTTP method
            data_size: Size of data being sent (for POST requests)

        Returns:
            True if user confirms, False otherwise
        """
        if self.never_confirm:
            return True

        if self.auto_confirm and method == "GET":
            return True

        segments = [
            OutputSegment("🌐 Confirm web request", OutputType.INFO),
            OutputSegment(f"   URL: {url}", OutputType.TEXT),
            OutputSegment(f"   Method: {method}", OutputType.TEXT),
        ]

        if data_size > 0:
            segments.append(
                OutputSegment(f"   Data size: {data_size} bytes", OutputType.TEXT)
            )

        # Security warnings for external requests
        if not self._is_safe_domain(url):
            segments.append(
                OutputSegment(
                    "   ⚠️  External domain - verify this is expected",
                    OutputType.WARNING,
                )
            )

        segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        segments.append(OutputSegment("   Continue? (y/N): ", OutputType.INFO))

        self.formatter.display_segments(segments)
        response = input().strip()
        return response.lower() in ("y", "yes")

    async def confirm_llm_request(
        self,
        prompt_preview: str,
        estimated_tokens: int,
        estimated_cost: float = 0.0,
    ) -> bool:
        """
        Confirm LLM API requests, especially expensive ones

        Args:
            prompt_preview: Preview of the prompt (first 200 chars)
            estimated_tokens: Estimated token usage
            estimated_cost: Estimated cost in USD

        Returns:
            True if user confirms, False otherwise
        """
        if self.never_confirm:
            return True

        # Auto-confirm small, inexpensive requests
        if self.auto_confirm and estimated_tokens < 1000 and estimated_cost < 0.10:
            return True

        segments = [
            OutputSegment("🤖 Confirm LLM request", OutputType.INFO),
            OutputSegment(f"   Prompt preview: {prompt_preview}...", OutputType.TEXT),
            OutputSegment(f"   Estimated tokens: {estimated_tokens}", OutputType.TEXT),
        ]

        if estimated_cost > 0:
            segments.append(
                OutputSegment(
                    f"   Estimated cost: ${estimated_cost:.3f}", OutputType.TEXT
                )
            )

        # Warn about expensive requests
        if estimated_cost > 1.0:
            segments.append(
                OutputSegment(
                    "   ⚠️  This request may be expensive!", OutputType.WARNING
                )
            )
        elif estimated_tokens > 5000:
            segments.append(
                OutputSegment(
                    "   ⚠️  Large token usage - this may take time", OutputType.WARNING
                )
            )

        segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        segments.append(OutputSegment("   Continue? (y/N): ", OutputType.INFO))

        self.formatter.display_segments(segments)
        response = input().strip()
        return response.lower() in ("y", "yes")

    async def confirm_plugin_execution(
        self,
        plugin_name: str,
        plugin_path: str,
        permissions: list[str],
    ) -> bool:
        """
        Confirm plugin execution for security

        Args:
            plugin_name: Name of the plugin
            plugin_path: Path to the plugin file
            permissions: List of permissions the plugin requests

        Returns:
            True if user confirms, False otherwise
        """
        if self.never_confirm:
            return True

        segments = [
            OutputSegment("🔌 Confirm plugin execution", OutputType.WARNING),
            OutputSegment(f"   Plugin: {plugin_name}", OutputType.TEXT),
            OutputSegment(f"   Path: {plugin_path}", OutputType.TEXT),
        ]

        if permissions:
            segments.append(OutputSegment("   Requested permissions:", OutputType.TEXT))
            for permission in permissions:
                segments.append(
                    OutputSegment(f"     • {permission}", OutputType.WARNING)
                )

        segments.append(
            OutputSegment(
                "   ⚠️  Only run plugins from trusted sources!",
                OutputType.ERROR,
            )
        )

        segments.append(OutputSegment("", OutputType.TEXT))  # Empty line
        segments.append(OutputSegment("   Continue? (y/N): ", OutputType.INFO))

        self.formatter.display_segments(segments)
        response = input().strip()
        return response.lower() in ("y", "yes")

    def show_progress_confirmation(
        self,
        operation: str,
        current: int,
        total: int,
        allow_cancel: bool = True,
    ) -> bool:
        """
        Show progress and allow cancellation during long operations

        Args:
            operation: Description of the operation
            current: Current progress
            total: Total items/steps
            allow_cancel: Whether to allow cancellation

        Returns:
            True to continue, False to cancel
        """
        if not allow_cancel:
            return True

        percentage = (current / total) * 100 if total > 0 else 0

        # Only show confirmation every 10% or every 10 items
        if current % max(1, total // 10) != 0 and current % 10 != 0:
            return True

        segments = [
            OutputSegment(
                f"🔄 {operation} - {current}/{total} ({percentage:.1f}%)",
                OutputType.INFO,
            )
        ]

        if allow_cancel:
            segments.append(
                OutputSegment(
                    "   Press 'c' to cancel, any other key to continue: ",
                    OutputType.INFO,
                )
            )

            self.formatter.display_segments(segments)

            # Non-blocking input check
            try:
                import select
                import termios
                import tty

                if select.select([sys.stdin], [], [], 0.1)[0]:
                    old_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.cbreak(sys.stdin.fileno())
                        response = sys.stdin.read(1)
                        if response.lower() == "c":
                            return False
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            except Exception:
                # Fallback for systems without proper terminal support
                pass
        else:
            self.formatter.display_segments(segments)

        return True

    def _sanitize_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Sanitize parameters to hide sensitive information"""
        sanitized = {}
        sensitive_keys = {
            "password",
            "pass",
            "pwd",
            "secret",
            "key",
            "token",
            "api_key",
            "auth",
            "credential",
            "private",
        }

        for key, value in parameters.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = "[HIDDEN]"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = f"{value[:50]}... ({len(value)} chars)"
            else:
                sanitized[key] = value

        return sanitized

    def _is_safe_domain(self, url: str) -> bool:
        """Check if URL is from a safe/known domain"""
        safe_domains = {
            "localhost",
            "127.0.0.1",
            "::1",
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "stackoverflow.com",
            "openai.com",
            "anthropic.com",
            "google.com",
            "microsoft.com",
            "mozilla.org",
        }

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            return any(
                domain == safe_domain or domain.endswith(f".{safe_domain}")
                for safe_domain in safe_domains
            )
        except Exception:
            return False
