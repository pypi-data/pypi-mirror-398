# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Pydantic AI-based LLM Provider - Modern agent framework integration"""


import os
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional

from pydantic_ai import Agent
from pydantic_ai.models import Model, infer_model

from .llm_provider import LLMProvider, LLMResponse
from aii.config.manager import ConfigManager

# Debug mode flag
DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")

# v0.10.0: Vision-capable models (synced with llm-models.catalog.json)
VISION_MODELS = {
    # OpenAI models with vision (from catalog)
    "gpt-5.1",          # Full multimodal (text, image, pdf, audio, video)
    "gpt-5-mini",       # Full multimodal
    "gpt-5-nano",       # Full multimodal
    "gpt-4o",           # Full multimodal
    "gpt-4o-mini",      # Full multimodal
    "gpt-4.1",          # Vision + PDF only (no audio/video)
    "gpt-4.1-mini",     # Vision + PDF only
    "gpt-4.1-nano",     # Vision + PDF only
    # OpenAI legacy models (not in catalog but still supported)
    "gpt-4o-2024-11-20",
    "gpt-4o-2024-08-06",
    "gpt-4o-2024-05-13",
    "gpt-4o-mini-2024-07-18",
    "gpt-4-turbo",
    "gpt-4-turbo-2024-04-09",
    "gpt-4-vision-preview",

    # Anthropic Claude models with vision (from catalog)
    "claude-sonnet-4-5",  # Vision + PDF (no audio/video)
    "claude-sonnet-4",    # Vision + PDF
    "claude-haiku-4-5",   # Vision + PDF
    "claude-opus-4-1",    # Vision + PDF
    "claude-opus-4",      # Vision + PDF
    # Anthropic legacy models (not in catalog but still supported)
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-latest",
    "claude-3-5-sonnet",
    "claude-3-opus-20240229",
    "claude-3-opus",
    "claude-3-sonnet-20240229",
    "claude-3-sonnet",
    "claude-3-haiku-20240307",
    "claude-3-haiku",

    # Google Gemini models with vision (from catalog)
    "gemini-3-pro-preview",  # Full multimodal (text, image, pdf, audio, video)
    "gemini-2.5-pro",        # Full multimodal
    "gemini-2.5-flash",      # Image + audio + video (NO PDF!)
    # Gemini legacy models (not in catalog but still supported)
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",
    "gemini-1.5-flash",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash-8b",

    # DeepSeek models with vision (from catalog)
    "deepseek-chat",  # Full multimodal (V3)
    # Note: deepseek-coder and deepseek-reasoner are text-only
}

# Vision token estimation per image (provider-specific)
VISION_TOKENS_PER_IMAGE = {
    "anthropic": 1600,  # Claude: ~1600 tokens/image
    "openai": 765,      # GPT-4o: ~765 tokens high detail
    "google": 258,      # Gemini: ~258 tokens/image
    "gemini": 258       # Gemini (alternative name): ~258 tokens/image
}


def detect_image_format(base64_data: str) -> str:
    """
    Detect image format from base64 data by checking magic bytes.

    Args:
        base64_data: Base64-encoded image data

    Returns:
        MIME type string (image/png, image/jpeg, image/gif, image/webp)
        Defaults to image/png if unable to detect
    """
    import base64

    try:
        # Decode first few bytes to check magic numbers
        decoded = base64.b64decode(base64_data[:32])

        # Check magic bytes (file signatures)
        if decoded.startswith(b'\x89PNG'):
            return "image/png"
        elif decoded.startswith(b'\xff\xd8\xff'):
            return "image/jpeg"
        elif decoded.startswith(b'GIF87a') or decoded.startswith(b'GIF89a'):
            return "image/gif"
        elif decoded.startswith(b'RIFF') and b'WEBP' in decoded[:16]:
            return "image/webp"
        else:
            # Default to PNG if can't detect
            return "image/png"
    except Exception:
        # If any error, default to PNG
        return "image/png"


@dataclass
class PydanticAIResponse:
    """Enhanced response with Pydantic AI integration"""

    content: str
    model: str
    usage: dict[str, int] = None
    finish_reason: str = "stop"
    run_id: str = None


