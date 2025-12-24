"""
Deduplication cache for preventing duplicate operations on retry.

Used for non-idempotent operations like file uploads and resource creation.
"""

import time
from typing import Any, Callable


class DeduplicationCache:
    """
    Cache to prevent duplicate operations on retry.

    Useful for non-idempotent operations where retries would create duplicates:
    - File uploads (use content hash as key)
    - Resource creation (use request_id as key)
    - Chat messages (use chat_id + message_id as key)
    """

    def __init__(self, ttl: int = 3600):
        """
        Initialize deduplication cache.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self._cache: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl

    def get_or_create(
        self,
        cache_key: str,
        factory_func: Callable[[], Any],
    ) -> Any:
        """
        Get cached result or create new one.

        Args:
            cache_key: Unique key for operation (e.g., "upload:sha256hash")
            factory_func: Function to call if cache miss

        Returns:
            Cached or new result
        """
        # Clean expired entries
        self._clean_expired()

        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            return result

        # Create new result
        result = factory_func()
        self._cache[cache_key] = (result, time.time())
        return result

    def invalidate(self, cache_key: str):
        """
        Invalidate specific cache entry.

        Args:
            cache_key: Key to invalidate
        """
        if cache_key in self._cache:
            del self._cache[cache_key]

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        self._clean_expired()
        return {
            "size": len(self._cache),
            "ttl": self._ttl,
            "keys": list(self._cache.keys()),
        }

    def _clean_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
