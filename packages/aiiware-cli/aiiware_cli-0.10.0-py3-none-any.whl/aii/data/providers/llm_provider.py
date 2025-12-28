# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""LLM Provider abstraction layer"""


import asyncio
import json
import os
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class LLMResponse:
    """Response from LLM provider"""

    content: str
    model: str
    usage: dict[str, int] = None
    finish_reason: str = "stop"


class LLMRetryConfig:
    """Configuration for LLM retry logic"""
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds
    MAX_DELAY = 8.0  # seconds
    TIMEOUT = 30.0  # seconds
    BACKOFF_MULTIPLIER = 2.0


async def retry_with_exponential_backoff(
    func,
    max_retries: int = LLMRetryConfig.MAX_RETRIES,
    base_delay: float = LLMRetryConfig.BASE_DELAY,
    max_delay: float = LLMRetryConfig.MAX_DELAY,
    timeout: float = LLMRetryConfig.TIMEOUT,
):
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        timeout: Total timeout for the operation (seconds)

    Returns:
        Result from the function

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    start_time = time.time()

    for attempt in range(max_retries + 1):
        try:
            # Check if we've exceeded total timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Operation timed out after {elapsed:.1f}s (limit: {timeout}s)"
                )

            # Execute with timeout for this attempt
            remaining_timeout = timeout - elapsed
            result = await asyncio.wait_for(func(), timeout=remaining_timeout)

            # Success!
            if attempt > 0:
                print(f"✅ Retry successful after {attempt} attempt(s)")
            return result

        except asyncio.TimeoutError as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (LLMRetryConfig.BACKOFF_MULTIPLIER ** attempt), max_delay)
                print(
                    f"⏱️  Request timed out (attempt {attempt + 1}/{max_retries + 1}). "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                print(f"❌ All retry attempts exhausted after timeout")
                raise TimeoutError(
                    f"LLM request failed after {max_retries + 1} attempts due to timeout"
                ) from e

        except Exception as e:
            last_exception = e
            # Check if this is a retryable error
            error_str = str(e).lower()
            retryable_errors = [
                "rate limit",
                "timeout",
                "connection",
                "network",
                "temporarily unavailable",
                "503",
                "504",
                "502",
                "429",  # Too Many Requests
            ]

            is_retryable = any(err in error_str for err in retryable_errors)

            if is_retryable and attempt < max_retries:
                delay = min(base_delay * (LLMRetryConfig.BACKOFF_MULTIPLIER ** attempt), max_delay)
                print(
                    f"⚠️  {type(e).__name__}: {str(e)} "
                    f"(attempt {attempt + 1}/{max_retries + 1}). "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
            else:
                if not is_retryable:
                    print(f"❌ Non-retryable error: {type(e).__name__}: {str(e)}")
                else:
                    print(f"❌ All retry attempts exhausted")
                raise

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, model: str = "default"):
        self.api_key = api_key
        self.model = model

    @property
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'OpenAI', 'Anthropic')"""
        return self.__class__.__name__.replace("Provider", "")

    @property
    def model_name(self) -> str:
        """Get the model name (alias for self.model for backward compatibility)"""
        return self.model

    @property
    def model_info(self) -> str:
        """Get formatted model information (e.g., 'OpenAI:gpt-4')"""
        return f"{self.provider_name}:{self.model}"

    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        pass

    @abstractmethod
    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information

        Args:
            prompt: The prompt to generate completion for
            on_token: Optional callback to receive tokens as they stream in (for real-time display)
            **kwargs: Additional provider-specific arguments

        Returns:
            LLMResponse with content, usage, and metadata
        """
        pass

    @abstractmethod
    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        pass

    @abstractmethod
    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt"""
        pass

    async def close(self) -> None:
        """Close provider connections"""
        return


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            import openai

            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        except ImportError as e:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            ) from e

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Prepare parameters
        params = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
        }

        try:
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI completion failed: {str(e)}") from e

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Prepare parameters
        params = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
        }

        try:
            # If streaming callback provided, use streaming
            if on_token is not None:
                params["stream"] = True
                accumulated_text = ""
                usage_data = None

                async for chunk in await self.client.chat.completions.create(**params):
                    if chunk.choices[0].delta.content:
                        delta = chunk.choices[0].delta.content
                        accumulated_text += delta
                        await on_token(delta)

                    # Capture usage from final chunk if available
                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_data = chunk.usage

                # Estimate usage if not provided in stream
                usage = {}
                if usage_data:
                    usage = {
                        "input_tokens": usage_data.prompt_tokens,
                        "output_tokens": usage_data.completion_tokens,
                        "total_tokens": usage_data.total_tokens,
                    }
                else:
                    # Fallback estimation
                    input_est = len(prompt.split()) * 1.3
                    output_est = len(accumulated_text.split()) * 1.3
                    usage = {
                        "input_tokens": int(input_est),
                        "output_tokens": int(output_est),
                        "total_tokens": int(input_est + output_est),
                    }

                return LLMResponse(
                    content=accumulated_text,
                    model=params["model"],
                    usage=usage,
                    finish_reason="stop",
                )
            else:
                # Non-streaming path
                response = await self.client.chat.completions.create(**params)

                # Extract usage information
                usage = {}
                if hasattr(response, "usage") and response.usage:
                    usage = {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }

                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=params["model"],
                    usage=usage,
                    finish_reason=response.choices[0].finish_reason,
                )
        except Exception as e:
            # Check for content filter errors (OpenAI, Moonshot, etc.)
            error_str = str(e)
            if "content_filter" in error_str or "considered high risk" in error_str:
                provider_name = getattr(self, 'provider_name', 'LLM provider')
                raise RuntimeError(
                    f"Content filtered by {provider_name}: The request was rejected due to content policy. "
                    f"This content may contain sensitive topics (politics, violence, etc.). "
                    f"Try using a different model (Claude, Gemini, DeepSeek) which have less restrictive filters."
                ) from e

            # Generic error for other failures
            provider_name = getattr(self, 'provider_name', 'LLM provider')
            raise RuntimeError(f"{provider_name} completion failed: {str(e)}") from e

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        params = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")

        try:
            response = await self.client.chat.completions.create(**params)
            return {
                "content": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "usage": response.usage._asdict() if response.usage else {},
                "finish_reason": response.choices[0].finish_reason,
            }
        except Exception as e:
            raise RuntimeError(f"OpenAI completion with tools failed: {str(e)}") from e

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt"""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        params = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True,
        }

        try:
            async for chunk in await self.client.chat.completions.create(**params):
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise RuntimeError(f"OpenAI streaming failed: {str(e)}") from e

    async def close(self) -> None:
        """Close OpenAI client"""
        if self.client and hasattr(self.client, "close"):
            await self.client.close()