class PydanticAIProvider(LLMProvider):
    """Pydantic AI-powered LLM provider with modern agent capabilities"""

    def __init__(self, api_key: str, model_name: str = "gpt-4", provider_name: str = None):
        super().__init__(api_key, model_name)
        self._model: Model = None
        self._agent: Agent = None

        # Extract provider and model from model_name (e.g., "anthropic:claude-sonnet-4-5-20250929")
        if provider_name:
            # Provider explicitly provided (preferred method)
            self._underlying_provider_name = provider_name
            # Extract model from model_name if it has a prefix, otherwise use as-is
            if ":" in model_name:
                _, self._underlying_model_name = model_name.split(":", 1)
            else:
                self._underlying_model_name = model_name
        elif ":" in model_name:
            # Provider prefix in model_name (e.g., "anthropic:claude-sonnet-4-5-20250929")
            self._underlying_provider_name, self._underlying_model_name = model_name.split(":", 1)
        else:
            # Fallback for models without provider prefix (shouldn't happen with new code)
            self._underlying_provider_name = "unknown"
            self._underlying_model_name = model_name

        if DEBUG_MODE:
            print(f"DEBUG PydanticAIProvider init: provider_name={provider_name}, model_name={model_name}")
            print(f"DEBUG PydanticAIProvider init: _underlying_provider_name={self._underlying_provider_name}, _underlying_model_name={self._underlying_model_name}")

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Pydantic AI model and agent"""
        try:
            # Try to infer the model from the model name
            try:
                self._model = infer_model(self.model)
                if DEBUG_MODE:
                    print(f"DEBUG _initialize_client: infer_model succeeded for {self.model}")
            except Exception as infer_error:
                # If infer_model fails (e.g., unknown OpenAI-compatible model),
                # pass the model string directly to Agent
                if self.model.startswith("openai:"):
                    if DEBUG_MODE:
                        print(f"DEBUG _initialize_client: infer_model failed, using model string directly: {self.model}")
                    # Agent can accept a string model name directly
                    self._model = self.model
                else:
                    # Re-raise if not an OpenAI model
                    raise infer_error

            # Create a basic agent for text completion
            self._agent = Agent(
                model=self._model,
                system_prompt="You are a helpful AI assistant that provides accurate and concise responses.",
            )

        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Pydantic AI provider: {str(e)}"
            ) from e

    @property
    def provider_name(self) -> str:
        """Get the underlying provider name (e.g., 'anthropic', 'openai')"""
        return self._underlying_provider_name

    @property
    def model_name(self) -> str:
        """Get the underlying model name (e.g., 'claude-sonnet-4-5-20250929')"""
        return self._underlying_model_name

    @property
    def model_info(self) -> str:
        """Get formatted model information"""
        return f"PydanticAI:{self.model}"

    def supports_vision(self) -> bool:
        """Check if the current model supports vision/multimodal input"""
        return self._underlying_model_name in VISION_MODELS

    def estimate_vision_tokens(self, attachments: list[dict[str, Any]]) -> int:
        """
        Estimate token count for vision inputs.

        Args:
            attachments: List of file attachments (images, PDFs)

        Returns:
            Estimated token count for vision inputs
        """
        if not attachments:
            return 0

        # Get tokens per image for this provider
        tokens_per_image = VISION_TOKENS_PER_IMAGE.get(self._underlying_provider_name, 1600)

        total_tokens = 0
        for attachment in attachments:
            att_type = attachment.get("type")
            if att_type == "image":
                total_tokens += tokens_per_image
            elif att_type == "pdf":
                # PDFs are arrays of page images
                data = attachment.get("data", [])
                if isinstance(data, list):
                    total_tokens += len(data) * tokens_per_image

        return total_tokens

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt using Pydantic AI"""
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        try:
            # Run the agent with the prompt
            result = await self._agent.run(prompt)
            return result.output

        except Exception as e:
            raise RuntimeError(f"Pydantic AI completion failed: {str(e)}") from e

    async def _complete_with_streaming(
        self,
        prompt: str,
        on_token: Callable[[str], Awaitable[None]],
        **kwargs
    ):
        """Internal method to complete with streaming support"""
        try:
            # Use Pydantic AI's streaming support
            accumulated_text = ""
            last_content = ""

            async with self._agent.run_stream(prompt) as stream:
                # Iterate over the stream's text chunks
                # Note: stream.stream() may send cumulative text (snapshots) not deltas
                async for text_chunk in stream.stream():
                    if text_chunk:
                        # Check if this is a delta or cumulative
                        if text_chunk.startswith(last_content):
                            # This is cumulative - extract only the new part
                            delta = text_chunk[len(last_content):]
                            if delta:
                                accumulated_text += delta
                                await on_token(delta)  # Await async callback
                            last_content = text_chunk
                        else:
                            # This is a delta
                            accumulated_text += text_chunk
                            await on_token(text_chunk)  # Await async callback
                            last_content += text_chunk

                # StreamedRunResult doesn't need get_final(), just use accumulated text
                # Return the final result
                return type('StreamResult', (), {'output': accumulated_text})()

        except Exception as e:
            # Fallback: if streaming fails, use non-streaming
            if DEBUG_MODE:
                print(f"DEBUG: Streaming failed, falling back to non-streaming: {e}")
            result = await self._agent.run(prompt)
            # Still call on_token with the full response
            await on_token(result.output)  # Await async callback
            return result

    async def _complete_multimodal(
        self,
        prompt: str,
        attachments: list[dict[str, Any]],
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Handle multimodal completion (vision) using underlying Anthropic SDK directly.

        This method bypasses Pydantic AI's Agent abstraction to directly call the Anthropic
        Messages API with vision content blocks.

        Args:
            prompt: Text prompt
            attachments: List of file attachments (images, PDFs)
            on_token: Optional streaming callback
            **kwargs: Additional arguments

        Returns:
            LLMResponse with content and usage information

        Raises:
            ValueError: If model doesn't support vision
            RuntimeError: If API call fails
        """
        # Check if model supports vision
        if not self.supports_vision():
            raise ValueError(
                f"Model '{self._underlying_model_name}' does not support vision. "
                f"Vision-capable models: Claude 3.5 Sonnet, GPT-4o, Gemini 2.5 Pro, etc."
            )

        # Route to provider-specific implementation
        if self._underlying_provider_name == "anthropic":
            return await self._complete_multimodal_anthropic(prompt, attachments, on_token, **kwargs)
        elif self._underlying_provider_name == "openai":
            return await self._complete_multimodal_openai(prompt, attachments, on_token, **kwargs)
        elif self._underlying_provider_name in ("google", "gemini"):
            return await self._complete_multimodal_gemini(prompt, attachments, on_token, **kwargs)
        else:
            raise ValueError(
                f"Multimodal (vision) not supported for provider: {self._underlying_provider_name}. "
                f"Supported providers: anthropic (Claude), openai (GPT-4o), google/gemini (Gemini)"
            )

    async def _complete_multimodal_anthropic(
        self,
        prompt: str,
        attachments: list[dict[str, Any]],
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Handle Anthropic Claude vision API calls"""

        # Import Anthropic SDK
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")

        # Get API key (try ConfigManager first, then environment variables)
        config = ConfigManager()
        api_key = config.get_secret("anthropic_api_key")
        if not api_key:
            # Fallback to environment variable
            api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Anthropic API key not found. Please set one of:\n"
                "  1. anthropic_api_key in ~/.aii/secrets.yaml (preferred)\n"
                "  2. ANTHROPIC_API_KEY environment variable\n"
                "Example: aii config set anthropic_api_key your_key_here"
            )

        client = AsyncAnthropic(api_key=api_key)

        # Build Anthropic-specific content array
        content = []

        # Add attachments first (images/PDFs)
        for attachment in attachments:
            att_type = attachment.get("type")
            mime_type = attachment.get("mime_type", "")
            data = attachment.get("data")

            if att_type == "image":
                # Single image - add as image content block
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": data
                    }
                })
            elif att_type == "pdf":
                # PDF - data is array of base64-encoded page images
                if isinstance(data, list):
                    for page_data in data:
                        # Detect actual image format from base64 data
                        detected_mime = detect_image_format(page_data)
                        content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": detected_mime,  # Auto-detect format
                                "data": page_data
                            }
                        })
                        if DEBUG_MODE:
                            print(f"  📄 PDF page image: {detected_mime}")
                else:
                    if DEBUG_MODE:
                        print(f"⚠️  WARNING: PDF data is not a list, skipping")
            elif att_type == "video":
                # Anthropic doesn't support direct video upload
                # Check if frame extraction is available for this model
                from aii.data.providers.model_catalog import get_model_info
                from aii.utils.video import check_ffmpeg_installed, save_base64_video, enhance_prompt_for_frames
                from aii.utils.video_modes import extract_video_frames_with_mode

                model_info = get_model_info(self._underlying_provider_name, self._underlying_model_name)

                # Check if model supports image analysis (whitelist for frame extraction)
                can_extract_frames = (
                    model_info
                    and model_info.get("modalities", {}).get("image") == True
                    and model_info.get("modalities", {}).get("video") == False
                )

                if can_extract_frames:
                    # Check ffmpeg availability
                    if not check_ffmpeg_installed():
                        raise RuntimeError(
                            "ffmpeg is required for video frame extraction. "
                            "Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu). "
                            "Alternatively, use Gemini 2.5 Pro for native video support."
                        )

                    # Save base64 video to temporary file
                    video_path = None
                    try:
                        video_path = save_base64_video(data, mime_type)

                        # Get video extraction config
                        video_config = config.get_video_extraction_config()

                        # Extract frames using configured mode
                        result = extract_video_frames_with_mode(
                            video_path=video_path,
                            model_name=self._underlying_model_name,
                            input_price_per_million=model_info.get("input_price_per_million", 3.0),
                            mode=video_config["mode"],
                            fps=video_config["fps"],
                            max_frames=video_config["max_frames"],
                            hard_cost_limit=video_config["hard_cost_limit"]
                        )

                        # Show simple user-friendly message (hide technical details unless DEBUG)
                        if not DEBUG_MODE:
                            print(f"📹 Analyzing video ({result.duration:.0f}s)...")
                        # DEBUG mode messages handled inside extract_video_frames_with_mode

                        # Send frames as images
                        for frame_data in result.frames:
                            content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": frame_data
                                }
                            })

                        # Enhance prompt with frame context
                        prompt = enhance_prompt_for_frames(
                            prompt,
                            num_frames=result.num_frames,
                            fps=result.actual_fps
                        )

                    finally:
                        # Clean up temporary file
                        if video_path:
                            try:
                                import os
                                os.unlink(video_path)
                            except Exception:
                                pass  # Ignore cleanup errors

                else:
                    raise RuntimeError(
                        f"{self._underlying_model_name} doesn't support direct video upload or frame extraction. "
                        "Try using Gemini 2.5 Pro instead (native video support)."
                    )

        # Add text prompt after images
        content.append({
            "type": "text",
            "text": prompt
        })

        if DEBUG_MODE:
            print(f"🔍 DEBUG [Anthropic Multimodal]: Built content array with {len(content)} parts")
            for i, part in enumerate(content):
                if part["type"] == "image":
                    print(f"  [{i+1}] Image (base64, {len(part['source']['data'])} chars)")
                else:
                    print(f"  [{i+1}] Text: {part['text'][:50]}...")

        # Call Anthropic Messages API
        try:
            if on_token:
                # Streaming mode
                accumulated_text = ""

                async with client.messages.stream(
                    model=self._underlying_model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": content}]
                ) as stream:
                    async for text in stream.text_stream:
                        accumulated_text += text
                        await on_token(text)

                    # Get final message with usage
                    final_message = await stream.get_final_message()

                    return LLMResponse(
                        content=accumulated_text,
                        model=self._underlying_model_name,
                        usage={
                            "input_tokens": final_message.usage.input_tokens,
                            "output_tokens": final_message.usage.output_tokens,
                            "total_tokens": final_message.usage.input_tokens + final_message.usage.output_tokens
                        },
                        finish_reason="stop"
                    )
            else:
                # Non-streaming mode
                response = await client.messages.create(
                    model=self._underlying_model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": content}]
                )

                return LLMResponse(
                    content=response.content[0].text,
                    model=self._underlying_model_name,
                    usage={
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    finish_reason=response.stop_reason
                )

        except Exception as e:
            raise RuntimeError(f"Anthropic multimodal API call failed: {str(e)}") from e

    async def _complete_multimodal_openai(
        self,
        prompt: str,
        attachments: list[dict[str, Any]],
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Handle OpenAI GPT-4o vision API calls"""

        # Import OpenAI SDK
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Install with: pip install openai")

        # Get API key (try ConfigManager first, then environment variables)
        config = ConfigManager()
        api_key = config.get_secret("openai_api_key")
        if not api_key:
            # Fallback to environment variable
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OpenAI API key not found. Please set one of:\n"
                "  1. openai_api_key in ~/.aii/secrets.yaml (preferred)\n"
                "  2. OPENAI_API_KEY environment variable\n"
                "Example: aii config set openai_api_key your_key_here"
            )

        client = AsyncOpenAI(api_key=api_key)

        # Build OpenAI-specific content array
        content = []

        # Add attachments first (images/PDFs as data URLs)
        for attachment in attachments:
            att_type = attachment.get("type")
            mime_type = attachment.get("mime_type", "image/png")
            data = attachment.get("data")

            if att_type == "image":
                # Single image - add as image_url with data URL
                data_url = f"data:{mime_type};base64,{data}"
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": data_url,
                        "detail": "high"  # High detail for better analysis
                    }
                })
            elif att_type == "video":
                # OpenAI doesn't support direct video upload via API
                # Check if frame extraction is available for this model
                from aii.data.providers.model_catalog import get_model_info
                from aii.utils.video import check_ffmpeg_installed, save_base64_video, enhance_prompt_for_frames
                from aii.utils.video_modes import extract_video_frames_with_mode

                model_info = get_model_info(self._underlying_provider_name, self._underlying_model_name)

                # Check if model supports image analysis (whitelist for frame extraction)
                can_extract_frames = (
                    model_info
                    and model_info.get("modalities", {}).get("image") == True
                    and model_info.get("modalities", {}).get("video") == False
                )

                if can_extract_frames:
                    # Check ffmpeg availability
                    if not check_ffmpeg_installed():
                        raise RuntimeError(
                            "ffmpeg is required for video frame extraction. "
                            "Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu). "
                            "Alternatively, use Gemini 2.5 Pro for native video support."
                        )

                    # Save base64 video to temporary file
                    video_path = None
                    try:
                        video_path = save_base64_video(data, mime_type)

                        # Get video extraction config
                        video_config = config.get_video_extraction_config()

                        # Extract frames using configured mode
                        result = extract_video_frames_with_mode(
                            video_path=video_path,
                            model_name=self._underlying_model_name,
                            input_price_per_million=model_info.get("input_price_per_million", 0.5),
                            mode=video_config["mode"],
                            fps=video_config["fps"],
                            max_frames=video_config["max_frames"],
                            hard_cost_limit=video_config["hard_cost_limit"]
                        )

                        # Show simple user-friendly message (hide technical details unless DEBUG)
                        if not DEBUG_MODE:
                            print(f"📹 Analyzing video ({result.duration:.0f}s)...")
                        # DEBUG mode messages handled inside extract_video_frames_with_mode

                        # Send frames as images
                        for frame_data in result.frames:
                            content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{frame_data}",
                                    "detail": "high"
                                }
                            })

                        # Enhance prompt with frame context
                        prompt = enhance_prompt_for_frames(
                            prompt,
                            num_frames=result.num_frames,
                            fps=result.actual_fps
                        )

                    finally:
                        # Clean up temporary file
                        if video_path:
                            try:
                                import os
                                os.unlink(video_path)
                            except Exception:
                                pass  # Ignore cleanup errors

                else:
                    raise RuntimeError(
                        f"{self._underlying_model_name} doesn't support direct video upload or frame extraction. "
                        "Try using Gemini 2.5 Pro instead (native video support)."
                    )
            elif att_type == "pdf":
                # PDF - data is array of base64-encoded page images
                if isinstance(data, list):
                    for page_data in data:
                        data_url = f"data:image/png;base64,{page_data}"
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url,
                                "detail": "high"
                            }
                        })
                else:
                    if DEBUG_MODE:
                        print(f"⚠️  WARNING: PDF data is not a list, skipping")

        # Add text prompt after images
        content.append({
            "type": "text",
            "text": prompt
        })

        if DEBUG_MODE:
            print(f"🔍 DEBUG [OpenAI Multimodal]: Built content array with {len(content)} parts")
            for i, part in enumerate(content):
                if part["type"] == "image_url":
                    url_preview = part["image_url"]["url"][:60] + "..."
                    print(f"  [{i+1}] Image ({part['image_url']['detail']} detail): {url_preview}")
                else:
                    print(f"  [{i+1}] Text: {part['text'][:50]}...")

        # Call OpenAI Chat Completions API
        try:
            if on_token:
                # Streaming mode
                accumulated_text = ""
                prompt_tokens = 0
                completion_tokens = 0
                chunk_count = 0

                stream = await client.chat.completions.create(
                    model=self._underlying_model_name,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4096,
                    stream=True,
                    stream_options={"include_usage": True}  # Request usage stats in stream
                )

                async for chunk in stream:
                    chunk_count += 1

                    # Debug: Print chunk structure
                    if DEBUG_MODE and chunk_count <= 2:
                        print(f"🔍 DEBUG [OpenAI Chunk #{chunk_count}]: {chunk}")

                    # Process content if available
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            accumulated_text += delta.content
                            await on_token(delta.content)

                    # Capture usage if available (should be in final chunk)
                    if hasattr(chunk, 'usage') and chunk.usage:
                        prompt_tokens = chunk.usage.prompt_tokens
                        completion_tokens = chunk.usage.completion_tokens
                        if DEBUG_MODE:
                            print(f"✅ DEBUG [OpenAI Usage Found]: Chunk #{chunk_count} - prompt={prompt_tokens}, completion={completion_tokens}, total={prompt_tokens + completion_tokens}")
                    elif DEBUG_MODE and chunk_count == 1:
                        print(f"🔍 DEBUG [OpenAI Chunk #{chunk_count}]: No usage field, hasattr={hasattr(chunk, 'usage')}, chunk.usage={getattr(chunk, 'usage', 'N/A')}")

                # Debug: Final summary
                if DEBUG_MODE:
                    print(f"🔍 DEBUG [OpenAI Stream Complete]: Total chunks={chunk_count}, prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}")
                    if prompt_tokens == 0:
                        print(f"⚠️  WARNING: OpenAI streaming did not provide usage data after {chunk_count} chunks")
                        print(f"💡 TIP: Check if OpenAI SDK version supports stream_options parameter")

                return LLMResponse(
                    content=accumulated_text,
                    model=self._underlying_model_name,
                    usage={
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    },
                    finish_reason="stop"
                )
            else:
                # Non-streaming mode
                response = await client.chat.completions.create(
                    model=self._underlying_model_name,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4096
                )

                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=self._underlying_model_name,
                    usage={
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    finish_reason=response.choices[0].finish_reason
                )

        except Exception as e:
            raise RuntimeError(f"OpenAI multimodal API call failed: {str(e)}") from e

    async def _complete_multimodal_gemini(
        self,
        prompt: str,
        attachments: list[dict[str, Any]],
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        **kwargs
    ) -> LLMResponse:
        """Handle Google Gemini multimodal API calls"""

        # Import Google Generative AI SDK
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai")

        # Get API key (try ConfigManager first, then environment variables)
        config = ConfigManager()
        api_key = config.get_secret("gemini_api_key")
        if not api_key:
            # Fallback to environment variables (try both GEMINI_API_KEY and GOOGLE_API_KEY)
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Gemini API key not found. Please set one of:\n"
                "  1. gemini_api_key in ~/.aii/secrets.yaml (preferred)\n"
                "  2. GEMINI_API_KEY environment variable\n"
                "  3. GOOGLE_API_KEY environment variable\n"
                "Example: aii config set gemini_api_key your_key_here"
            )

        # Configure Gemini
        genai.configure(api_key=api_key)

        # Create model
        model = genai.GenerativeModel(self._underlying_model_name)

        # Build Gemini-specific content array (parts)
        parts = []

        # Add attachments first (images/PDFs as inline_data)
        for attachment in attachments:
            att_type = attachment.get("type")
            mime_type = attachment.get("mime_type", "image/png")
            data = attachment.get("data")

            if att_type == "image":
                # Single image - add as inline_data part
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": data  # Base64 string (no data URL prefix)
                    }
                })
            elif att_type == "video":
                # Video - add as inline_data part
                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,  # e.g., "video/mp4"
                        "data": data  # Base64 string
                    }
                })
                if DEBUG_MODE:
                    print(f"  🎬 Video: {mime_type}, {len(data)} chars")
            elif att_type == "pdf":
                # PDF - data is array of base64-encoded page images
                if isinstance(data, list):
                    for page_data in data:
                        # Detect actual image format from base64 data
                        detected_mime = detect_image_format(page_data)
                        parts.append({
                            "inline_data": {
                                "mime_type": detected_mime,  # Auto-detect format
                                "data": page_data
                            }
                        })
                        if DEBUG_MODE:
                            print(f"  📄 PDF page image: {detected_mime}")
                else:
                    if DEBUG_MODE:
                        print(f"⚠️  WARNING: PDF data is not a list, skipping")

        # Add text prompt after images
        parts.append(prompt)

        if DEBUG_MODE:
            print(f"🔍 DEBUG [Gemini Multimodal]: Built parts array with {len(parts)} parts")
            for i, part in enumerate(parts):
                if isinstance(part, dict) and "inline_data" in part:
                    print(f"  [{i+1}] Image (mime: {part['inline_data']['mime_type']}, {len(part['inline_data']['data'])} chars)")
                else:
                    print(f"  [{i+1}] Text: {str(part)[:50]}...")

        # Call Gemini API
        try:
            if on_token:
                # Streaming mode
                accumulated_text = ""

                response = model.generate_content(
                    parts,
                    stream=True
                )

                # Gemini streaming returns chunks with text
                for chunk in response:
                    try:
                        # Try to access chunk.text (may raise ValueError if blocked/empty)
                        chunk_text = chunk.text
                        if chunk_text:
                            accumulated_text += chunk_text
                            await on_token(chunk_text)
                    except (ValueError, AttributeError):
                        # Chunk has no text (safety filter, blocked content, etc.)
                        # Check finish_reason for details
                        if hasattr(chunk, 'candidates') and chunk.candidates:
                            finish_reason = chunk.candidates[0].finish_reason
                            if DEBUG_MODE:
                                print(f"  ⚠️  Gemini chunk blocked: finish_reason={finish_reason}")
                        continue

                # Check if any content was generated
                if not accumulated_text:
                    # No content returned - likely blocked by safety filters
                    finish_reason = "blocked"
                    if hasattr(response, 'candidates') and response.candidates:
                        finish_reason = response.candidates[0].finish_reason.name if hasattr(response.candidates[0], 'finish_reason') else "blocked"

                    error_msg = (
                        f"Gemini returned no content. Finish reason: {finish_reason}. "
                        "This may be due to safety filters, content policy, or unsupported media format. "
                        "Try a different prompt or check if the video format is supported."
                    )
                    raise RuntimeError(error_msg)

                # Get usage metadata (Gemini provides this after streaming completes)
                # Note: response.usage_metadata may not be available during streaming
                try:
                    prompt_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
                    completion_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
                except:
                    # Estimate if not available
                    prompt_tokens = len(prompt.split()) * 2 + self.estimate_vision_tokens(attachments)
                    completion_tokens = len(accumulated_text.split()) * 2

                return LLMResponse(
                    content=accumulated_text,
                    model=self._underlying_model_name,
                    usage={
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    },
                    finish_reason="stop"
                )
            else:
                # Non-streaming mode
                response = model.generate_content(parts)

                # Try to get response text (may be blocked/empty)
                try:
                    response_text = response.text
                except (ValueError, AttributeError) as e:
                    # No content returned - likely blocked by safety filters
                    finish_reason = "blocked"
                    if hasattr(response, 'candidates') and response.candidates:
                        finish_reason = response.candidates[0].finish_reason.name if hasattr(response.candidates[0], 'finish_reason') else "blocked"

                    error_msg = (
                        f"Gemini returned no content. Finish reason: {finish_reason}. "
                        "This may be due to safety filters, content policy, or unsupported media format. "
                        "Try a different prompt or check if the video format is supported."
                    )
                    raise RuntimeError(error_msg) from e

                # Get usage metadata
                try:
                    prompt_tokens = response.usage_metadata.prompt_token_count
                    completion_tokens = response.usage_metadata.candidates_token_count
                except:
                    # Estimate if not available
                    prompt_tokens = len(prompt.split()) * 2 + self.estimate_vision_tokens(attachments)
                    completion_tokens = len(response_text.split()) * 2

                return LLMResponse(
                    content=response_text,
                    model=self._underlying_model_name,
                    usage={
                        "input_tokens": prompt_tokens,
                        "output_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    },
                    finish_reason=response.candidates[0].finish_reason.name if response.candidates else "stop"
                )

        except Exception as e:
            raise RuntimeError(f"Gemini multimodal API call failed: {str(e)}") from e

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], Awaitable[None]]] = None,
        attachments: Optional[list[dict[str, Any]]] = None,  # v0.10.0: Multimodal support
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information using Pydantic AI

        Args:
            prompt: Text prompt
            on_token: Optional streaming callback
            attachments: Optional file attachments for vision models (images, PDFs)
            **kwargs: Additional keyword arguments

        Returns:
            LLMResponse with content and usage information
        """
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        # v0.10.0: Check if this is a multimodal request
        has_attachments = attachments and len(attachments) > 0

        if has_attachments:
            # Multimodal request - use underlying SDK directly (Pydantic AI may not support vision yet)
            return await self._complete_multimodal(prompt, attachments, on_token, **kwargs)

        # Retry configuration for rate limit errors
        max_retries = 3
        base_delay = 2.0  # seconds
        max_delay = 10.0  # seconds

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                # Sanitize prompt to fix Unicode surrogate issues (common with emoji)
                # This handles cases where emojis or special characters cause encoding errors
                sanitized_prompt = prompt.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='replace')

                # Check if streaming is requested and supported
                if on_token is not None:
                    # Use streaming path
                    result = await self._complete_with_streaming(sanitized_prompt, on_token, **kwargs)
                else:
                    # Use non-streaming path
                    result = await self._agent.run(sanitized_prompt)

                # Success - break out of retry loop
                break

            except Exception as e:
                # Check if this is a rate limit error (429)
                error_str = str(e).lower()
                is_rate_limit = (
                    "429" in error_str or
                    "rate limit" in error_str or
                    "overloaded" in error_str or
                    "too many requests" in error_str
                )

                last_error = e

                if is_rate_limit and attempt < max_retries:
                    # Calculate exponential backoff delay
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    if DEBUG_MODE:
                        print(f"⚠️  Rate limit hit (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f}s...")

                    # Wait before retrying
                    import asyncio
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Not a rate limit error, or max retries exceeded - re-raise
                    raise

        # If we get here without a result, we exhausted retries
        if last_error:
            raise last_error

        # Extract usage information from the result
        usage = {}

        # Debug: Check what attributes the result object has
        if DEBUG_MODE:
            print(f"DEBUG result object type: {type(result)}")
            print(f"DEBUG result attributes: {dir(result)}")
            if hasattr(result, "_model_name"):
                print(f"DEBUG result._model_name: {result._model_name}")
            if hasattr(result, "model"):
                print(f"DEBUG result.model: {result.model}")

        # Call the usage() method to get actual usage data
        usage_data = None
        if hasattr(result, "usage"):
            try:
                usage_data = result.usage()  # Call the method!
            except Exception as e:
                # Fallback if usage() method fails
                pass

        if usage_data:
            # Pydantic AI usage structure may vary
            # Use new field names first, fall back to deprecated ones
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)

                if hasattr(usage_data, "input_tokens"):
                    usage["input_tokens"] = usage_data.input_tokens or 0
                elif hasattr(usage_data, "request_tokens"):
                    usage["input_tokens"] = usage_data.request_tokens or 0

                if hasattr(usage_data, "output_tokens"):
                    usage["output_tokens"] = usage_data.output_tokens or 0
                elif hasattr(usage_data, "response_tokens"):
                    usage["output_tokens"] = usage_data.response_tokens or 0

            if hasattr(usage_data, "total_tokens"):
                usage["total_tokens"] = usage_data.total_tokens or 0
            else:
                # Calculate total if not available
                usage["total_tokens"] = usage.get("input_tokens", 0) + usage.get(
                    "output_tokens", 0
                )
        else:
            if DEBUG_MODE: print("DEBUG: Using fallback token estimation")
            # Fallback: estimate token usage
            # Use character-based estimation for better accuracy with CJK languages

            def estimate_tokens(text: str) -> int:
                """
                Estimate tokens for text, handling both space-separated and CJK languages.

                Rules:
                - CJK characters (Chinese, Japanese, Korean): ~1 token per character
                - Space-separated words (English, etc.): ~1.3 tokens per word
                - Mixed text: combine both approaches
                """
                if not text:
                    return 0

                # Count CJK characters (Unicode ranges for Chinese, Japanese, Korean)
                import re
                cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]+')
                cjk_chars = ''.join(cjk_pattern.findall(text))
                cjk_tokens = len(cjk_chars)  # ~1 token per CJK character

                # Remove CJK characters and count remaining words
                non_cjk_text = cjk_pattern.sub(' ', text)
                words = non_cjk_text.split()
                word_tokens = len(words) * 1.3  # ~1.3 tokens per English word

                return int(cjk_tokens + word_tokens)

            input_estimate = estimate_tokens(prompt)
            output_estimate = estimate_tokens(result.output) if isinstance(result.output, str) else 0

            if DEBUG_MODE:
                print(f"DEBUG: Input estimate: {input_estimate} tokens (prompt length: {len(prompt)} chars)")
                print(f"DEBUG: Output estimate: {output_estimate} tokens (output length: {len(result.output) if isinstance(result.output, str) else 0} chars)")

            usage = {
                "input_tokens": int(input_estimate),
                "output_tokens": int(output_estimate),
                "total_tokens": int(input_estimate + output_estimate),
            }
            if DEBUG_MODE: print(f"DEBUG: Final estimated usage: {usage}")

        # Return LLMResponse (for both actual usage and estimated usage paths)
        if DEBUG_MODE:
            print(f"DEBUG complete_with_usage: returning model={self._underlying_model_name} (self.model={self.model})")

        return LLMResponse(
            content=result.output,
            model=self._underlying_model_name,  # Use clean model name (without provider prefix)
            usage=usage,
            finish_reason="stop",
        )

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        # For now, convert to simple completion
        # TODO: Implement proper tool calling with Pydantic AI tools
        if messages:
            last_message = messages[-1]
            if last_message.get("role") == "user":
                result = await self.complete_with_usage(
                    last_message["content"], **kwargs
                )
                return {
                    "content": result.content,
                    "usage": result.usage,
                    "finish_reason": result.finish_reason,
                }

        return {"content": "", "usage": {}, "finish_reason": "stop"}

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt using Pydantic AI"""
        if not self._agent:
            raise RuntimeError("Pydantic AI agent not initialized")

        try:
            # Use Pydantic AI streaming support
            async with self._agent.run_stream(prompt) as stream:
                async for message in stream:
                    # Handle different message types from Pydantic AI stream
                    if hasattr(message, "snapshot"):
                        # This is a streaming event with partial content
                        if (
                            hasattr(message.snapshot, "all_messages")
                            and message.snapshot.all_messages
                        ):
                            last_message = message.snapshot.all_messages[-1]
                            if (
                                hasattr(last_message, "content")
                                and last_message.content
                            ):
                                yield last_message.content
                    elif hasattr(message, "content") and message.content:
                        # Direct content message
                        yield message.content
                    elif hasattr(message, "delta") and message.delta:
                        # Delta content (incremental updates)
                        yield message.delta

        except Exception as e:
            # Fallback to regular completion if streaming fails
            try:
                result = await self.complete(prompt, **kwargs)
                yield result
            except Exception as fallback_error:
                raise RuntimeError(
                    f"Both streaming and fallback completion failed. Streaming: {str(e)}, Fallback: {str(fallback_error)}"
                ) from e

    async def close(self) -> None:
        """Close provider connections"""
        # Pydantic AI handles cleanup automatically
        pass


def create_pydantic_ai_provider(
    provider_name: str, api_key: str, model: str
) -> PydanticAIProvider:
    """Factory function to create Pydantic AI providers"""

    # Map provider names to model strings that Pydantic AI understands
    model_mapping = {
        "openai": {
            # GPT-5 models (frontier models - latest)
            "gpt-5": "openai:gpt-5",
            "gpt-5-mini": "openai:gpt-5-mini",
            "gpt-5-nano": "openai:gpt-5-nano",
            # GPT-4.1 models
            "gpt-4.1": "openai:gpt-4.1",
            "gpt-4.1-mini": "openai:gpt-4.1-mini",
            "gpt-4.1-nano": "openai:gpt-4.1-nano",
            # GPT-4o models
            "gpt-4o": "openai:gpt-4o",
            "gpt-4o-mini": "openai:gpt-4o-mini",
            # Legacy models
            "gpt-4": "openai:gpt-4",
            "gpt-4-turbo": "openai:gpt-4-turbo-preview",
            "gpt-3.5-turbo": "openai:gpt-3.5-turbo",
        },
        "anthropic": {
            "claude-3-5-sonnet-20241022": "anthropic:claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022": "anthropic:claude-3-5-haiku-20241022",
            "claude-3-opus-20240229": "anthropic:claude-3-opus-20240229",
            "claude-3-7-sonnet-20250219": "anthropic:claude-3-7-sonnet-20250219",
        },
        "gemini": {
            # Gemini 3.0 models (newest)
            "gemini-3-pro-preview": "gemini-3-pro-preview",
            # Gemini 2.5 models (latest)
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
            # Gemini 2.0 models
            "gemini-2.0-flash-001": "gemini-2.0-flash-001",
            "gemini-2.0-flash-lite-001": "gemini-2.0-flash-lite-001",
            "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",  # Legacy experimental
            # Legacy preview models
            "gemini-2.5-flash-preview-09-2025": "gemini-2.5-flash-preview-09-2025",
            # Gemini 1.5 models (legacy)
            "gemini-1.5-pro": "gemini-1.5-pro",
            "gemini-1.5-flash": "gemini-1.5-flash",
        },
    }

    # Get the appropriate model string with improved fallback logic
    provider_models = model_mapping.get(provider_name.lower(), {})

    if model in provider_models:
        # Model found in mapping - use the mapped value
        pydantic_model = provider_models[model]
    else:
        # Model not in mapping - use the configured model directly with provider prefix
        # This allows for new models that aren't in our mapping yet
        pydantic_model = f"{provider_name.lower()}:{model}"

    # Set API key in environment for Pydantic AI
    import os

    if provider_name.lower() == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider_name.lower() == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif provider_name.lower() == "gemini":
        os.environ["GEMINI_API_KEY"] = api_key
    elif provider_name.lower() == "moonshot":
        # Moonshot AI uses OpenAI-compatible API
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = "https://api.moonshot.ai/v1"
        # Use openai: prefix so Pydantic AI uses OpenAI client
        # The actual model name will be sent to the custom base URL
        pydantic_model = f"openai:{model}"
    elif provider_name.lower() == "deepseek":
        # DeepSeek AI uses OpenAI-compatible API
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"
        # Use openai: prefix so Pydantic AI uses OpenAI client
        # The actual model name will be sent to the custom base URL
        pydantic_model = f"openai:{model}"

    # Pass provider_name explicitly to ensure proper cost tracking
    return PydanticAIProvider(api_key, pydantic_model, provider_name=provider_name.lower())
