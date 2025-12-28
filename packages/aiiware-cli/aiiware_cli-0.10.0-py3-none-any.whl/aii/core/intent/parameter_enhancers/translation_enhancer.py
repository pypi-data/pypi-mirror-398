# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for translation functions."""


import re
from typing import Any

from .base_enhancer import BaseEnhancer


class TranslationEnhancer(BaseEnhancer):
    """Enhancer for translate function."""

    @property
    def supported_functions(self) -> list[str]:
        return ["translate"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Enhance translation parameters."""

        # 1. TEXT EXTRACTION
        if "text" not in parameters:
            text = self._extract_text(user_input)
            if text:
                parameters["text"] = text

        # 2. TARGET LANGUAGE
        if "target_language" not in parameters:
            target_lang = self._extract_target_language(user_input)
            if target_lang:
                parameters["target_language"] = target_lang

        # 3. SOURCE LANGUAGE
        if "source_language" not in parameters:
            source_lang = self._extract_source_language(user_input)
            if source_lang:
                parameters["source_language"] = source_lang

        self.debug(f"Enhanced translate parameters: {parameters}")
        return parameters

    def _extract_text(self, user_input: str) -> str | None:
        """Extract text to translate."""
        patterns = [
            r"translate\s+this\s+to\s+\w+:\s*[\"'](.+?)[\"']",
            r"translate\s+this\s+to\s+\w+:\s*(.+)$",
            r"translate\s+[\"'](.+?)[\"']\s+to\s+\w+",
            r"translate\s+(.+?)\s+to\s+\w+",
            r"translate\s+[\"'](.+?)[\"']",
            r"translate:\s*(.+)$",
            r"translate\s+(.+)$",
        ]

        text = self.extract_multiple_patterns(patterns, user_input)
        if text:
            text = text.strip('"\'')
            # Remove trailing period from short texts
            if text.endswith(".") and len(text) < 50:
                text = text.rstrip(".")
        return text

    def _extract_target_language(self, user_input: str) -> str | None:
        """Extract target language."""
        patterns = {
            r"to\s+spanish": "spanish",
            r"to\s+french": "french",
            r"to\s+german": "german",
            r"to\s+english": "english",
            r"to\s+chinese": "chinese",
            r"to\s+japanese": "japanese",
            r"to\s+korean": "korean",
            r"to\s+italian": "italian",
            r"to\s+portuguese": "portuguese",
            r"to\s+russian": "russian",
            r"to\s+arabic": "arabic",
            r"in\s+spanish": "spanish",
            r"in\s+french": "french",
            r"in\s+german": "german",
            r"in\s+english": "english",
            r"in\s+chinese": "chinese",
        }

        for pattern, language in patterns.items():
            if re.search(pattern, user_input.lower()):
                return language
        return None

    def _extract_source_language(self, user_input: str) -> str | None:
        """Extract source language."""
        patterns = {
            r"from\s+spanish": "spanish",
            r"from\s+french": "french",
            r"from\s+german": "german",
            r"from\s+english": "english",
            r"from\s+chinese": "chinese",
            r"from\s+japanese": "japanese",
            r"from\s+korean": "korean",
        }

        for pattern, language in patterns.items():
            if re.search(pattern, user_input.lower()):
                return language
        return None