class OpenAICompatibleProvider(OpenAIProvider):
    """OpenAI-compatible provider for Moonshot, DeepSeek, and other compatible APIs"""

    def __init__(self, api_key: str, model: str, base_url: str, provider_name: str = None):
        """
        Initialize OpenAI-compatible provider with custom base URL.

        Args:
            api_key: API key for the provider
            model: Model name (e.g., 'kimi-k2-thinking', 'deepseek-chat')
            base_url: Custom API base URL (e.g., 'https://api.moonshot.ai/v1')
            provider_name: Provider name for cost calculation (e.g., 'moonshot', 'deepseek')
        """
        self.base_url = base_url
        self._provider_name = provider_name  # Store for cost calculation
        # Call parent constructor
        LLMProvider.__init__(self, api_key, model)
        self.client = None
        self._initialize_client()

    @property
    def provider_name(self) -> str:
        """Override to return actual provider name for cost calculation"""
        return self._provider_name if self._provider_name else "openai"

    def _initialize_client(self):
        """Initialize OpenAI client with custom base URL"""
        try:
            import openai

            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except ImportError as e:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            ) from e


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation with subscription support"""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229", use_subscription: bool = False):
        super().__init__(api_key, model)
        self.client = None
        self.use_subscription = use_subscription
        self.oauth_token = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Anthropic client with subscription or API key authentication"""
        try:
            import anthropic

            # Try subscription authentication first
            if self.use_subscription:
                oauth_token = self._get_oauth_token()
                if oauth_token:
                    self.oauth_token = oauth_token
                    print(f"DEBUG: Found OAuth token starting with: {oauth_token[:20]}...")
                    # OAuth tokens starting with sk-ant-oat01- are for web API only
                    if oauth_token.startswith("sk-ant-oat01-"):
                        print("DEBUG: OAuth token detected - using subscription web API exclusively")
                        # Subscription OAuth tokens - use custom web API client exclusively
                        self.client = "subscription_web_api"  # Flag for custom handling
                        self.oauth_token = oauth_token
                    else:
                        print("DEBUG: Using standard API for OAuth token")
                        # Regular OAuth tokens - use standard API
                        self.client = anthropic.AsyncAnthropic(
                            api_key=oauth_token,
                            base_url="https://api.anthropic.com"
                        )
                    return
                else:
                    print("Warning: OAuth token not found, falling back to API key")

            # Fallback to API key authentication
            if self.api_key and self.api_key != "subscription":
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            else:
                raise RuntimeError("No valid authentication method available")

        except ImportError as e:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            ) from e

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Handle subscription web API for OAuth tokens
        if self.client == "subscription_web_api":
            return await self._complete_web_api(prompt, **kwargs)

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = await self.client.messages.create(**params)
            return response.content[0].text
        except Exception as e:
            # Handle subscription-specific errors
            if self.use_subscription and "rate limit" in str(e).lower():
                raise RuntimeError(f"Subscription usage limit reached: {str(e)}") from e
            elif self.use_subscription and "unauthorized" in str(e).lower():
                # Try to refresh OAuth token
                if self._refresh_oauth_token():
                    self._initialize_client()
                    response = await self.client.messages.create(**params)
                    return response.content[0].text
            raise RuntimeError(f"Anthropic completion failed: {str(e)}") from e

    def _get_oauth_token(self) -> Optional[str]:
        """Get OAuth token from native aii OAuth client"""
        print("DEBUG: _get_oauth_token called")
        try:
            # Import here to avoid circular imports
            from ...auth.claude_oauth import ClaudeOAuthClient

            # Use aii's native OAuth client
            config_dir = Path.home() / ".aii"
            oauth_client = ClaudeOAuthClient(config_dir)

            # Load existing credentials if available
            import asyncio
            try:
                # Try to get the running loop
                loop = asyncio.get_running_loop()
                # If there's already a running loop, we need to handle this differently
                # For now, let's use the synchronous credential loading method
                if oauth_client.credentials_file.exists():
                    import json
                    with open(oauth_client.credentials_file, 'r') as f:
                        creds = json.load(f)
                    token = creds.get("access_token")
                    print(f"DEBUG: Loaded token synchronously: {token[:20] if token else None}...")
                else:
                    token = None
                    print("DEBUG: No credentials file found")
            except RuntimeError:
                # No running loop, safe to create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                token = loop.run_until_complete(oauth_client.get_valid_token())
                loop.close()

            if token:
                print(f"DEBUG: Found OAuth token: {token[:20]}...")
                return token
            else:
                print("DEBUG: No OAuth token found from oauth_client")

            # Fallback: check for environment variable
            oauth_token = os.getenv("CLAUDE_OAUTH_TOKEN") or os.getenv("CLAUDE_SESSION_KEY")
            if oauth_token:
                return oauth_token

            # Fallback: check Claude Code credentials for compatibility
            claude_dir = Path.home() / ".claude"
            credentials_file = claude_dir / ".credentials.json"

            if credentials_file.exists():
                with open(credentials_file, 'r') as f:
                    credentials = json.load(f)
                    # Extract access token from Claude Code OAuth credentials
                    if "access_token" in credentials:
                        return credentials["access_token"]
                    elif "oauth" in credentials and "access_token" in credentials["oauth"]:
                        return credentials["oauth"]["access_token"]

        except Exception as e:
            print(f"Warning: Failed to load OAuth token: {e}")

        return None

    def _refresh_oauth_token(self) -> bool:
        """Attempt to refresh OAuth token using native OAuth client"""
        try:
            # Import here to avoid circular imports
            from ...auth.claude_oauth import ClaudeOAuthClient

            # Use aii's native OAuth client for token refresh
            config_dir = Path.home() / ".aii"
            oauth_client = ClaudeOAuthClient(config_dir)

            # Attempt to refresh token
            import asyncio
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(oauth_client._refresh_access_token())

            if success:
                # Update our token
                self.oauth_token = loop.run_until_complete(oauth_client.get_valid_token())
                return True

            return False

        except Exception as e:
            print(f"Warning: Failed to refresh OAuth token: {e}")
            return False

    @property
    def auth_method(self) -> str:
        """Get current authentication method"""
        if self.oauth_token:
            return "subscription"
        return "api_key"

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information with retry logic"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        # Handle subscription web API
        if self.client == "subscription_web_api":
            return await self._complete_web_api_with_usage(prompt, **kwargs)

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": [{"role": "user", "content": prompt}],
        }

        async def _make_request():
            # Check if streaming is requested
            if on_token is not None:
                # Streaming path
                accumulated_text = ""
                input_tokens = 0
                output_tokens = 0

                async with self.client.messages.stream(**params) as stream:
                    async for text in stream.text_stream:
                        accumulated_text += text
                        on_token(text)

                    # Get final message for usage
                    final_message = await stream.get_final_message()
                    if hasattr(final_message, "usage") and final_message.usage:
                        input_tokens = final_message.usage.input_tokens
                        output_tokens = final_message.usage.output_tokens

                usage = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                }

                return LLMResponse(
                    content=accumulated_text,
                    model=params["model"],
                    usage=usage,
                    finish_reason="stop",
                )
            else:
                # Non-streaming path
                response = await self.client.messages.create(**params)

                # Extract usage information
                usage = {}
                if hasattr(response, "usage") and response.usage:
                    usage = {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens
                        + response.usage.output_tokens,
                    }

                return LLMResponse(
                    content=response.content[0].text,
                    model=params["model"],
                    usage=usage,
                    finish_reason=response.stop_reason,
                )

        try:
            # Use retry logic with exponential backoff
            return await retry_with_exponential_backoff(_make_request)
        except Exception as e:
            raise RuntimeError(
                f"Anthropic completion with usage failed: {str(e)}"
            ) from e

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": messages,
        }

        if tools:
            params["tools"] = tools

        try:
            response = await self.client.messages.create(**params)
            return {
                "content": response.content[0].text,
                "tool_calls": None,  # Anthropic handles tools differently
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                "finish_reason": response.stop_reason,
            }
        except Exception as e:
            raise RuntimeError(
                f"Anthropic completion with tools failed: {str(e)}"
            ) from e

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt"""
        if not self.client:
            raise RuntimeError("Anthropic client not initialized")

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            async with self.client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Anthropic streaming failed: {str(e)}") from e

    async def _complete_web_api(self, prompt: str, **kwargs) -> str:
        """Complete using Claude's web API for subscription users"""
        import aiohttp
        import uuid

        # Get organization ID from stored credentials
        org_id = self._get_organization_id()
        print(f"DEBUG: Loaded organization ID: {org_id}")
        if not org_id:
            raise RuntimeError("Organization ID not found. Please re-authenticate with aii oauth.")

        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Origin": "https://claude.ai",
            "Referer": "https://claude.ai/",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

        # Use stored organization ID directly - try direct completion API
        async with aiohttp.ClientSession() as session:

            # Try the direct completion endpoint that Claude web UI might use
            completion_url = f"https://claude.ai/api/organizations/{org_id}/completion"

            # Format the request similar to the standard API but for web
            completion_data = {
                "model": kwargs.get("model", self.model),
                "prompt": prompt,
                "max_tokens": kwargs.get("max_tokens", 4000),
                "temperature": kwargs.get("temperature", 0.7),
                "stream": False
            }

            print(f"DEBUG: Trying direct completion at URL: {completion_url}")
            print(f"DEBUG: Completion data: {completion_data}")

            async with session.post(completion_url, headers=headers, json=completion_data) as response:
                print(f"DEBUG: Completion response status: {response.status}")
                response_text = await response.text()
                print(f"DEBUG: Completion response: {response_text[:200]}...")

                if response.status == 200:
                    try:
                        result = await response.json()
                        return result.get("completion", result.get("content", response_text))
                    except:
                        return response_text.strip()

                # If direct completion fails, try the conversation approach
                print("DEBUG: Direct completion failed, trying conversation approach...")

            # Fallback: Create conversation approach
            conversation_url = f"https://claude.ai/api/organizations/{org_id}/chat_conversations"
            conversation_data = {
                "uuid": str(uuid.uuid4()),
                "name": "aii conversation"
            }

            print(f"DEBUG: Creating conversation at URL: {conversation_url}")
            print(f"DEBUG: Conversation data: {conversation_data}")
            async with session.post(conversation_url, headers=headers, json=conversation_data) as response:
                print(f"DEBUG: Conversation creation response status: {response.status}")
                response_text = await response.text()
                print(f"DEBUG: Conversation creation response: {response_text[:200]}...")

                if response.status not in [200, 201]:
                    raise RuntimeError(f"Failed to create conversation: {response.status} - {response_text}")

                conversation = await response.json()
                conversation_id = conversation["uuid"]

            # Send message
            message_url = f"https://claude.ai/api/organizations/{org_id}/chat_conversations/{conversation_id}/completion"
            message_data = {
                "prompt": prompt,
                "model": kwargs.get("model", self.model),
                "timezone": "UTC"
            }

            async with session.post(message_url, headers=headers, json=message_data) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to send message: {response.status}")

                # Claude web API may return streaming response
                response_text = ""
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode())
                            if "completion" in data:
                                response_text += data["completion"]
                        except:
                            continue

                return response_text.strip()

    async def _complete_web_api_with_usage(self, prompt: str, **kwargs) -> LLMResponse:
        """Complete using Claude's web API with usage information"""
        content = await self._complete_web_api(prompt, **kwargs)

        # Web API doesn't provide detailed usage info, so we estimate
        input_tokens = len(prompt.split()) * 1.3  # Rough estimation
        output_tokens = len(content.split()) * 1.3

        return LLMResponse(
            content=content,
            model=self.model,
            usage={
                "input_tokens": int(input_tokens),
                "output_tokens": int(output_tokens)
            },
            finish_reason="stop"
        )

    async def _complete_standard_api(self, prompt: str, **kwargs) -> str:
        """Complete using standard Anthropic API with OAuth token"""
        print("DEBUG: Using standard Anthropic API with OAuth token")

        # Create a temporary client for this request
        import anthropic
        temp_client = anthropic.AsyncAnthropic(
            api_key=self.oauth_token,
            base_url="https://api.anthropic.com"
        )

        params = {
            "model": kwargs.get("model", self.model),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = await temp_client.messages.create(**params)
            return response.content[0].text
        finally:
            await temp_client.close()

    def _get_organization_id(self) -> Optional[str]:
        """Get organization ID from stored OAuth credentials"""
        try:
            # Import here to avoid circular imports
            from pathlib import Path
            import json
            from aii.config.manager import ConfigManager

            config_manager = ConfigManager()
            config_dir = Path(config_manager.config_dir)
            auth_dir = config_dir / "auth"
            credentials_file = auth_dir / "claude_oauth_credentials.json"

            if not credentials_file.exists():
                return None

            with open(credentials_file, 'r') as f:
                credentials = json.load(f)

            return credentials.get("org_id")
        except Exception:
            return None

    async def close(self) -> None:
        """Close Anthropic client"""
        if self.client and hasattr(self.client, "close"):
            await self.client.close()


class LocalLLMProvider(LLMProvider):
    """Local LLM provider for offline operation"""

    def __init__(self, model_path: str, model: str = "local"):
        super().__init__("local", model)
        self.model_path = model_path
        self.client = None

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion using local model"""
        # This would integrate with local models like Ollama, llama.cpp, etc.
        # For now, return a placeholder
        return f"Local model response to: {prompt[:50]}..."

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with usage tracking for local models"""
        content = await self.complete(prompt, **kwargs)

        # If streaming callback provided, send the complete response
        if on_token is not None:
            on_token(content)

        # Estimate token usage for local models (rough approximation)
        input_tokens = len(prompt.split()) * 1.3  # Rough token estimation
        output_tokens = len(content.split()) * 1.3

        usage = {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(input_tokens + output_tokens),
        }

        return LLMResponse(
            content=content, model=self.model, usage=usage, finish_reason="stop"
        )

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Local models typically don't support function calling"""
        content = await self.complete(messages[-1]["content"], **kwargs)
        return {
            "content": content,
            "tool_calls": None,
            "usage": {"tokens": 0},
            "finish_reason": "stop",
        }

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from local model"""
        # Simulate streaming for local model
        response = await self.complete(prompt, **kwargs)
        words = response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.1)


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        super().__init__(api_key, model)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Gemini client"""
        try:
            import google.genai as genai

            # Configure the client with API key
            self.client = genai.Client(api_key=self.api_key)
        except ImportError as e:
            raise ImportError(
                "Google GenAI package not installed. Install with: pip install google-genai"
            ) from e

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion from prompt"""
        if not self.client:
            raise RuntimeError("Gemini client not initialized")

        try:
            # Generate response using google-genai
            response = await self.client.aio.models.generate_content(
                model=kwargs.get("model", self.model),
                contents=prompt,
                config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 2000),
                },
            )

            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini completion failed: {str(e)}") from e

    async def complete_with_usage(
        self,
        prompt: str,
        on_token: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion with detailed usage information"""
        if not self.client:
            raise RuntimeError("Gemini client not initialized")

        try:
            # Check if streaming is requested
            if on_token is not None:
                # Use Gemini's async streaming support
                accumulated_text = ""
                input_tokens = 0
                output_tokens = 0

                # Stream content
                async for chunk in self.client.aio.models.generate_content_stream(
                    model=kwargs.get("model", self.model),
                    contents=prompt,
                    config={
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_output_tokens": kwargs.get("max_tokens", 2000),
                    },
                ):
                    # Extract text from chunk
                    if hasattr(chunk, 'text') and chunk.text:
                        # Calculate delta (new text only)
                        chunk_text = chunk.text
                        if chunk_text.startswith(accumulated_text):
                            # This is a cumulative chunk
                            delta = chunk_text[len(accumulated_text):]
                        else:
                            # This is a new delta chunk
                            delta = chunk_text

                        if delta:
                            accumulated_text += delta
                            on_token(delta)

                    # Try to get usage from chunk
                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        input_tokens = getattr(chunk.usage_metadata, "prompt_token_count", 0)
                        output_tokens = getattr(chunk.usage_metadata, "candidates_token_count", 0)

                # Create a response-like object with accumulated text
                response = type('StreamedResponse', (), {
                    'text': accumulated_text,
                    'usage_metadata': type('Usage', (), {
                        'prompt_token_count': input_tokens,
                        'candidates_token_count': output_tokens,
                        'total_token_count': input_tokens + output_tokens
                    })()
                })()
            else:
                # Non-streaming path
                response = await self.client.aio.models.generate_content(
                    model=kwargs.get("model", self.model),
                    contents=prompt,
                    config={
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_output_tokens": kwargs.get("max_tokens", 2000),
                    },
                )

            # Extract usage information from google-genai response
            # The google-genai library uses usage_metadata with specific field names
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                # Use the correct field names from google-genai
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }
            elif hasattr(response, "usage") and response.usage:
                # Fallback to old field names if available
                usage = {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                }

            # If usage is still empty or all zeros, try count_tokens API
            if not usage or usage.get("total_tokens", 0) == 0:
                try:
                    # Use Gemini's official token counting API
                    input_count_response = await self.client.aio.models.count_tokens(
                        model=kwargs.get("model", self.model),
                        contents=prompt
                    )
                    input_tokens = input_count_response.total_tokens

                    # Count output tokens
                    output_count_response = await self.client.aio.models.count_tokens(
                        model=kwargs.get("model", self.model),
                        contents=response.text
                    )
                    output_tokens = output_count_response.total_tokens

                    usage = {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    }
                except Exception as count_error:
                    # Final fallback to estimation if count_tokens API fails
                    print(f"Warning: Token counting API failed: {count_error}, using estimation")
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response.text.split()) * 1.3
                    usage = {
                        "input_tokens": int(input_tokens),
                        "output_tokens": int(output_tokens),
                        "total_tokens": int(input_tokens + output_tokens),
                    }

            return LLMResponse(
                content=response.text,
                model=kwargs.get("model", self.model),
                usage=usage,
                finish_reason="stop",
            )
        except Exception as e:
            raise RuntimeError(f"Gemini completion with usage failed: {str(e)}") from e

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with function calling support"""
        if not self.client:
            raise RuntimeError("Gemini client not initialized")

        try:
            # Convert messages to Gemini format
            prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

            # Generate response (Gemini has function calling support but simplified here)
            model = self.client.GenerativeModel(
                model_name=kwargs.get("model", self.model)
            )

            generation_config = {
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 2000),
            }

            response = await model.generate_content_async(
                prompt, generation_config=generation_config
            )

            return {
                "content": response.text,
                "tool_calls": None,  # Simplified for now
                "usage": {
                    "input_tokens": getattr(
                        response.usage_metadata, "prompt_token_count", 0
                    ),
                    "output_tokens": getattr(
                        response.usage_metadata, "candidates_token_count", 0
                    ),
                },
                "finish_reason": "stop",
            }
        except Exception as e:
            raise RuntimeError(f"Gemini completion with tools failed: {str(e)}") from e

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion from prompt"""
        if not self.client:
            raise RuntimeError("Gemini client not initialized")

        try:
            model = self.client.GenerativeModel(
                model_name=kwargs.get("model", self.model)
            )

            generation_config = {
                "temperature": kwargs.get("temperature", 0.7),
                "max_output_tokens": kwargs.get("max_tokens", 2000),
            }

            # Gemini streaming
            response = model.generate_content(
                prompt, generation_config=generation_config, stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise RuntimeError(f"Gemini streaming failed: {str(e)}") from e

    async def close(self) -> None:
        """Close Gemini client"""
        # Gemini client doesn't need explicit closing
        pass


def create_llm_provider(
    provider_name: str, api_key: str, model: str = None, use_pydantic_ai: bool = False, use_subscription: bool = False
) -> LLMProvider:
    """Factory function to create LLM providers"""
    provider_name = provider_name.lower()
    # Creating LLM provider

    # Handle OpenAI-compatible providers FIRST (bypass Pydantic AI)
    # Moonshot and DeepSeek use OpenAI SDK with custom base URLs
    if provider_name == "moonshot":
        return OpenAICompatibleProvider(
            api_key=api_key,
            model=model or "kimi-k2-turbo-preview",
            base_url="https://api.moonshot.ai/v1",
            provider_name="moonshot"
        )
    elif provider_name == "deepseek":
        return OpenAICompatibleProvider(
            api_key=api_key,
            model=model or "deepseek-chat",
            base_url="https://api.deepseek.com",
            provider_name="deepseek"
        )

    # Use Pydantic AI if requested (for other providers)
    if use_pydantic_ai:
        try:
            from .pydantic_ai_provider import create_pydantic_ai_provider

            return create_pydantic_ai_provider(provider_name, api_key, model)
        except ImportError as e:
            print(
                f"Warning: Pydantic AI not available, falling back to custom provider: {e}"
            )

    # Fallback to custom providers
    if provider_name == "gemini":
        return GeminiProvider(api_key, model or "gemini-2.0-flash")
    elif provider_name == "openai":
        return OpenAIProvider(api_key, model or "gpt-4")
    elif provider_name == "anthropic":
        return AnthropicProvider(
            api_key,
            model or "claude-3-sonnet-20240229",
            use_subscription=use_subscription
        )
    elif provider_name == "local":
        return LocalLLMProvider(
            api_key, model or "local"
        )  # api_key is model_path for local
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")


async def create_temporary_provider(
    provider_name: str,
    model: str,
    config_manager
) -> LLMProvider:
    """
    Create a temporary LLM provider for a single request.

    This allows per-request model overrides without affecting the server's
    default provider configuration.

    Args:
        provider_name: Provider name (openai, anthropic, gemini, moonshot, deepseek)
        model: Model name to use
        config_manager: ConfigManager instance for API key lookup

    Returns:
        LLMProvider instance configured for the specified model

    Raises:
        ValueError: If provider_name is not supported
        RuntimeError: If API key for provider is not configured

    Example:
        >>> temp_provider = await create_temporary_provider(
        ...     provider_name="moonshot",
        ...     model="kimi-k2-thinking",
        ...     config_manager=config_manager
        ... )
        >>> response = await temp_provider.complete("hello")
    """
    # Validate provider
    valid_providers = ["openai", "anthropic", "gemini", "moonshot", "deepseek"]
    if provider_name not in valid_providers:
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Valid providers: {', '.join(valid_providers)}"
        )

    # Get API key for provider
    api_key_map = {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "gemini_api_key",
        "moonshot": "moonshot_api_key",
        "deepseek": "deepseek_api_key"
    }

    api_key = config_manager.get_secret(api_key_map[provider_name])
    if not api_key:
        raise RuntimeError(
            f"API key for {provider_name} not configured. "
            f"Set {api_key_map[provider_name].upper()} environment variable "
            f"or run 'aii config provider {provider_name}'"
        )

    # Create provider instance (reuse existing factory)
    return create_llm_provider(
        provider_name=provider_name,
        api_key=api_key,
        model=model,
        use_pydantic_ai=True  # Use default behavior
    )
