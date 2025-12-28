# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Web Search Integration with multiple providers

Supports:
- DuckDuckGo (free, no API key required) - Primary provider
- Brave Search (premium, API key required)
- Google Custom Search (premium, API key + CX required)

Features:
- LRU cache with TTL for search results
- Rate limiting for API protection
- Comprehensive error handling
- Protocol-based extensibility

SOLID Principles:
- Single Responsibility: Each provider handles one search engine
- Open/Closed: Easy to add new providers without modifying existing code
- Liskov Substitution: All providers honor WebSearchProvider protocol
- Interface Segregation: Minimal protocol interface
- Dependency Inversion: Depend on abstractions, not concrete implementations
"""


from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from collections import OrderedDict
import asyncio
import logging
import warnings
import ssl

import aiohttp
import certifi

# Suppress warnings from duckduckgo_search package
warnings.filterwarnings("ignore", message=".*duckduckgo_search.*renamed.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed.*")


def create_ssl_context() -> ssl.SSLContext:
    """Create SSL context with certifi certificates for HTTPS requests.

    This fixes SSL certificate verification issues on macOS/Anaconda
    by using certifi's bundled CA certificates instead of system defaults.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    return ssl_context

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Web search result"""

    title: str
    url: str
    snippet: str
    timestamp: datetime | None = None
    source: str = "web"
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "metadata": self.metadata
        }


class SearchCache:
    """
    LRU cache with TTL for search results.

    SOLID: Single Responsibility - only responsible for caching logic
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize search cache.

        Args:
            max_size: Maximum number of cached queries (default: 100)
            ttl_seconds: Time-to-live for cached results in seconds (default: 1 hour)
        """
        self._cache: OrderedDict[str, tuple[list[SearchResult], datetime]] = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)

    def _make_key(self, query: str, num_results: int, time_range: Optional[str]) -> str:
        """Generate cache key from search parameters"""
        return f"{query}:{num_results}:{time_range or 'none'}"

    def get(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> Optional[list[SearchResult]]:
        """
        Retrieve cached search results if available and not expired.

        Returns:
            Cached results or None if not found/expired
        """
        key = self._make_key(query, num_results, time_range)

        if key not in self._cache:
            return None

        results, timestamp = self._cache[key]

        # Check if expired
        if datetime.now() - timestamp > self._ttl:
            del self._cache[key]
            return None

        # Move to end (LRU)
        self._cache.move_to_end(key)

        logger.debug(f"Cache hit for query: {query[:50]}...")
        return results

    def set(
        self,
        query: str,
        results: list[SearchResult],
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> None:
        """
        Store search results in cache.

        Implements LRU eviction when cache is full.
        """
        key = self._make_key(query, num_results, time_range)

        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._cache.popitem(last=False)

        self._cache[key] = (results, datetime.now())
        self._cache.move_to_end(key)

        logger.debug(f"Cached {len(results)} results for query: {query[:50]}...")

    def clear(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        logger.debug("Search cache cleared")


class RateLimiter:
    """
    Simple rate limiter for API requests.

    SOLID: Single Responsibility - only handles rate limiting logic
    """

    def __init__(self, min_interval_seconds: float = 1.0):
        """
        Initialize rate limiter.

        Args:
            min_interval_seconds: Minimum time between requests (default: 1 second)
        """
        self._min_interval = min_interval_seconds
        self._last_request_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def wait_if_needed(self) -> None:
        """Wait if necessary to respect rate limit"""
        async with self._lock:
            if self._last_request_time is not None:
                elapsed = asyncio.get_event_loop().time() - self._last_request_time
                if elapsed < self._min_interval:
                    wait_time = self._min_interval - elapsed
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)

            self._last_request_time = asyncio.get_event_loop().time()


class SearchError(Exception):
    """Base exception for search-related errors"""
    pass


class WebSearchProvider(ABC):
    """Abstract web search provider"""

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> list[SearchResult]:
        """Execute search and return results"""
        pass

    async def health_check(self) -> bool:
        """Check if the search service is available"""
        try:
            results = await self.search("test", num_results=1)
            return len(results) > 0
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False


class DuckDuckGoSearchProvider(WebSearchProvider):
    """
    DuckDuckGo search provider (free, no API key required)

    Features:
    - Free, no API key required
    - Built-in rate limiting (1 req/sec)
    - LRU cache with 1-hour TTL
    - Comprehensive error handling

    SOLID Principles:
    - Single Responsibility: Only handles DuckDuckGo search operations
    - Open/Closed: Can be extended without modifying base class
    - Liskov Substitution: Fully honors WebSearchProvider protocol
    - Dependency Inversion: Depends on abstractions (SearchCache, RateLimiter)
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_size: int = 100,
        cache_ttl_seconds: int = 3600,
        rate_limit_seconds: float = 1.0
    ):
        """
        Initialize DuckDuckGo search provider.

        Args:
            use_cache: Enable result caching (default: True)
            cache_size: Maximum cache entries (default: 100)
            cache_ttl_seconds: Cache TTL in seconds (default: 3600 = 1 hour)
            rate_limit_seconds: Minimum time between requests (default: 1.0s)
        """
        try:
            import warnings
            import sys
            import os
            # Suppress ALL warnings during import and instantiation
            # Also redirect stderr temporarily to suppress print-based warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Temporarily redirect stderr to devnull
                stderr_backup = sys.stderr
                try:
                    sys.stderr = open(os.devnull, 'w')
                    from duckduckgo_search import DDGS
                    self._ddgs = DDGS()
                finally:
                    sys.stderr.close() if sys.stderr != stderr_backup else None
                    sys.stderr = stderr_backup
        except ImportError as e:
            raise ImportError(
                "duckduckgo-search library not installed. "
                "Install with: pip install duckduckgo-search"
            ) from e

        self._cache = SearchCache(cache_size, cache_ttl_seconds) if use_cache else None
        self._rate_limiter = RateLimiter(rate_limit_seconds)
        self._use_cache = use_cache

        logger.info(
            f"DuckDuckGoSearchProvider initialized "
            f"(cache={'enabled' if use_cache else 'disabled'}, "
            f"rate_limit={rate_limit_seconds}s)"
        )

    async def search(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> list[SearchResult]:
        """
        Search DuckDuckGo with the given query.

        Args:
            query: Search query string
            num_results: Maximum results to return (1-50, default: 5)
            time_range: Time filter ('d'=day, 'w'=week, 'm'=month, 'y'=year)

        Returns:
            List of SearchResult objects

        Raises:
            ValueError: If query is empty or parameters invalid
            SearchError: If search operation fails
        """
        # Validation
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        if num_results < 1 or num_results > 50:
            raise ValueError("num_results must be between 1 and 50")

        query = query.strip()

        # Check cache first
        if self._cache:
            cached_results = self._cache.get(query, num_results, time_range)
            if cached_results:
                logger.info(f"Returning cached results for: {query[:50]}...")
                return cached_results[:num_results]

        # Rate limiting
        await self._rate_limiter.wait_if_needed()

        # Perform search
        try:
            logger.info(f"Searching DuckDuckGo: {query[:50]}... (num_results={num_results})")

            # Map time_range to DuckDuckGo format
            timelimit = None
            if time_range:
                time_map = {
                    'day': 'd',
                    'week': 'w',
                    'month': 'm',
                    'year': 'y',
                    'd': 'd',
                    'w': 'w',
                    'm': 'm',
                    'y': 'y'
                }
                timelimit = time_map.get(time_range.lower())

            # Execute search in thread pool (DDGS is synchronous)
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self._ddgs.text(
                    query,
                    max_results=num_results,
                    safesearch='moderate',
                    timelimit=timelimit
                ))
            )

            # Convert to SearchResult objects
            search_results = [
                SearchResult(
                    title=r.get('title', ''),
                    url=r.get('href', ''),
                    snippet=r.get('body', ''),
                    source='duckduckgo',
                    timestamp=datetime.now(),
                    metadata={}
                )
                for r in results
            ]

            logger.info(f"Found {len(search_results)} results for: {query[:50]}...")

            # Cache results
            if self._cache and search_results:
                self._cache.set(query, search_results, num_results, time_range)

            return search_results

        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {e}")
            raise SearchError(f"Search failed: {str(e)}") from e


