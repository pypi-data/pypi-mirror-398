# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Model Registry - Maps model names to providers."""


from aii.data.providers.model_catalog import get_model_info as _get_catalog_info


# Model → Provider mapping
# This registry enables auto-detection of provider from model name
# v0.9.3: Optimized to include only actively maintained models (KEEP/RECOMMENDED)
# Removed: Deprecated/retired models (gpt-3.5-turbo, claude-3-*, gemini-pro-vision, etc.)
MODEL_PROVIDER_MAP = {
    # OpenAI models (November 2025 - Active only)
    "gpt-5.1": "openai",  # 🆕 RECOMMENDED - Adaptive reasoning (Nov 2025)
    "gpt-5-mini": "openai",  # ✅ KEEP - Cost-effective GPT-5
    "gpt-5-nano": "openai",  # ✅ KEEP - Ultra-cheap GPT-5
    "gpt-4o": "openai",  # ✅ KEEP - Multimodal, fast (128K)
    "gpt-4o-mini": "openai",  # ✅ KEEP - Best GPT-3.5 replacement
    "gpt-4.1": "openai",  # ✅ KEEP - Coding, 1M context
    "gpt-4.1-mini": "openai",  # ✅ KEEP - Mid-tier, affordable (1M)
    "gpt-4.1-nano": "openai",  # ✅ KEEP - Smallest, fastest, cheapest (1M)

    # Anthropic models (Latest Claude series - use API aliases for cleaner UX)
    "claude-sonnet-4-5": "anthropic",  # 🆕 RECOMMENDED - Best coding (Sept 2025)
    "claude-sonnet-4": "anthropic",  # ✅ KEEP - Balanced performance
    "claude-haiku-4-5": "anthropic",  # ✅ KEEP - Fast, affordable (Oct 2024)
    "claude-opus-4-1": "anthropic",  # ✅ KEEP - Latest Opus (Aug 2025)
    "claude-opus-4": "anthropic",  # ✅ KEEP - Most capable Claude

    # Google Gemini models (Latest series)
    "gemini-3-pro-preview": "gemini",  # 🆕 LATEST - Newest flagship (Dec 2024)
    "gemini-2.5-pro": "gemini",  # ✅ KEEP - Latest flagship (2M)
    "gemini-2.5-flash": "gemini",  # 🆕 RECOMMENDED - Balanced, efficient (1M)

    # Moonshot models (Kimi K2 series - All active)
    "kimi-k2-thinking": "moonshot",  # ✅ KEEP - Advanced reasoning
    "kimi-k2-thinking-turbo": "moonshot",  # ✅ KEEP - Fast reasoning
    "kimi-k2-0905-preview": "moonshot",  # ✅ KEEP - Preview model
    "kimi-k2-turbo-preview": "moonshot",  # ✅ KEEP - Fast, cost-effective

    # DeepSeek models (V3, V2, R1 - Ultra cost-effective)
    "deepseek-chat": "deepseek",  # 🆕 RECOMMENDED - V3, ultra cost-effective
    "deepseek-coder": "deepseek",  # 🆕 RECOMMENDED - V2, best for coding
    "deepseek-reasoner": "deepseek",  # ✅ KEEP - R1, advanced reasoning
}


def detect_provider_from_model(model: str) -> str:
    """
    Auto-detect provider from model name.

    Args:
        model: Model name (e.g., 'kimi-k2-thinking', 'gpt-4.1-mini')

    Returns:
        Provider name (e.g., 'moonshot', 'openai')

    Raises:
        ValueError: If model is not recognized

    Example:
        >>> detect_provider_from_model("kimi-k2-thinking")
        'moonshot'
        >>> detect_provider_from_model("gpt-4.1-mini")
        'openai'
        >>> detect_provider_from_model("invalid-model")
        Traceback (most recent call last):
            ...
        ValueError: Model 'invalid-model' not recognized...
    """
    # Try exact match first
    provider = MODEL_PROVIDER_MAP.get(model)
    if provider:
        return provider

    # Try prefix matching for flexible model names
    # Example: "gpt-4-turbo-2024-04-09" matches "gpt-4-turbo"
    for model_name, provider_name in MODEL_PROVIDER_MAP.items():
        if model.startswith(model_name):
            return provider_name

    # Model not found - provide helpful error
    available_models = sorted(MODEL_PROVIDER_MAP.keys())
    raise ValueError(
        f"Model '{model}' not recognized. "
        f"Available models: {', '.join(available_models)}"
    )


