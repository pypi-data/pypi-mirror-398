# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Language Detection Function - Detect the language of input text"""


import re
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class LanguageDetectionFunction(FunctionPlugin):
    """Identify and detect what language text is written in"""

    @property
    def name(self) -> str:
        return "detect_language"

    @property
    def description(self) -> str:
        return """Identify and detect what language a given text is written in.

IMPORTANT: This function ONLY identifies the language name (e.g., 'french', 'spanish', 'japanese').
It does NOT translate the text. For translation, use the 'translate' function instead.

Use this function when the user asks:
- "what language is this"
- "detect the language of [text]"
- "identify language: [text]"
- "which language is this written in"
- "is this written in [language]?"

Do NOT use this if the user wants translation (e.g., "translate to spanish") - use 'translate' function for that.

Returns: Just the language name in lowercase (e.g., "french", "spanish", "chinese")"""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.TRANSLATION

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "text": ParameterSchema(
                name="text",
                type="string",
                required=True,
                description="Text to analyze for language detection",
            )
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Language detection should show clean output by default (just the language name)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Language detection supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False, errors=["LLM provider required for language detection"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Detect language of text"""
        try:
            text = parameters.get("text", "").strip()
            if not text:
                return ExecutionResult(
                    success=False, message="No text provided for language detection"
                )

            # Use LLM for accurate language detection
            prompt = f"""Detect the language of this text and provide confidence score:

Text: "{text}"

Respond in JSON format:
{{
  "language": "language_name",
  "confidence": 0.95,
  "reasoning": "brief explanation"
}}

Common languages: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Russian, Arabic"""

            # Use complete_with_usage for accurate token tracking
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                response = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                response = await context.llm_provider.complete(prompt)
                # Fallback to estimates if usage tracking unavailable
                usage = {
                    "input_tokens": len(prompt.split()) + len(text.split()),
                    "output_tokens": len(response.split()) if response else 0
                }

            # Parse JSON response
            import json

            try:
                result = json.loads(response.strip())
                language = result.get("language", "unknown")
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")
            except json.JSONDecodeError:
                # Fallback to simple detection
                language = self._simple_language_detection(text)
                confidence = 0.7
                reasoning = "Pattern-based detection"

            # Create reasoning for THINKING/VERBOSE modes
            if reasoning:
                # Use LLM-provided reasoning
                thinking_reasoning = f"Detected {language} based on {reasoning.lower()}"
            else:
                thinking_reasoning = f"Detected {language} with {confidence:.0%} confidence based on linguistic patterns and character analysis"

            return ExecutionResult(
                success=True,
                message=f"Detected language: {language} (confidence: {confidence:.0%})",
                data={
                    "clean_output": language,  # For CLEAN mode - just the language name
                    "language": language,
                    "confidence": confidence,
                    "reasoning": thinking_reasoning,  # For THINKING/VERBOSE modes
                    "text_sample": text[:100] + "..." if len(text) > 100 else text,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Language detection failed: {str(e)}"
            )

    def _simple_language_detection(self, text: str) -> str:
        """Fallback simple language detection"""
        text_lower = text.lower()

        # Character-based detection
        if re.search(r"[一-龯]", text):
            return "Chinese"
        elif re.search(r"[ひらがなカタカナ]", text):
            return "Japanese"
        elif re.search(r"[가-힣]", text):
            return "Korean"
        elif re.search(r"[а-яё]", text):
            return "Russian"
        elif re.search(r"[ا-ي]", text):
            return "Arabic"

        # European language patterns
        if re.search(r"[äöüß]", text_lower):
            return "German"
        elif re.search(r"[àâäéèêëïîôùûüÿç]", text_lower):
            return "French"
        elif re.search(r"[áéíñóúü¿¡]", text_lower):
            return "Spanish"

        return "English"  # Default fallback

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming translation

        Args:
            parameters: Function parameters containing text and language info

        Returns:
            str: Formatted prompt for LLM
        """
        text = parameters.get("text", "").strip()
        target_language = parameters.get("target_language", "english")
        source_language = parameters.get("source_language", "auto")
        preserve_formatting = parameters.get("preserve_formatting", True)

        # Build translation prompt
        if source_language == "auto" or source_language == "auto-detect":
            source_info = "from the detected language"
        else:
            source_info = f"from {source_language}"

        formatting_instruction = (
            "Preserve all formatting, structure, and style from the original text."
            if preserve_formatting
            else "Provide a natural translation without preserving specific formatting."
        )

        prompt = f"""Translate the following text {source_info} to {target_language}.

{formatting_instruction}

Text to translate:
{text}

Provide only the translation, no explanations or additional text."""

        return prompt
