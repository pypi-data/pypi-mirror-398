# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Summarize Function - Summarize documents, articles, or content."""


from pathlib import Path
from typing import Any

from ...cli.status_display import ProgressTracker
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


class SummarizeFunction(FunctionPlugin):
    """Summarize documents, articles, or content"""

    @property
    def name(self) -> str:
        return "summarize"

    @property
    def description(self) -> str:
        return "Summarize documents, articles, or text content"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "content": ParameterSchema(
                name="content",
                type="string",
                required=False,
                description="Text content to summarize (if not using file_path)",
            ),
            "file_path": ParameterSchema(
                name="file_path",
                type="string",
                required=False,
                description="Path to file to summarize (if not using content)",
            ),
            "length": ParameterSchema(
                name="length",
                type="string",
                required=False,
                description="Summary length",
                choices=["brief", "medium", "detailed"],
                default="medium",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                description="Summary format",
                choices=["paragraph", "bullet_points", "structured"],
                default="structured",
            ),
            "language": ParameterSchema(
                name="language",
                type="string",
                required=False,
                description="Output language for the summary (e.g., 'chinese', 'english', 'spanish')",
                choices=["chinese", "english", "spanish", "french", "german", "japanese", "korean", "italian", "portuguese"],
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
        """Summarize should show clean output by default (just the summary)"""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Summarize supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check prerequisites"""
        content = context.parameters.get("content")
        file_path = context.parameters.get("file_path")

        if not content and not file_path:
            return ValidationResult(
                valid=False,
                errors=["Either content or file_path must be provided"],
            )

        if file_path:
            path = Path(file_path)
            if not path.exists():
                return ValidationResult(
                    valid=False, errors=[f"File not found: {file_path}"]
                )

            # Check if this is multimodal content (images, PDFs, videos)
            multimodal_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.mp4', '.mov', '.avi', '.mkv'}
            is_multimodal = path.suffix.lower() in multimodal_extensions

            # Check file size (max 500KB) - only for text files, not multimodal
            if not is_multimodal and path.stat().st_size > 500 * 1024:
                return ValidationResult(
                    valid=False,
                    errors=["File too large for summarization (max 500KB)"],
                )

        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for summarization"],
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute summarization"""
        content = parameters.get("content")
        file_path = parameters.get("file_path")
        length = parameters.get("length", "medium")
        format_type = parameters.get("format", "structured")

        try:
            # Check if file_path is an image/PDF/video (multimodal content)
            is_multimodal = False
            if file_path:
                path = Path(file_path)
                multimodal_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.mp4', '.mov', '.avi', '.mkv'}
                if path.suffix.lower() in multimodal_extensions:
                    is_multimodal = True

            # Handle multimodal content (images, PDFs, videos)
            if is_multimodal and file_path:
                return await self._handle_multimodal_content(
                    file_path, length, format_type, parameters.get("language"), context
                )

            # Get text content (original behavior)
            if file_path and not content:
                path = Path(file_path)
                content = path.read_text(encoding="utf-8")
                source = f"file: {file_path}"
            else:
                source = "provided text"

            if not content:
                return ExecutionResult(success=False, message="No content to summarize")

            # Extract language parameter for language-specific summaries
            language = parameters.get("language")

            summary, usage = await self._generate_summary(
                content, length, format_type, context.llm_provider, language
            )

            # Create reasoning for THINKING mode
            reasoning_parts = [f"Summarizing content from {source}"]
            reasoning_parts.append(f"generating {length} summary in {format_type} format")
            if language:
                reasoning_parts.append(f"outputting in {language}")
            reasoning = ", ".join(reasoning_parts) + "."

            return ExecutionResult(
                success=True,
                message=f"# Summary ({source})\n\n{summary}",
                data={
                    "clean_output": summary,  # For CLEAN mode
                    "summary": summary,
                    "source": source,
                    "length": length,
                    "reasoning": reasoning,  # For THINKING/VERBOSE modes
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "format": format_type,
                    "original_length": len(content),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Summarization failed: {str(e)}"
            )

    async def _generate_summary(
        self, content: str, length: str, format_type: str, llm_provider: Any, language: str = None
    ) -> tuple[str, dict[str, int]]:
        """Generate summary using LLM"""
        length_instructions = {
            "brief": "Create a very concise summary (2-3 sentences)",
            "medium": "Create a balanced summary (1-2 paragraphs)",
            "detailed": "Create a comprehensive summary with key details",
        }

        format_instructions = {
            "paragraph": "Format as flowing paragraphs",
            "bullet_points": "Format as bullet points",
            "structured": "Use structured format with headers and bullet points",
        }

        length_instruction = length_instructions.get(
            length, length_instructions["medium"]
        )
        format_instruction = format_instructions.get(
            format_type, format_instructions["structured"]
        )

        # Truncate content if too long for LLM
        if len(content) > 8000:
            content = content[:8000] + "..."

        # Add language instruction if specified
        language_instruction = ""
        if language:
            language_map = {
                "chinese": "中文 (Chinese)",
                "english": "English",
                "spanish": "Spanish",
                "french": "French",
                "german": "German",
                "japanese": "Japanese",
                "korean": "Korean",
                "italian": "Italian",
                "portuguese": "Portuguese",
            }
            language_name = language_map.get(language.lower(), language)
            language_instruction = f"**CRITICAL REQUIREMENT**: Write the ENTIRE summary in {language_name} ONLY. Do not use English at all"

        # Build requirements list
        requirements = [
            length_instruction,
            format_instruction,
            "Focus on the most important points and key takeaways",
            "Maintain accuracy and don't add information not in the original",
            "Use clear, concise language",
            "If structured format, use markdown headers and bullet points"
        ]

        # Add language instruction if specified
        if language_instruction:
            requirements.insert(0, language_instruction)  # Put language first for emphasis

        requirements_text = "\n".join(f"- {req}" for req in requirements)

        # Special handling for language-specific summaries
        if language:
            prompt = f"""IMPORTANT: You must write the summary in {language_map.get(language.lower(), language)} ONLY. Do not use English.

Summarize the following content in {language_map.get(language.lower(), language)}:

{content}

Requirements:
{requirements_text}

Generate the summary in {language_map.get(language.lower(), language)}:"""
        else:
            prompt = f"""Summarize the following content:

{content}

Requirements:
{requirements_text}

Generate the summary:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate summary",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate summary: {str(e)}") from e

    async def _handle_multimodal_content(
        self, file_path: str, length: str, format_type: str, language: str | None, context: ExecutionContext
    ) -> ExecutionResult:
        """Handle multimodal content (images, PDFs, videos) using vision models"""
        import base64
        import mimetypes
        from ...data.providers.model_catalog import get_model_info

        try:
            path = Path(file_path)
            if not path.exists():
                return ExecutionResult(success=False, message=f"File not found: {file_path}")

            # Validate model supports vision/multimodal
            # Get provider and model from context.llm_provider (respects --model override)
            provider_name = getattr(context.llm_provider, '_underlying_provider_name', None)
            model_name = getattr(context.llm_provider, '_underlying_model_name', None)

            # Fallback to provider_name property if _underlying_provider_name not available
            if not provider_name:
                provider_name = getattr(context.llm_provider, 'provider_name', 'unknown')
            if not model_name:
                model_name = getattr(context.llm_provider, 'model', 'unknown')

            model_info = get_model_info(provider_name, model_name)
            if not model_info:
                return ExecutionResult(
                    success=False,
                    message=f"Model information not found for {provider_name}/{model_name}"
                )

            # Check if model supports image/multimodal modality
            supports_vision = model_info.get("modalities", {}).get("image", False)
            if not supports_vision:
                return ExecutionResult(
                    success=False,
                    message=(
                        f"Model '{model_name}' doesn't support image analysis.\n\n"
                        f"Please use a vision-capable model:\n"
                        f"  • aii --model gpt-4o summarize --attach {file_path}\n"
                        f"  • aii --model claude-sonnet-4-5 summarize --attach {file_path}\n"
                        f"  • aii --model gemini-2.5-flash summarize --attach {file_path}"
                    )
                )

            # Create attachment from file path
            # Read file and encode as base64
            with open(file_path, "rb") as f:
                file_data = f.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Fallback based on extension
                ext = path.suffix.lower()
                mime_map = {
                    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
                    '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
                    '.pdf': 'application/pdf',
                    '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
                    '.mkv': 'video/x-matroska'
                }
                mime_type = mime_map.get(ext, 'application/octet-stream')

            # Determine attachment type
            if mime_type.startswith('image/'):
                att_type = 'image'
            elif mime_type == 'application/pdf':
                att_type = 'pdf'
            elif mime_type.startswith('video/'):
                att_type = 'video'
            else:
                att_type = 'file'

            # Create attachment dict
            attachments = [{
                'type': att_type,
                'data': base64_data,
                'mime_type': mime_type,
                'filename': path.name,
                'size': len(file_data)
            }]

            # Build summarization prompt for visual content
            length_instructions = {
                "brief": "Create a very concise summary (2-3 sentences)",
                "medium": "Create a balanced summary (1-2 paragraphs)",
                "detailed": "Create a comprehensive summary with key details",
            }

            format_instructions = {
                "paragraph": "Format as flowing paragraphs",
                "bullet_points": "Format as bullet points",
                "structured": "Use structured format with headers and bullet points",
            }

            length_instruction = length_instructions.get(length, length_instructions["medium"])
            format_instruction = format_instructions.get(format_type, format_instructions["structured"])

            # Build requirements list
            requirements = [
                length_instruction,
                format_instruction,
                "Focus on the most important visual elements, text, and key information",
                "Describe what you see and extract any text or data",
                "Maintain accuracy based on what's actually present",
                "Use clear, concise language"
            ]

            # Add language instruction if specified
            if language:
                language_map = {
                    "chinese": "中文 (Chinese)",
                    "english": "English",
                    "spanish": "Spanish",
                    "french": "French",
                    "german": "German",
                    "japanese": "Japanese",
                    "korean": "Korean",
                    "italian": "Italian",
                    "portuguese": "Portuguese",
                }
                language_name = language_map.get(language.lower(), language)
                requirements.insert(0, f"**CRITICAL**: Write the ENTIRE summary in {language_name} ONLY")

            requirements_text = "\n".join(f"- {req}" for req in requirements)

            # Determine content type
            file_extension = path.suffix.lower()
            content_type = "image"
            if file_extension == '.pdf':
                content_type = "PDF document"
            elif file_extension in {'.mp4', '.mov', '.avi', '.mkv'}:
                content_type = "video"

            prompt = f"""Analyze and summarize this {content_type}.

Requirements:
{requirements_text}

Generate the summary:"""

            # Call multimodal API using complete_with_usage
            streaming_callback = getattr(context.llm_provider, '_streaming_callback', None)

            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    prompt=prompt,
                    attachments=attachments,
                    on_token=streaming_callback
                )

                summary = llm_response.content
                usage = llm_response.usage or {}
            else:
                # Fallback for providers without complete_with_usage
                return ExecutionResult(
                    success=False,
                    message="Current LLM provider doesn't support multimodal analysis. Please use a vision-capable model (e.g., GPT-4o, Claude Sonnet 4.5, Gemini 2.0)."
                )

            # Create reasoning
            reasoning = f"Analyzing {content_type} from file: {file_path}, generating {length} summary in {format_type} format"
            if language:
                reasoning += f", outputting in {language}"

            return ExecutionResult(
                success=True,
                message=f"# Summary ({content_type}: {path.name})\n\n{summary}",
                data={
                    "clean_output": summary,
                    "summary": summary,
                    "source": f"{content_type}: {file_path}",
                    "length": length,
                    "reasoning": reasoning,
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "format": format_type,
                    "file_type": content_type,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Multimodal summarization failed: {str(e)}"
            )