def get_available_models() -> dict[str, list[str]]:
    """
    Get all available models grouped by provider.

    Returns:
        Dictionary mapping provider → list of models

    Example:
        >>> models = get_available_models()
        >>> 'openai' in models
        True
        >>> 'gpt-4.1-mini' in models['openai']
        True
        >>> 'kimi-k2-thinking' in models['moonshot']
        True
    """
    result: dict[str, list[str]] = {}

    for model, provider in MODEL_PROVIDER_MAP.items():
        if provider not in result:
            result[provider] = []
        result[provider].append(model)

    # Sort models within each provider for better readability
    for provider in result:
        result[provider].sort()

    return result


def validate_model_provider_match(model: str, provider: str) -> bool:
    """
    Validate that a model belongs to the specified provider.

    Args:
        model: Model name
        provider: Provider name

    Returns:
        True if model belongs to provider, False otherwise

    Example:
        >>> validate_model_provider_match("gpt-4.1-mini", "openai")
        True
        >>> validate_model_provider_match("gpt-4.1-mini", "anthropic")
        False
    """
    try:
        detected_provider = detect_provider_from_model(model)
        return detected_provider == provider
    except ValueError:
        # Model not recognized
        return False


def get_models_for_provider(provider: str) -> list[str]:
    """
    Get all models available for a specific provider.

    Args:
        provider: Provider name (openai, anthropic, gemini, moonshot, deepseek)

    Returns:
        List of model names for that provider

    Example:
        >>> models = get_models_for_provider("openai")
        >>> "gpt-4.1-mini" in models
        True
        >>> models = get_models_for_provider("moonshot")
        >>> "kimi-k2-thinking" in models
        True
    """
    all_models = get_available_models()
    return all_models.get(provider, [])


