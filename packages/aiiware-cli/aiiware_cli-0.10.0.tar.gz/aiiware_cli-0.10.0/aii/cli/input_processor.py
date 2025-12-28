# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Input Processor - Basic input sanitization for security"""


import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SanitizedInput:
    """Represents sanitized user input - simplified for LLM-first architecture"""

    raw_input: str
    sanitized_input: str
    is_safe: bool
    validation_errors: list[str]
    length: int

    # Legacy properties for backward compatibility during transition
    @property
    def is_valid(self) -> bool:
        """Alias for is_safe"""
        return self.is_safe

    @property
    def extracted_entities(self) -> dict[str, list]:
        """Empty entities - detection delegated to LLM system"""
        return {"urls": [], "file_paths": [], "commands": []}


class InputProcessor:
    """Basic input sanitization - entity detection delegated to LLM system"""

    def __init__(self) -> None:
        # Simplified - no complex pattern matching needed
        pass

    def sanitize_input(self, raw_input: str) -> SanitizedInput:
        """Sanitize user input for basic security (LLM handles advanced analysis)"""
        if not raw_input or not isinstance(raw_input, str):
            return SanitizedInput(
                raw_input=raw_input or "",
                sanitized_input="",
                is_safe=False,
                validation_errors=["Empty or invalid input"],
                length=0,
            )

        # Basic sanitization only
        sanitized = self._basic_sanitize(raw_input)

        # Basic safety check
        is_safe, errors = self._basic_safety_check(sanitized)

        return SanitizedInput(
            raw_input=raw_input,
            sanitized_input=sanitized,
            is_safe=is_safe,
            validation_errors=errors,
            length=len(sanitized),
        )

    # Legacy methods for backward compatibility - simplified implementations
    def detect_urls(self, input_text: str) -> list[str]:
        """Legacy method - entity detection delegated to LLM system"""
        return []

    def detect_file_paths(self, input_text: str) -> list[str]:
        """Legacy method - entity detection delegated to LLM system"""
        return []

    def detect_commands(self, input_text: str) -> list[str]:
        """Legacy method - entity detection delegated to LLM system"""
        return []

    def validate_safety(self, input_text: str) -> dict[str, Any]:
        """Basic safety validation - advanced assessment delegated to LLM system"""
        sanitized_result = self.sanitize_input(input_text)
        return {
            "is_safe": sanitized_result.is_safe,
            "errors": sanitized_result.validation_errors,
            "warnings": [],
            "length": sanitized_result.length,
        }

    def extract_intent_keywords(self, input_text: str) -> list[str]:
        """Legacy method - intent recognition delegated to LLM system"""
        # Return empty list - LLM system handles this
        return []

    def structure_input(self, input_text: str) -> dict[str, Any]:
        """Legacy method - structure analysis delegated to LLM system"""
        sanitized_result = self.sanitize_input(input_text)
        return {
            "original": input_text,
            "sanitized": sanitized_result.sanitized_input,
            "type": "text",  # LLM determines actual type
            "files": [],
            "urls": [],
            "commands": [],
            "keywords": [],
            "is_valid": sanitized_result.is_safe,
            "errors": sanitized_result.validation_errors,
        }

    def _basic_sanitize(self, raw_input: str) -> str:
        """Basic input sanitization for security - simplified for LLM-first architecture"""
        sanitized = raw_input.strip()

        # Basic length limit
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]

        # Remove null bytes and control characters (except newlines and tabs)
        sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

        return sanitized

    def _basic_safety_check(self, sanitized: str) -> tuple[bool, list[str]]:
        """Basic safety validation - advanced assessment delegated to LLM system"""
        errors = []

        # Check for empty input
        if len(sanitized.strip()) == 0:
            errors.append("Input is empty after sanitization")

        # Check for obvious malicious patterns (very basic)
        dangerous_patterns = [
            r"<script[^>]*>",  # Script tags
            r"javascript:",  # JavaScript URLs
            r"data:text/html",  # Data URLs with HTML
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                errors.append("Input contains potentially dangerous script content")
                break

        is_safe = len(errors) == 0
        return is_safe, errors
