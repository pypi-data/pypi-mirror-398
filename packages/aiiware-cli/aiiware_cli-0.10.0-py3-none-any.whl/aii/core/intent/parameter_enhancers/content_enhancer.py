# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for content generation functions."""


import re
from typing import Any

from .base_enhancer import BaseEnhancer


class ContentEnhancer(BaseEnhancer):
    """Enhancer for explain, summarize, and email generation."""

    @property
    def supported_functions(self) -> list[str]:
        return ["explain", "summarize", "generate_email"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Dispatch to specific enhancement method."""
        user_lower = user_input.lower()
        params_str = str(parameters).lower()

        # Check for email first (most specific)
        if "email" in user_lower or "purpose" in params_str or "recipient" in params_str:
            return self._enhance_email(parameters, user_input)
        # Then summarize
        elif "summarize" in user_lower or "summary" in user_lower or ("content" in params_str and "content" in parameters):
            return self._enhance_summarize(parameters, user_input)
        # Then explain (most general)
        elif "explain" in user_lower or "topic" in params_str or "concept" in params_str:
            return self._enhance_explain(parameters, user_input)

        return parameters

    def _enhance_explain(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for explain function."""

        # 0. PARAMETER NAME NORMALIZATION
        parameters = self.normalize_parameter(parameters, "concept", "topic")

        # 1. WORD LIMIT DETECTION
        word_limit = self._detect_word_limit(user_input)
        if word_limit:
            parameters["max_words"] = word_limit
            parameters["brevity"] = self._word_limit_to_brevity(word_limit)
            if word_limit <= 200:
                parameters["format_style"] = "paragraph"

        # 2. BREVITY INDICATORS
        if "brevity" not in parameters:
            brevity = self._detect_brevity_level(user_input)
            if brevity:
                parameters["brevity"] = brevity

        # 3. FORMAT CONSTRAINTS
        format_style = self._detect_format_style(user_input)
        if format_style:
            parameters["format_style"] = format_style

        # 4. SPECIAL CONSTRAINTS
        constraints = self._extract_constraints(user_input)
        if constraints:
            parameters["constraints"] = "; ".join(constraints)

        # 5. EXAMPLE HANDLING
        if re.search(
            r"\b(without examples|no examples|skip examples)\b", user_input.lower()
        ):
            parameters["include_examples"] = False

        self.debug(f"Enhanced explain parameters: {parameters}")
        return parameters

    def _detect_word_limit(self, text: str) -> int | None:
        """Detect word limit from text."""
        patterns = [
            r"in (\d+) words?",  # "in 50 words"
            r"within (\d+) words?",
            r"in (\d+) words? or less",
            r"no more than (\d+) words?",
            r"(\d+) words? max",
            r"(\d+)-word explanation",
            r"limit to (\d+) words?",
            r"under (\d+) words?",
            r"maximum (\d+) words?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return int(match.group(1))
        return None

    def _word_limit_to_brevity(self, word_count: int) -> str:
        """Map word count to brevity level."""
        if word_count <= 25:
            return "brief"
        elif word_count <= 75:
            return "concise"
        elif word_count <= 150:
            return "standard"
        else:
            return "detailed"

    def _detect_brevity_level(self, text: str) -> str | None:
        """Detect brevity level from text."""
        patterns = [
            (r"\b(brief|briefly|short|shortly|quick|quickly)\b", "brief"),
            (r"\b(concise|concisely|succinct|terse)\b", "concise"),
            (
                r"\b(extensive|exhaustive|comprehensive|complete|full)\b",
                "comprehensive",
            ),
            (r"\b(detailed|thorough|in-depth)\b", "detailed"),
        ]

        for pattern, level in patterns:
            if re.search(pattern, text.lower()):
                return level
        return None

    def _detect_format_style(self, text: str) -> str | None:
        """Detect format style from text."""
        patterns = {
            r"\b(bullet points?|list|bulleted|points)\b": "bullet_points",
            r"\b(one sentence|single sentence|definition only)\b": "definition",
            r"\b(summary|summarize)\b": "summary",
            r"\b(paragraph|prose)\b": "paragraph",
        }

        for pattern, style in patterns.items():
            if re.search(pattern, text.lower()):
                return style
        return None

    def _extract_constraints(self, text: str) -> list[str]:
        """Extract special constraints from text."""
        constraint_indicators = [
            r"(no|without) (technical jargon|jargon|technical terms)",
            r"(simple language|plain english|easy to understand)",
            r"(one sentence|single sentence)",
            r"(definition only|just the definition)",
            r"(without examples|no examples)",
        ]

        constraints = []
        for pattern in constraint_indicators:
            match = re.search(pattern, text.lower())
            if match:
                constraints.append(match.group())

        return constraints

    def _enhance_summarize(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for summarize function."""

        # 1. CONTENT EXTRACTION
        if "content" not in parameters:
            content = self._extract_summary_content(user_input)
            if content:
                parameters["content"] = content

        # 2. LANGUAGE PREFERENCE
        language = self._detect_language_preference(user_input)
        if language:
            parameters["language"] = language

        # 3. LENGTH/FORMAT PREFERENCES
        length_format = self._detect_summary_length_format(user_input)
        if length_format:
            for key, value in length_format.items():
                parameters[key] = value

        self.debug(f"Enhanced summarize parameters: {parameters}")
        return parameters

    def _extract_summary_content(self, user_input: str) -> str | None:
        """Extract content to summarize."""
        patterns = [
            r"summarize\s+this\s+article\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+text\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+in\s+\w+:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+article:\s*[\"'](.+?)[\"']",
            r"summarize\s+this\s+text:\s*[\"'](.+?)[\"']",
            r"summarize\s+this:\s*[\"'](.+?)[\"']",
            r"summarize\s+[\"'](.+?)[\"']",
            r"create\s+(?:a\s+)?summary\s+of\s+this:\s*(.+?)(?:\.\s+output|\.\s+write|\.$|$)",
            r"summarize\s+(.+)",
        ]

        content = self.extract_multiple_patterns(patterns, user_input)
        if content:
            content = content.strip('"\'')
            content = content.replace("\\", "")
        return content

    def _detect_language_preference(self, text: str) -> str | None:
        """Detect output language preference."""
        patterns = {
            r"in\s+chinese": "chinese",
            r"in\s+english": "english",
            r"in\s+spanish": "spanish",
            r"output.*in\s+chinese\s+language": "chinese",
            r"用中文": "chinese",
            r"用英文": "english",
        }

        for pattern, language in patterns.items():
            if re.search(pattern, text.lower()):
                return language
        return None

    def _detect_summary_length_format(self, text: str) -> dict:
        """Detect summary length and format preferences."""
        result = {}

        patterns = {
            r"(?:brief|short|concise)": {"length": "brief"},
            r"(?:long|detailed|comprehensive|in-depth)": {"length": "detailed"},
            r"(?:bullet|bullets|bullet points|list)": {"format": "bullet_points"},
            r"(?:executive|executive summary)": {"format": "executive"},
        }

        for pattern, value in patterns.items():
            if re.search(pattern, text.lower()):
                result.update(value)

        return result

    def _enhance_email(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for generate_email function."""

        # 1. PURPOSE EXTRACTION
        purpose = self._extract_email_purpose(user_input)
        if purpose:
            parameters["purpose"] = purpose

        # 2. RECIPIENT TYPE DETECTION
        recipient_type = self._detect_recipient_type(user_input)
        if recipient_type:
            parameters["recipient_type"] = recipient_type

        # 3. TONE DETECTION
        tone = self._detect_email_tone(user_input)
        if tone:
            parameters["tone"] = tone

        self.debug(f"Enhanced email parameters: {parameters}")
        return parameters

    def _extract_email_purpose(self, user_input: str) -> str:
        """Extract email purpose from input."""
        patterns = [
            r"write (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"generate (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"create (?:a |an )?(?:professional )?email (declining|accepting|about|regarding|for|to) (.+)",
            r"write (?:a |an )?(?:professional )?email (.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return f"{groups[0]} {groups[1]}".strip()
                else:
                    return groups[0].strip()

        return user_input.strip('"\'.,!?')

    def _detect_recipient_type(self, text: str) -> str:
        """Detect email recipient type."""
        patterns = {
            "client": ["client", "customer"],
            "manager": ["manager", "supervisor", "boss"],
            "team": ["team", "colleagues", "everyone"],
            "external": ["external", "vendor", "partner"],
        }

        text_lower = text.lower()
        for rec_type, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return rec_type

        return "colleague"

    def _detect_email_tone(self, text: str) -> str:
        """Detect email tone."""
        patterns = {
            "formal": ["formal", "official"],
            "friendly": ["friendly", "casual", "warm"],
            "urgent": ["urgent", "asap", "immediate", "quickly"],
        }

        text_lower = text.lower()
        for tone_type, keywords in patterns.items():
            if any(keyword in text_lower for keyword in keywords):
                return tone_type

        return "professional"
