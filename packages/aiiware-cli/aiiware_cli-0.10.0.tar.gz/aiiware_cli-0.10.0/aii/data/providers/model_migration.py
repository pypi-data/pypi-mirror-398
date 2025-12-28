# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Model Migration - Handle deprecated model migration and warnings."""


import logging
from typing import Optional

logger = logging.getLogger(__name__)


# v0.9.3: Deprecated model migration map
# Maps old/deprecated models → recommended replacements
DEPRECATED_MODEL_MAP = {
    # OpenAI deprecated models
    "gpt-3.5-turbo": {
        "replacement": "gpt-4o-mini",
        "reason": "gpt-3.5-turbo retired Sept 2024",
        "benefit": "60% lower cost, better quality"
    },
    "gpt-3.5-turbo-16k": {
        "replacement": "gpt-4o-mini",
        "reason": "gpt-3.5-turbo-16k retired Sept 2024",
        "benefit": "similar cost, better quality, larger context (128K)"
    },
    "gpt-4": {
        "replacement": "gpt-4o",
        "reason": "gpt-4 is legacy, gpt-4o is faster and cheaper",
        "benefit": "similar cost, much faster, multimodal"
    },
    "gpt-4-turbo": {
        "replacement": "gpt-4o",
        "reason": "gpt-4-turbo superseded by gpt-4o",
        "benefit": "similar performance, lower cost"
    },
    "gpt-4-turbo-preview": {
        "replacement": "gpt-4o",
        "reason": "preview version superseded by stable gpt-4o",
        "benefit": "stable release, lower cost"
    },
    "gpt-5": {
        "replacement": "gpt-5.1",
        "reason": "gpt-5 superseded by gpt-5.1 with adaptive reasoning",
        "benefit": "adaptive reasoning, faster, same price"
    },
    "gpt-5.1-instant": {
        "replacement": "gpt-5.1",
        "reason": "gpt-5.1-instant does not exist (404)",
        "benefit": "verified working model"
    },
    "gpt-5.1-codex": {
        "replacement": "gpt-4.1",
        "reason": "gpt-5.1-codex does not exist (404)",
        "benefit": "verified coding model, 1M context"
    },
    "gpt-5.1-codex-mini": {
        "replacement": "gpt-4.1-mini",
        "reason": "gpt-5.1-codex-mini does not exist (404)",
        "benefit": "verified coding model, cost-effective"
    },

    # Anthropic deprecated models
    "claude-3-opus-20240229": {
        "replacement": "claude-opus-4-1",
        "reason": "retires Jan 5, 2026",
        "benefit": "latest Opus, same pricing"
    },
    "claude-3-sonnet-20240229": {
        "replacement": "claude-sonnet-4-5",
        "reason": "retired July 21, 2025",
        "benefit": "best coding model, same pricing"
    },
    "claude-3-haiku-20240307": {
        "replacement": "claude-haiku-4-5",
        "reason": "legacy Claude 3, outdated",
        "benefit": "faster, more capable"
    },
    "claude-haiku-3.5": {
        "replacement": "claude-haiku-4-5",
        "reason": "older Haiku version",
        "benefit": "better performance, newer"
    },

    # Google Gemini deprecated models
    "gemini-pro": {
        "replacement": "gemini-2.5-pro",
        "reason": "legacy Gemini Pro superseded",
        "benefit": "2M context, better quality"
    },
    "gemini-pro-vision": {
        "replacement": "gemini-2.5-flash",
        "reason": "retired July 12, 2024",
        "benefit": "97% cheaper, better multimodal"
    },
}


def get_replacement_model(deprecated_model: str) -> Optional[dict]:
    """
    Get replacement info for a deprecated model.

    Args:
        deprecated_model: Model ID that may be deprecated

    Returns:
        Dict with 'replacement', 'reason', 'benefit' keys, or None if not deprecated

    Example:
        >>> info = get_replacement_model("gpt-3.5-turbo")
        >>> info['replacement']
        'gpt-4o-mini'
        >>> info['benefit']
        '60% lower cost, better quality'
    """
    return DEPRECATED_MODEL_MAP.get(deprecated_model)


def migrate_model_if_needed(model: str, warn: bool = True) -> str:
    """
    Migrate a model to its replacement if deprecated.

    Args:
        model: Model ID to check
        warn: Whether to log a warning (default True)

    Returns:
        Replacement model if deprecated, otherwise original model

    Example:
        >>> migrate_model_if_needed("gpt-3.5-turbo")
        'gpt-4o-mini'  # Also logs warning
        >>> migrate_model_if_needed("gpt-4o")
        'gpt-4o'  # Not deprecated, no change
    """
    migration_info = get_replacement_model(model)

    if migration_info is None:
        # Not deprecated, return as-is
        return model

    replacement = migration_info["replacement"]
    reason = migration_info["reason"]
    benefit = migration_info["benefit"]

    if warn:
        logger.warning(
            f"\n⚠️  Model '{model}' is deprecated ({reason}).\n"
            f"   Auto-migrating to '{replacement}'.\n"
            f"   Benefit: {benefit}\n"
            f"   Run 'aii config model' to update your configuration."
        )

    return replacement


def is_deprecated(model: str) -> bool:
    """
    Check if a model is deprecated.

    Args:
        model: Model ID to check

    Returns:
        True if model is deprecated, False otherwise

    Example:
        >>> is_deprecated("gpt-3.5-turbo")
        True
        >>> is_deprecated("gpt-4o")
        False
    """
    return model in DEPRECATED_MODEL_MAP


def get_all_deprecated_models() -> list[str]:
    """
    Get list of all deprecated model IDs.

    Returns:
        List of deprecated model IDs

    Example:
        >>> models = get_all_deprecated_models()
        >>> "gpt-3.5-turbo" in models
        True
    """
    return list(DEPRECATED_MODEL_MAP.keys())
