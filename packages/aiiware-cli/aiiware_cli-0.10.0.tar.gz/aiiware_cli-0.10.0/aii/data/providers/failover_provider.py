# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Multi-provider failover wrapper for LLM providers"""


from collections.abc import AsyncIterator
from typing import Any

from .llm_provider import LLMProvider, LLMResponse


class FailoverLLMProvider(LLMProvider):
    """
    LLM provider wrapper that supports automatic failover between multiple providers

    Example:
        primary = AnthropicProvider(api_key="...")
        fallback = OpenAIProvider(api_key="...")

        provider = FailoverLLMProvider(
            providers=[primary, fallback],
            provider_names=["anthropic", "openai"]
        )

        # Will try anthropic first, fall back to openai on failure
        response = await provider.complete_with_usage("Hello")
    """

    def __init__(
        self,
        providers: list[LLMProvider],
        provider_names: list[str] | None = None,
    ):
        """
        Initialize failover provider

        Args:
            providers: List of LLM providers to use (in order of preference)
            provider_names: Optional list of provider names for logging
        """
        if not providers:
            raise ValueError("At least one provider is required")

        # Use the first provider's API key and model for the base class
        super().__init__(providers[0].api_key, providers[0].model)

        self.providers = providers
        self.provider_names = provider_names or [
            p.__class__.__name__ for p in providers
        ]

        if len(self.provider_names) != len(self.providers):
            raise ValueError("provider_names must match providers length")

        self._current_provider_index = 0
        self._failure_counts = [0] * len(providers)

    @property
    def provider_name(self) -> str:
        """Get current provider name"""
        return self.provider_names[self._current_provider_index]

    @property
    def model_info(self) -> str:
        """Get current model info"""
        current = self.providers[self._current_provider_index]
        return f"{self.provider_name}:{current.model}"

    def get_current_provider(self) -> LLMProvider:
        """Get the currently active provider"""
        return self.providers[self._current_provider_index]

    async def _try_with_failover(self, operation_name: str, operation):
        """
        Try an operation with automatic failover

        Args:
            operation_name: Name of the operation for logging
            operation: Async callable that takes a provider and returns result

        Returns:
            Result from the successful provider

        Raises:
            RuntimeError: If all providers fail
        """
        last_error = None

        for attempt_idx, (provider, name) in enumerate(zip(self.providers, self.provider_names)):
            try:
                result = await operation(provider)

                # Success! Update current provider index
                if attempt_idx != self._current_provider_index:
                    print(f"✅ Failover successful: Using {name} provider")
                    self._current_provider_index = attempt_idx

                # Reset failure count for this provider
                self._failure_counts[attempt_idx] = 0

                return result

            except Exception as e:
                last_error = e
                self._failure_counts[attempt_idx] += 1

                # Log the failure
                if attempt_idx < len(self.providers) - 1:
                    next_name = self.provider_names[attempt_idx + 1]
                    print(
                        f"⚠️  {name} provider failed ({operation_name}): {str(e)[:50]}... "
                        f"Trying {next_name}..."
                    )
                else:
                    print(f"❌ {name} provider failed ({operation_name}): {str(e)[:50]}...")

        # All providers failed
        raise RuntimeError(
            f"All {len(self.providers)} providers failed for {operation_name}. "
            f"Last error: {str(last_error)}"
        ) from last_error

    async def complete(self, prompt: str, **kwargs) -> str:
        """Generate completion with automatic failover"""
        async def _operation(provider):
            return await provider.complete(prompt, **kwargs)

        return await self._try_with_failover("complete", _operation)

    async def complete_with_usage(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate completion with usage tracking and automatic failover"""
        async def _operation(provider):
            return await provider.complete_with_usage(prompt, **kwargs)

        return await self._try_with_failover("complete_with_usage", _operation)

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Generate completion with tools and automatic failover"""
        async def _operation(provider):
            return await provider.complete_with_tools(messages, tools, **kwargs)

        return await self._try_with_failover("complete_with_tools", _operation)

    async def stream_complete(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Stream completion with automatic failover (returns from first successful provider)"""
        last_error = None

        for attempt_idx, (provider, name) in enumerate(zip(self.providers, self.provider_names)):
            try:
                async for chunk in provider.stream_complete(prompt, **kwargs):
                    yield chunk

                # Success! Update current provider
                if attempt_idx != self._current_provider_index:
                    self._current_provider_index = attempt_idx

                self._failure_counts[attempt_idx] = 0
                return

            except Exception as e:
                last_error = e
                self._failure_counts[attempt_idx] += 1

                if attempt_idx < len(self.providers) - 1:
                    next_name = self.provider_names[attempt_idx + 1]
                    print(
                        f"⚠️  {name} provider streaming failed: {str(e)[:50]}... "
                        f"Trying {next_name}..."
                    )

        raise RuntimeError(
            f"All {len(self.providers)} providers failed for streaming. "
            f"Last error: {str(last_error)}"
        ) from last_error

    async def close(self) -> None:
        """Close all providers"""
        for provider in self.providers:
            try:
                await provider.close()
            except Exception as e:
                print(f"Warning: Failed to close provider: {e}")

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of all providers"""
        return {
            "providers": [
                {
                    "name": name,
                    "failures": count,
                    "is_current": idx == self._current_provider_index,
                }
                for idx, (name, count) in enumerate(zip(self.provider_names, self._failure_counts))
            ],
            "current_provider": self.provider_name,
        }
