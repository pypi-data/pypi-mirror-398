# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Parameter enhancer for code-related functions."""


import re
from typing import Any

from .base_enhancer import BaseEnhancer


class CodeEnhancer(BaseEnhancer):
    """Enhancer for code_generate and code_review functions."""

    @property
    def supported_functions(self) -> list[str]:
        return ["code_generate", "code_review"]

    def enhance(
        self, parameters: dict, user_input: str, context: Any = None
    ) -> dict:
        """Dispatch to specific enhancement method."""
        # Detect which function based on parameters or keywords
        if "specification" in str(parameters) or any(
            kw in user_input.lower() for kw in ["write", "create", "implement", "generate"]
        ):
            return self._enhance_code_generate(parameters, user_input)
        elif "file_path" in str(parameters) or any(
            kw in user_input.lower() for kw in ["review", "analyze", "check", "examine"]
        ):
            return self._enhance_code_review(parameters, user_input)
        return parameters

    def _enhance_code_generate(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for code_generate function."""

        # 1. SPECIFICATION EXTRACTION
        if "specification" not in parameters:
            spec, language = self._extract_specification_and_language(user_input)
            parameters["specification"] = spec
            if language and "language" not in parameters:
                parameters["language"] = language

        # 2. LANGUAGE DETECTION
        if "language" not in parameters or parameters.get("language") in [
            None,
            "",
            "auto",
        ]:
            detected_lang = self._detect_programming_language(user_input)
            if detected_lang:
                parameters["language"] = detected_lang

        # 3. LANGUAGE NORMALIZATION
        parameters["language"] = self._normalize_language(
            parameters.get("language", "auto")
        )

        self.debug(f"Enhanced code_generate parameters: {parameters}")
        return parameters

    def _extract_specification_and_language(
        self, user_input: str
    ) -> tuple[str, str | None]:
        """Extract code specification and detect language."""
        patterns = [
            r"write me an? (\w+) implementation (?:for|of) (.+)",  # "write me a Golang implementation for X"
            r"(?:create|write|implement|generate) (?:a )?(.+) in (\w+)",  # "create X in Python"
            r"(?:create|write|implement|generate) (?:a )?(\w+) (.+)",  # "create Python script"
            r"(?:create|write|implement|generate) (.+)",  # "create edit distance algorithm"
        ]

        for pattern in patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    lang_candidate, spec_candidate = groups
                    if self._is_programming_language(lang_candidate):
                        return spec_candidate, lang_candidate.lower()
                    elif self._is_programming_language(spec_candidate):
                        return lang_candidate, spec_candidate.lower()
                    else:
                        return f"{lang_candidate} {spec_candidate}", None
                else:
                    return groups[0], None

        return user_input, None

    def _detect_programming_language(self, user_input: str) -> str | None:
        """Detect programming language from input."""
        language_patterns = [
            (r"\b(golang|go)\b", "go"),
            (r"\b(python|py)\b", "python"),
            (r"\b(javascript|js)\b", "javascript"),
            (r"\b(typescript|ts)\b", "typescript"),
            (r"\b(java)\b", "java"),
            (r"\b(c\+\+|cpp)\b", "cpp"),
            (r"\b(rust|rs)\b", "rust"),
        ]

        for pattern, lang in language_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                return lang
        return None

    def _is_programming_language(self, text: str) -> bool:
        """Check if text is a programming language name."""
        languages = [
            "golang",
            "go",
            "python",
            "py",
            "javascript",
            "js",
            "typescript",
            "ts",
            "java",
            "c++",
            "cpp",
            "rust",
            "rs",
        ]
        return text.lower() in languages

    def _normalize_language(self, language: str) -> str:
        """Normalize language name to standard format."""
        mapping = {
            "golang": "go",
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
        }

        valid_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "cpp",
            "go",
            "rust",
            "text",
            "auto",
        ]
        normalized = mapping.get(language, language)

        return normalized if normalized in valid_languages else "auto"

    def _enhance_code_review(self, parameters: dict, user_input: str) -> dict:
        """Enhanced parameter mapping for code_review function."""

        # 1. FILE PATH EXTRACTION
        if "file_path" not in parameters:
            file_path = self._extract_file_path(user_input)
            if file_path:
                parameters["file_path"] = file_path

        # 2. FOCUS AREA DETECTION
        if "focus" not in parameters:
            parameters["focus"] = self._detect_focus_area(user_input)

        self.debug(f"Enhanced code_review parameters: {parameters}")
        return parameters

    def _extract_file_path(self, user_input: str) -> str | None:
        """Extract file path from input."""
        path_patterns = [
            r"analyze (?:the )?code in (?:the )?(?:folder|directory) (.+)",
            r"review (?:the )?code in (?:the )?(?:folder|directory) (.+)",
            r"analyze (?:the )?(?:folder|directory) (.+)",
            r"review (?:the )?(?:folder|directory) (.+)",
            r"analyze (?:the )?file (.+)",
            r"review (?:the )?file (.+)",
            r"code review (?:for|of) (.+)",
            r"check (?:the )?code in (.+)",
            r"examine (?:the )?code in (.+)",
        ]

        file_path = self.extract_multiple_patterns(path_patterns, user_input)
        if file_path:
            # Clean up artifacts
            file_path = file_path.replace(" folder", "").replace(" directory", "")
            file_path = file_path.strip('"\'')
            return file_path

        # Fallback: Look for path-like patterns
        candidates = re.findall(
            r"[a-zA-Z_][a-zA-Z0-9_/.-]*[a-zA-Z0-9_]", user_input
        )
        for candidate in candidates:
            if "/" in candidate or any(
                folder in candidate.lower()
                for folder in ["core", "src", "lib", "functions", "utils"]
            ):
                return candidate

        return None

    def _detect_focus_area(self, user_input: str) -> str:
        """Detect review focus area."""
        focus_patterns = {
            r"\b(security|secure|vulnerability|vulnerabilities)\b": "security",
            r"\b(performance|speed|optimize|optimization|efficient)\b": "performance",
            r"\b(style|format|formatting|convention|conventions)\b": "style",
            r"\b(all|everything|complete|comprehensive|full)\b": "all",
        }

        for pattern, focus_value in focus_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                return focus_value

        return "all"