class BraveSearchProvider(WebSearchProvider):
    """Brave Search API provider"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> list[SearchResult]:
        """Search using Brave Search API"""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }

        params = {
            "q": query,
            "count": min(num_results, 20),  # Brave API limit
            "offset": 0,
            "mkt": "en-US",
            "safesearch": "moderate",
        }

        # Add time range filter if specified (Brave uses 'freshness' parameter)
        if time_range:
            # Map to Brave's freshness values
            freshness_map = {
                'day': 'pd',  # past day
                'week': 'pw',  # past week
                'month': 'pm',  # past month
                'year': 'py',  # past year
                'd': 'pd',
                'w': 'pw',
                'm': 'pm',
                'y': 'py'
            }
            if time_range.lower() in freshness_map:
                params['freshness'] = freshness_map[time_range.lower()]

        try:
            # Create SSL context with certifi certificates (fixes macOS SSL issues)
            ssl_context = create_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Brave Search API error: {response.status}")

                    data = await response.json()
                    return self._parse_brave_results(data)

        except Exception as e:
            raise RuntimeError(f"Brave search failed: {str(e)}") from e

    def _parse_brave_results(self, data: dict[str, Any]) -> list[SearchResult]:
        """Parse Brave Search API response"""
        results = []
        web_results = data.get("web", {}).get("results", [])

        for result in web_results:
            search_result = SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("description", ""),
                source="brave",
                metadata={
                    "age": result.get("age"),
                    "language": result.get("language"),
                    "family_friendly": result.get("family_friendly", True),
                },
            )
            results.append(search_result)

        return results


class GoogleSearchProvider(WebSearchProvider):
    """Google Custom Search API provider"""

    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx  # Custom Search Engine ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None
    ) -> list[SearchResult]:
        """Search using Google Custom Search API"""
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": min(num_results, 10),  # Google API limit per request
        }

        # Add date restrict if time_range specified
        if time_range:
            # Google uses dateRestrict parameter (d[number], w[number], m[number], y[number])
            date_map = {
                'day': 'd1',
                'week': 'w1',
                'month': 'm1',
                'year': 'y1',
                'd': 'd1',
                'w': 'w1',
                'm': 'm1',
                'y': 'y1'
            }
            if time_range.lower() in date_map:
                params['dateRestrict'] = date_map[time_range.lower()]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(
                            f"Google Search API error: {response.status}"
                        )

                    data = await response.json()
                    return self._parse_google_results(data)

        except Exception as e:
            raise RuntimeError(f"Google search failed: {str(e)}") from e

    def _parse_google_results(self, data: dict[str, Any]) -> list[SearchResult]:
        """Parse Google Custom Search API response"""
        results = []
        items = data.get("items", [])

        for item in items:
            search_result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="google",
                metadata={
                    "display_link": item.get("displayLink"),
                    "formatted_url": item.get("formattedUrl"),
                },
            )
            results.append(search_result)

        return results


class WebSearchClient:
    """Main web search client with multiple provider support"""

    def __init__(self, provider: WebSearchProvider):
        self.provider = provider
        self.session: aiohttp.ClientSession | None = None

    @classmethod
    def create_duckduckgo_client(
        cls,
        use_cache: bool = True,
        cache_size: int = 100,
        cache_ttl_seconds: int = 3600,
        rate_limit_seconds: float = 1.0
    ) -> "WebSearchClient":
        """
        Create client with DuckDuckGo Search provider (free, no API key required)

        Args:
            use_cache: Enable result caching (default: True)
            cache_size: Maximum cache entries (default: 100)
            cache_ttl_seconds: Cache TTL in seconds (default: 3600)
            rate_limit_seconds: Minimum time between requests (default: 1.0s)
        """
        return cls(DuckDuckGoSearchProvider(
            use_cache=use_cache,
            cache_size=cache_size,
            cache_ttl_seconds=cache_ttl_seconds,
            rate_limit_seconds=rate_limit_seconds
        ))

    @classmethod
    def create_brave_client(cls, api_key: str) -> "WebSearchClient":
        """Create client with Brave Search provider (requires API key)"""
        return cls(BraveSearchProvider(api_key))

    @classmethod
    def create_google_client(cls, api_key: str, cx: str) -> "WebSearchClient":
        """Create client with Google Custom Search provider (requires API key + CX)"""
        return cls(GoogleSearchProvider(api_key, cx))

    async def search(
        self,
        query: str,
        num_results: int = 5,
        time_range: Optional[str] = None,
        filter_duplicates: bool = True
    ) -> list[SearchResult]:
        """
        Execute web search

        Args:
            query: Search query string
            num_results: Maximum results to return (default: 5)
            time_range: Optional time filter ('day', 'week', 'month', 'year')
            filter_duplicates: Remove duplicate URLs (default: True)

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []

        results = await self.provider.search(query.strip(), num_results, time_range)

        if filter_duplicates:
            results = self._remove_duplicates(results)

        return results

    async def health_check(self) -> bool:
        """Check if the search provider is available"""
        return await self.provider.health_check()

    async def fetch_content(self, url: str) -> str | None:
        """Fetch full content from a URL"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Aii-Bot/1.0 (https://github.com/aiiware/aii)"},
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._extract_text_content(content)
                return None

        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return None

    async def search_and_fetch(
        self, query: str, num_results: int = 3, fetch_full_content: bool = False
    ) -> list[dict[str, Any]]:
        """Search and optionally fetch full content"""
        search_results = await self.search(query, num_results)

        if not fetch_full_content:
            return [
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                }
                for result in search_results
            ]

        # Fetch full content for each result
        enriched_results = []
        for result in search_results:
            full_content = await self.fetch_content(result.url)

            enriched_results.append(
                {
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "full_content": full_content,
                    "source": result.source,
                    "metadata": result.metadata,
                }
            )

        return enriched_results

    async def close(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    def _remove_duplicates(self, results: list[SearchResult]) -> list[SearchResult]:
        """Remove duplicate results based on URL"""
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results

    def _extract_text_content(self, html_content: str) -> str:
        """Extract readable text from HTML content"""
        # This is a simplified text extraction
        # In production, you'd want to use libraries like BeautifulSoup or readability
        try:
            # Remove common HTML tags and scripts
            import re

            # Remove script and style tags
            html_content = re.sub(
                r"<script.*?</script>",
                "",
                html_content,
                flags=re.DOTALL | re.IGNORECASE,
            )
            html_content = re.sub(
                r"<style.*?</style>", "", html_content, flags=re.DOTALL | re.IGNORECASE
            )

            # Remove HTML tags
            text = re.sub(r"<[^>]+>", "", html_content)

            # Clean up whitespace
            text = re.sub(r"\\s+", " ", text)
            text = text.strip()

            # Limit length
            if len(text) > 5000:
                text = text[:5000] + "..."

            return text

        except Exception:
            return (
                html_content[:1000] + "..."
                if len(html_content) > 1000
                else html_content
            )


def create_web_search_client_from_config(config_manager=None) -> WebSearchClient:
    """
    Create web search client from configuration.

    SOLID: Dependency Inversion - depends on config interface, not concrete implementation

    Args:
        config_manager: ConfigManager instance (if None, uses default DuckDuckGo)

    Returns:
        WebSearchClient instance configured per user settings

    Example:
        >>> from aii.config.manager import ConfigManager
        >>> config = ConfigManager()
        >>> client = create_web_search_client_from_config(config)
        >>> results = await client.search("Python programming")
    """
    # Default to DuckDuckGo if no config provided
    if config_manager is None:
        logger.info("No config provided, using default DuckDuckGo client")
        return WebSearchClient.create_duckduckgo_client()

    # Get web search configuration
    web_search_config = config_manager.get("web_search", {})
    provider = web_search_config.get("provider", "duckduckgo").lower()

    logger.info(f"Creating web search client for provider: {provider}")

    if provider == "duckduckgo":
        # DuckDuckGo - free, no API key required
        return WebSearchClient.create_duckduckgo_client(
            use_cache=web_search_config.get("cache_enabled", True),
            cache_size=web_search_config.get("cache_size", 100),
            cache_ttl_seconds=web_search_config.get("cache_ttl_seconds", 3600),
            rate_limit_seconds=web_search_config.get("rate_limit_seconds", 1.0)
        )

    elif provider == "brave":
        # Brave Search - requires API key
        # Support both old (brave_api_key) and new (brave_search_api_key) key names for backwards compatibility
        api_key = config_manager.get_secret("brave_search_api_key") or config_manager.get_secret("brave_api_key")
        if not api_key:
            logger.debug(
                "Brave Search API key not found, falling back to DuckDuckGo"
            )
            return WebSearchClient.create_duckduckgo_client()

        return WebSearchClient.create_brave_client(api_key)

    elif provider == "google":
        # Google Custom Search - requires API key + CX
        api_key = config_manager.get_secret("google_search_api_key")
        cx = config_manager.get_secret("google_search_cx")

        if not api_key or not cx:
            logger.warning(
                "Google Search credentials not found in secrets. "
                "Falling back to DuckDuckGo. "
                "Set google_search_api_key and google_search_cx in ~/.aii/secrets.yaml"
            )
            return WebSearchClient.create_duckduckgo_client()

        return WebSearchClient.create_google_client(api_key, cx)

    else:
        logger.warning(
            f"Unknown search provider: {provider}. "
            f"Supported: duckduckgo, brave, google. "
            f"Falling back to DuckDuckGo."
        )
        return WebSearchClient.create_duckduckgo_client()


# Convenience exports
__all__ = [
    'SearchResult',
    'SearchError',
    'SearchCache',
    'RateLimiter',
    'WebSearchProvider',
    'DuckDuckGoSearchProvider',
    'BraveSearchProvider',
    'GoogleSearchProvider',
    'WebSearchClient',
    'create_web_search_client_from_config'
]
