# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""API key authentication for Aii API server."""


from aii.config.manager import ConfigManager


class APIKeyAuth:
    """API key authentication handler."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.api_keys = self._load_api_keys()

    def _load_api_keys(self) -> set[str]:
        """Load API keys from config."""
        keys = self.config.get("api.keys", [])
        return set(keys)

    def verify_key(self, api_key: str) -> bool:
        """Verify API key is valid."""
        return api_key in self.api_keys

    def add_key(self, api_key: str):
        """Add new API key and persist to config."""
        self.api_keys.add(api_key)

        # Persist to config
        keys = list(self.api_keys)
        self.config.set("api.keys", keys)
