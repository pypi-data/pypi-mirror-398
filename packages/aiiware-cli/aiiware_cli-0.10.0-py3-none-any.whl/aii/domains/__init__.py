# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Domain operations registry for Aii CLI.

Domains organize client-side operations that execute locally and interact with
the stateless Aii Server for LLM capabilities.

Architecture:
- Domain: Collection of related operations (git, code, content, sys)
- Operation: Single-purpose handler that owns prompts, context, and execution
- Client: Stateless LLM execution engine (no domain knowledge)

Example:
    from aii.domains import register_domain, get_domain

    # Register domains at startup
    register_domain("git", GitDomain())

    # Get domain and execute operation
    domain = get_domain("git")
    operation = domain.get_operation("commit")
    await operation.execute(config, client)
"""

from typing import Dict, List, Optional, Any

# Global domain registry
_DOMAIN_REGISTRY: Dict[str, Any] = {}


def register_domain(name: str, domain_class: Any) -> None:
    """
    Register a domain in the global registry.

    Args:
        name: Domain name (e.g., "git", "code", "content")
        domain_class: Domain class instance

    Example:
        register_domain("git", GitDomain())
    """
    _DOMAIN_REGISTRY[name] = domain_class


def get_domain(name: str) -> Optional[Any]:
    """
    Get domain by name from the registry.

    Args:
        name: Domain name

    Returns:
        Domain instance or None if not found
    """
    return _DOMAIN_REGISTRY.get(name)


def list_domains() -> List[str]:
    """
    List all registered domains.

    Returns:
        List of domain names
    """
    return list(_DOMAIN_REGISTRY.keys())


def clear_domains() -> None:
    """
    Clear all registered domains (for testing).
    """
    _DOMAIN_REGISTRY.clear()


__all__ = [
    "register_domain",
    "get_domain",
    "list_domains",
    "clear_domains",
]
