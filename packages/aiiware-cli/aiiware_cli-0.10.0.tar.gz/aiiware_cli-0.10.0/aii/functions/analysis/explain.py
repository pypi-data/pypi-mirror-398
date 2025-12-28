# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Explain Function - Explain concepts, technologies, or topics."""


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


class ExplainFunction(FunctionPlugin):
    """Explain concepts, technologies, or topics (NOT shell commands - use explain_command for those)"""

    @property
    def name(self) -> str:
        return "explain"

    @property
    def description(self) -> str:
        return "Explain concepts, technologies, or topics (e.g., machine learning, kubernetes, DNS). DO NOT use for shell commands - use explain_command instead."

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "topic": ParameterSchema(
                name="topic",
                type="string",
                required=True,
                description="The concept, technology, or topic to explain",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Output language for the explanation (e.g., 'English', 'Chinese', 'Spanish', 'French')",
                default="English",
            ),
            "audience": ParameterSchema(
                name="audience",
                type="string",
                required=False,
                description="Target audience level",
                choices=["beginner", "intermediate", "advanced", "expert"],
                default="intermediate",
            ),
            "include_examples": ParameterSchema(
                name="include_examples",
                type="boolean",
                required=False,
                description="Include practical examples",
                default=True,
            ),
            "max_words": ParameterSchema(
                name="max_words",
                type="integer",
                required=False,
                description="Maximum word count for explanation (e.g., 50, 100, 200)",
            ),
            "brevity": ParameterSchema(
                name="brevity",
                type="string",
                required=False,
                description="Level of brevity for explanation",
                choices=["brief", "concise", "standard", "detailed", "comprehensive"],
                default="standard",
            ),
            "format_style": ParameterSchema(
                name="format_style",
                type="string",
                required=False,
                description="Output format style",
                choices=["paragraph", "bullet_points", "structured", "definition", "summary"],
                default="structured",
            ),
            "constraints": ParameterSchema(
                name="constraints",
                type="string",
                required=False,
                description="Additional constraints or requirements (e.g., 'within 50 words', 'one sentence', 'no technical jargon')",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Explain should show clean output by default (just the explanation)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Explain supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for explanations"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute explanation"""
        topic = parameters["topic"]
        language = parameters.get("language", "English")
        audience = parameters.get("audience", "intermediate")
        include_examples = parameters.get("include_examples", True)
        max_words = parameters.get("max_words")
        brevity = parameters.get("brevity", "standard")
        format_style = parameters.get("format_style", "structured")
        constraints = parameters.get("constraints")

        # v0.6.0 FIX: Detect word limits directly from topic if not already set
        # This handles cases where pattern matching bypasses parameter enhancement
        if max_words is None:
            import re
            word_limit_patterns = [
                r"in (\d+) words?",
                r"within (\d+) words?",
                r"(\d+) words? or less",
                r"no more than (\d+) words?",
                r"(\d+) words? max",
                r"(\d+)-word",
            ]
            for pattern in word_limit_patterns:
                match = re.search(pattern, topic, re.IGNORECASE)
                if match:
                    max_words = int(match.group(1))
                    # Also adjust format for strict word limits
                    if max_words <= 200:
                        format_style = "paragraph"
                        brevity = "brief" if max_words <= 50 else "concise"
                    break

        try:
            explanation, usage = await self._generate_explanation(
                topic,
                language,
                audience,
                include_examples,
                max_words,
                brevity,
                format_style,
                constraints,
                context.llm_provider,
                context.web_client,
            )

            # Count actual words for verification
            actual_word_count = len(explanation.split())

            # Create reasoning for THINKING mode
            reasoning_parts = [f"Explaining '{topic}' for {audience} audience"]
            if max_words:
                reasoning_parts.append(f"limited to {max_words} words")
            if constraints:
                reasoning_parts.append(f"with constraints: {constraints}")
            reasoning_parts.append(f"using {brevity} brevity in {format_style} format")

            reasoning = ", ".join(reasoning_parts) + "."

            return ExecutionResult(
                success=True,
                message=f"# Explanation: {topic}\n\n{explanation}",
                data={
                    "clean_output": explanation,  # For CLEAN mode
                    "topic": topic,
                    "language": language,
                    "audience": audience,
                    "explanation": explanation,
                    "reasoning": reasoning,  # For THINKING/VERBOSE modes
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "include_examples": include_examples,
                    "max_words": max_words,
                    "brevity": brevity,
                    "format_style": format_style,
                    "constraints": constraints,
                    "word_count": actual_word_count,
                    "truncated": usage.get("truncated", False),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Explanation failed: {str(e)}"
            )

    async def _generate_explanation(
        self,
        topic: str,
        language: str,
        audience: str,
        include_examples: bool,
        max_words: int = None,
        brevity: str = "standard",
        format_style: str = "structured",
        constraints: str = None,
        llm_provider: Any = None,
        web_client: Any = None,
    ) -> str:
        """Generate constraint-aware explanation"""

        # Build constraint-aware prompt with strong emphasis on limits
        prompt_parts = []

        # CRITICAL CONSTRAINTS FIRST - Language and Word Count
        if language and language.lower() != "english":
            prompt_parts.append(f"🚨 CRITICAL CONSTRAINT #1: Output language MUST be {language} (NOT English, NOT any other language)")
            prompt_parts.append(f"📝 Your ENTIRE explanation must be written in {language}. Every single word must be in {language}.")

        if max_words:
            prompt_parts.append(f"🚨 CRITICAL CONSTRAINT #2: Your explanation must be EXACTLY {max_words} words or less. This is a HARD LIMIT.")
            prompt_parts.append(f"📊 Word count requirement: {max_words} words maximum. You MUST count your words carefully.")

            # STRICT: For tight word limits, FORCE simple format (override format_style)
            if max_words <= 200:
                prompt_parts.append(f"🚫 CRITICAL FORMAT RULE: Write as a SINGLE CONTINUOUS PARAGRAPH. NO headings, NO sections, NO bullet points, NO numbered lists.")
                prompt_parts.append(f"✏️ Format: One flowing paragraph only. Start directly with the explanation.")
                format_style = "paragraph"  # Override to prevent structured output

        # Brevity instructions
        brevity_instructions = {
            "brief": "Provide only the most essential information in the shortest form possible. Focus on core definition and key points only.",
            "concise": "Be concise and focused, avoiding unnecessary details. Cover main concepts efficiently.",
            "standard": "Provide balanced coverage with clear explanations and key details.",
            "detailed": "Provide comprehensive coverage with thorough explanations and context.",
            "comprehensive": "Include extensive details, examples, and related concepts with full context."
        }

        if brevity in brevity_instructions:
            prompt_parts.append(f"📝 Brevity level: {brevity_instructions[brevity]}")

        # Format instructions
        format_instructions = {
            "bullet_points": "Format as clear bullet points with short, direct statements.",
            "definition": "Provide a clear, concise definition in paragraph form. Focus on what it is and why it matters.",
            "summary": "Write as a summary paragraph covering the essential information.",
            "paragraph": "Write in flowing paragraph form with smooth transitions.",
            "structured": "Use clear headings and organized sections for easy reading."
        }

        if format_style in format_instructions:
            prompt_parts.append(f"📋 Format: {format_instructions[format_style]}")

        # Additional constraints
        if constraints:
            prompt_parts.append(f"⚠️ Additional requirements: {constraints}")

        # Audience guidance
        audience_guidance = {
            "beginner": "Assume no prior knowledge. Use simple terms and analogies. Avoid technical jargon.",
            "intermediate": "Assume basic knowledge. Include technical details but explain concepts clearly.",
            "advanced": "Assume good technical background. Focus on implementation details and advanced concepts.",
            "expert": "Assume deep expertise. Focus on edge cases, optimization, and cutting-edge developments.",
        }

        guidance = audience_guidance.get(audience, audience_guidance["intermediate"])
        prompt_parts.append(f"🎯 Audience: {audience} level. {guidance}")

        # Core explanation request
        prompt_parts.append(f"📖 Topic to explain: {topic}")

        # Example handling based on constraints
        if include_examples:
            if max_words and max_words <= 50:
                prompt_parts.append("Examples: Mention only if absolutely essential and word count allows.")
            elif max_words and max_words <= 100:
                prompt_parts.append("Examples: Include one brief example if word count allows.")
            else:
                prompt_parts.append("Examples: Include relevant, practical examples.")
        else:
            prompt_parts.append("Examples: Do not include examples.")

        # Web context (if available)
        context_info = ""
        if web_client and not max_words:  # Skip web search for very constrained responses
            try:
                search_results = await web_client.search(
                    f"{topic} explanation tutorial", num_results=2
                )
                if search_results:
                    context_info = "\n\n🌐 Current information:\n"
                    for result in search_results[:2]:
                        context_info += f"- {result.title}: {result.snippet}\n"
                    prompt_parts.append(context_info)
            except Exception:
                pass

        # Structure guidance based on format and constraints
        if format_style == "definition":
            prompt_parts.append("\n🏗️ Structure: Provide a clear definition followed by brief explanation of significance.")
        elif format_style == "bullet_points":
            prompt_parts.append("\n🏗️ Structure: Use bullet points to cover key aspects: definition, how it works, importance.")
        elif format_style == "summary":
            prompt_parts.append("\n🏗️ Structure: Write a cohesive summary covering what it is, how it works, and why it matters.")
        elif not max_words or max_words > 150:
            # Only use full structure for longer explanations
            prompt_parts.append(f"""
🏗️ Structure your explanation as follows:
1. **Overview**: What is {topic}?
2. **Key Concepts**: Core principles and terminology
3. **How It Works**: Technical details appropriate for {audience} level
{'4. **Examples**: Practical examples and use cases' if include_examples else ''}
5. **Applications**: Real-world uses and importance
{'6. **Further Learning**: Next steps or related topics' if not max_words or max_words > 200 else ''}""")

        # CONSTRAINT REINFORCEMENT for language and word limits
        if language and language.lower() != "english":
            prompt_parts.append(f"\n🔢 FINAL REMINDER #1: Write ENTIRELY in {language}. Do not mix languages or use English.")

        if max_words:
            prompt_parts.append(f"\n🔢 FINAL REMINDER #2: Your response must not exceed {max_words} words. Count carefully!")
            prompt_parts.append(f"🎯 If approaching the limit, prioritize: definition → how it works → importance")

            # ABSOLUTE OVERRIDE for strict word limits
            if max_words <= 200:
                prompt_parts.append("\n" + "="*80)
                prompt_parts.append("⚠️ CRITICAL FINAL INSTRUCTION - OVERRIDE ALL PREVIOUS FORMATTING ⚠️")
                prompt_parts.append("="*80)
                prompt_parts.append(f"Write ONLY a single flowing paragraph of {max_words} words maximum.")
                prompt_parts.append("DO NOT use markdown headings (###, ##, #).")
                prompt_parts.append("DO NOT create sections or numbered lists.")
                prompt_parts.append("DO NOT use any structural formatting.")
                prompt_parts.append("START your response DIRECTLY with the first sentence.")
                prompt_parts.append("="*80)

        # Combine all parts
        full_prompt = "\n\n".join(prompt_parts)

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # v0.6.0: DISABLE streaming for strict word limits (≤200)
            # Reason: Streaming shows raw LLM output before post-processing can clean it up
            if max_words and max_words <= 200:
                streaming_callback = None

            # Execute LLM request with constraint-aware prompt
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    full_prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(full_prompt)
                usage = {}

            if result is None:
                return "Failed to generate explanation", usage

            # POST-PROCESSING: Word count validation and intelligent truncation
            result_str = str(result)

            # v0.6.0: For strict word limits (≤200), strip markdown formatting FIRST
            if max_words and max_words <= 200:
                result_str = self._strip_markdown_formatting(result_str)

            word_count = len(result_str.split())
            usage["word_count"] = word_count

            if max_words and word_count > max_words:
                # Attempt intelligent truncation
                # v0.6.0: For strict limits (≤200), use 0% tolerance (hard limit)
                tolerance_percent = 0.0 if max_words <= 200 else 0.1
                truncated = self._intelligent_truncate(result_str, max_words, tolerance_percent)
                usage["truncated"] = True
                usage["original_word_count"] = word_count
                usage["final_word_count"] = len(truncated.split())
                return truncated, usage

            return result_str, usage

        except Exception as e:
            raise RuntimeError(f"Failed to generate explanation: {str(e)}") from e

    def _strip_markdown_formatting(self, text: str) -> str:
        """
        Strip markdown formatting for word-constrained responses.
        Removes headings, horizontal rules, and excessive whitespace.
        Converts to clean flowing text.
        """
        import re

        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()

            # Skip horizontal rules
            if re.match(r'^[-=_*]{3,}$', line):
                continue

            # Remove markdown headings (###, ##, #)
            line = re.sub(r'^#{1,6}\s+', '', line)

            # Skip empty lines
            if not line:
                continue

            cleaned_lines.append(line)

        # Join with single space to create flowing paragraph
        result = ' '.join(cleaned_lines)

        # Clean up excessive spacing
        result = re.sub(r'\s+', ' ', result)

        return result.strip()

    def _intelligent_truncate(self, text: str, max_words: int, tolerance_percent: float = 0.1) -> str:
        """
        Intelligently truncate text to word limit while preserving meaning

        Args:
            text: Text to truncate
            max_words: Maximum word count
            tolerance_percent: Percentage tolerance for natural sentence boundaries (default 10%)
        """
        words = text.split()
        if len(words) <= max_words:
            return text

        # Allow tolerance for natural sentence boundaries
        tolerance = int(max_words * tolerance_percent)
        max_allowed = max_words + tolerance

        # If within tolerance, check if we're at a natural break
        if len(words) <= max_allowed:
            # Check if text ends with sentence-ending punctuation
            if text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
                return text

        # Need to truncate - try to do so at sentence boundaries
        # Handle both English (.) and CJK (。) sentence endings
        sentence_endings = ['. ', '! ', '? ', '。', '！', '？']

        # Find sentence boundaries within word limit
        truncated_sentences = []
        word_count = 0
        current_sentence = []

        for i, word in enumerate(words):
            current_sentence.append(word)
            word_count += 1

            # Check if this word ends a sentence
            is_sentence_end = any(word.endswith(ending.strip()) for ending in sentence_endings)

            if is_sentence_end and word_count <= max_words:
                # Complete sentence within limit - keep it
                truncated_sentences.extend(current_sentence)
                current_sentence = []
            elif word_count > max_words:
                # Exceeded limit
                if truncated_sentences:
                    # We have complete sentences, stop here
                    break
                else:
                    # No complete sentences yet, truncate at word limit
                    truncated_text = ' '.join(words[:max_words])
                    # Add ellipsis if not ending with punctuation
                    if not truncated_text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
                        truncated_text += '...'
                    return truncated_text

        # Join preserved sentences
        if truncated_sentences:
            result = ' '.join(truncated_sentences)
            return result

        # Fallback: hard truncate at max_words
        truncated_text = ' '.join(words[:max_words])
        if not truncated_text.rstrip().endswith(('.', '!', '?', '。', '！', '？')):
            truncated_text += '...'
        return truncated_text

    def supports_streaming(self) -> bool:
        """This function supports streaming responses"""
        return True

    def build_prompt(self, parameters: dict[str, Any]) -> str:
        """Build LLM prompt for streaming explanation

        Args:
            parameters: Function parameters

        Returns:
            str: Formatted prompt for LLM
        """
        topic = parameters.get("topic", "")
        detail_level = parameters.get("detail_level", "medium")
        target_audience = parameters.get("target_audience", "general")
        include_examples = parameters.get("include_examples", True)

        # Build explanation prompt
        prompt_parts = [f"Explain the following topic: {topic}"]

        # Detail level
        if detail_level == "brief":
            prompt_parts.append("\nProvide a brief, concise explanation (2-3 paragraphs).")
        elif detail_level == "detailed":
            prompt_parts.append("\nProvide a comprehensive, detailed explanation with examples.")
        else:  # medium
            prompt_parts.append("\nProvide a clear explanation with appropriate depth.")

        # Target audience
        if target_audience != "general":
            prompt_parts.append(f"\nTarget audience: {target_audience}")
            prompt_parts.append(f"Adjust technical language and depth accordingly.")

        # Examples
        if include_examples:
            prompt_parts.append("\nInclude relevant examples to illustrate key concepts.")

        prompt_parts.append("\nBegin your explanation now:")

        return "\n".join(prompt_parts)