# v0.9.3: Model metadata with display names, cost tiers, and descriptions
# Updated to match optimized MODEL_PROVIDER_MAP (only KEEP/RECOMMENDED models)
MODEL_METADATA = {
    "openai": {
        "display_name": "OpenAI",
        "api_key_env_var": "OPENAI_API_KEY",
        "models": {
            "gpt-5.1": {
                "display_name": "GPT-5.1",
                "cost_tier": "premium",
                "description": "🆕 Adaptive reasoning, Nov 2025"
            },
            "gpt-5.1-instant": {
                "display_name": "GPT-5.1 Instant",
                "cost_tier": "premium",
                "description": "🆕 Warmer, conversational"
            },
            "gpt-5-mini": {
                "display_name": "GPT-5 Mini",
                "cost_tier": "standard",
                "description": "Cost-effective GPT-5 (272K)"
            },
            "gpt-5-nano": {
                "display_name": "GPT-5 Nano",
                "cost_tier": "cheap",
                "description": "Ultra-cheap GPT-5 (272K)"
            },
            "gpt-4o": {
                "display_name": "GPT-4o",
                "cost_tier": "premium",
                "description": "Multimodal, fast (128K)"
            },
            "gpt-4o-mini": {
                "display_name": "GPT-4o Mini",
                "cost_tier": "cheap",
                "description": "Best GPT-3.5 replacement"
            },
            "gpt-4.1": {
                "display_name": "GPT-4.1",
                "cost_tier": "standard",
                "description": "Coding, 1M context"
            },
            "gpt-4.1-mini": {
                "display_name": "GPT-4.1 Mini",
                "cost_tier": "cheap",
                "description": "Mid-tier, affordable (1M)"
            },
            "gpt-4.1-nano": {
                "display_name": "GPT-4.1 Nano",
                "cost_tier": "cheap",
                "description": "Smallest, fastest, cheapest (1M)"
            }
        }
    },
    "anthropic": {
        "display_name": "Anthropic",
        "api_key_env_var": "ANTHROPIC_API_KEY",
        "models": {
            "claude-sonnet-4-5": {
                "display_name": "Claude Sonnet 4.5",
                "cost_tier": "premium",
                "description": "🆕 Best coding model globally (Sept 2025)"
            },
            "claude-sonnet-4": {
                "display_name": "Claude Sonnet 4",
                "cost_tier": "premium",
                "description": "Balanced performance (200K, 1M beta)"
            },
            "claude-haiku-4-5": {
                "display_name": "Claude Haiku 4.5",
                "cost_tier": "standard",
                "description": "Fast, affordable (Oct 2024)"
            },
            "claude-opus-4-1": {
                "display_name": "Claude Opus 4.1",
                "cost_tier": "premium",
                "description": "Latest Opus (Aug 2025)"
            },
            "claude-opus-4": {
                "display_name": "Claude Opus 4",
                "cost_tier": "premium",
                "description": "Most capable Claude"
            }
        }
    },
    "gemini": {
        "display_name": "Google Gemini",
        "api_key_env_var": "GEMINI_API_KEY",
        "models": {
            "gemini-2.5-pro": {
                "display_name": "Gemini 2.5 Pro",
                "cost_tier": "premium",
                "description": "Latest flagship (2M context)"
            },
            "gemini-2.5-flash": {
                "display_name": "Gemini 2.5 Flash",
                "cost_tier": "cheap",
                "description": "🆕 Balanced, efficient (1M)"
            }
        }
    },
    "moonshot": {
        "display_name": "Moonshot AI",
        "api_key_env_var": "MOONSHOT_API_KEY",
        "models": {
            "kimi-k2-thinking": {
                "display_name": "Kimi K2 Thinking",
                "cost_tier": "cheap",
                "description": "Advanced reasoning (128K)"
            },
            "kimi-k2-thinking-turbo": {
                "display_name": "Kimi K2 Thinking Turbo",
                "cost_tier": "cheap",
                "description": "Fast reasoning (128K)"
            },
            "kimi-k2-0905-preview": {
                "display_name": "Kimi K2 Preview",
                "cost_tier": "cheap",
                "description": "Preview model (128K)"
            },
            "kimi-k2-turbo-preview": {
                "display_name": "Kimi K2 Turbo Preview",
                "cost_tier": "cheap",
                "description": "Fast, cost-effective (128K)"
            }
        }
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "api_key_env_var": "DEEPSEEK_API_KEY",
        "models": {
            "deepseek-chat": {
                "display_name": "DeepSeek Chat",
                "cost_tier": "cheap",
                "description": "🆕 V3, ultra cost-effective (128K)"
            },
            "deepseek-coder": {
                "display_name": "DeepSeek Coder",
                "cost_tier": "cheap",
                "description": "🆕 V2, best for coding (128K)"
            },
            "deepseek-reasoner": {
                "display_name": "DeepSeek Reasoner",
                "cost_tier": "cheap",
                "description": "R1, advanced reasoning (64K)"
            }
        }
    }
}


def get_model_metadata(provider: str, model: str) -> dict:
    """
    Get metadata for a specific model.

    v0.9.3: Now uses catalog for descriptions and cost tier when available

    Args:
        provider: Provider name
        model: Model name

    Returns:
        Dictionary with display_name, cost_tier, description

    Example:
        >>> meta = get_model_metadata("openai", "gpt-5.1")
        >>> meta["display_name"]
        'GPT-5.1'
        >>> 'complex tasks' in meta["description"]
        True
        >>> meta["cost_tier"]
        'premium'
    """
    # Get base metadata from MODEL_METADATA
    provider_meta = MODEL_METADATA.get(provider, {})
    base_meta = provider_meta.get("models", {}).get(model, {
        "display_name": model,
        "cost_tier": "standard",
        "description": "Model description not available"
    }).copy()  # Make a copy to avoid modifying the original

    # Try to enrich with catalog data (description and cost tier)
    catalog_info = _get_catalog_info(provider, model)
    if catalog_info:
        if catalog_info.get("description"):
            base_meta["description"] = catalog_info["description"]
        if catalog_info.get("tier"):
            base_meta["cost_tier"] = catalog_info["tier"]

    return base_meta


def get_provider_metadata(provider: str) -> dict:
    """
    Get metadata for a specific provider.

    Args:
        provider: Provider name

    Returns:
        Dictionary with display_name, api_key_env_var

    Example:
        >>> meta = get_provider_metadata("openai")
        >>> meta["display_name"]
        'OpenAI'
        >>> meta["api_key_env_var"]
        'OPENAI_API_KEY'
    """
    return MODEL_METADATA.get(provider, {
        "display_name": provider.title(),
        "api_key_env_var": f"{provider.upper()}_API_KEY"
    })
