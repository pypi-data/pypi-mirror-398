# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Model Catalog - Load structured model information from JSON catalog."""


import json
from pathlib import Path
from typing import Optional


# v0.9.3: Load catalog from bundled JSON file
_CATALOG_FILE = Path(__file__).parent.parent.parent / "config" / "llm-models.catalog.json"

# Cache the loaded catalog
_CATALOG_CACHE: Optional[list[dict]] = None


def load_catalog() -> list[dict]:
    """
    Load model catalog from JSON file.

    Returns:
        List of model dictionaries with provider, model, description, pricing, tier

    Example:
        >>> catalog = load_catalog()
        >>> len(catalog) >= 24
        True
        >>> catalog[0]['provider']
        'openai'
    """
    global _CATALOG_CACHE

    if _CATALOG_CACHE is not None:
        return _CATALOG_CACHE

    try:
        with open(_CATALOG_FILE, 'r', encoding='utf-8') as f:
            _CATALOG_CACHE = json.load(f)
        return _CATALOG_CACHE
    except FileNotFoundError:
        # Fallback: return empty list if catalog file not found
        return []
    except json.JSONDecodeError:
        # Fallback: return empty list if JSON is invalid
        return []


def get_model_info(provider: str, model: str) -> Optional[dict]:
    """
    Get model information from catalog.

    Args:
        provider: Provider name (e.g., 'openai', 'anthropic')
        model: Model ID (e.g., 'gpt-5.1', 'claude-sonnet-4-5')

    Returns:
        Model dict with description, pricing, tier, or None if not found

    Example:
        >>> info = get_model_info('openai', 'gpt-5.1')
        >>> info['description']
        'Best overall quality for complex tasks, analysis, and long-form answers'
        >>> info['input_price_per_million']
        1.25
    """
    catalog = load_catalog()

    for entry in catalog:
        if entry.get('provider') == provider and entry.get('model') == model:
            return entry

    return None


def get_model_pricing(model: str) -> Optional[dict]:
    """
    Get pricing for a specific model (provider-agnostic lookup).

    Args:
        model: Model ID (e.g., 'gpt-5.1', 'claude-sonnet-4-5')

    Returns:
        Dict with 'input' and 'output' keys for pricing per 1M tokens, or None

    Example:
        >>> pricing = get_model_pricing('gpt-5.1')
        >>> pricing['input']
        1.25
        >>> pricing['output']
        10.0
    """
    catalog = load_catalog()

    for entry in catalog:
        if entry.get('model') == model:
            return {
                'input': entry.get('input_price_per_million', 0.0),
                'output': entry.get('output_price_per_million', 0.0)
            }

    return None


def get_all_models_by_provider() -> dict[str, list[dict]]:
    """
    Get all models grouped by provider.

    Returns:
        Dictionary mapping provider name to list of model entries

    Example:
        >>> models = get_all_models_by_provider()
        >>> 'openai' in models
        True
        >>> len(models['openai']) >= 8
        True
    """
    catalog = load_catalog()
    result: dict[str, list[dict]] = {}

    for entry in catalog:
        provider = entry.get('provider')
        if provider not in result:
            result[provider] = []
        result[provider].append(entry)

    return result
