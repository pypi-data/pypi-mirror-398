"""
Task Planning Cache - In-memory caching for pre-fetched resources

This module provides caching functionality to avoid repeated database calls
for frequently accessed resources (agents, teams, environments, queues).

Features:
- TTL-based cache expiration (default 5 minutes)
- Per-organization caching
- Thread-safe operations
"""

from typing import Optional, Dict, Any
import time
import threading
import structlog

logger = structlog.get_logger()


# ============================================================================
# Cache Configuration
# ============================================================================

DEFAULT_CACHE_TTL = 300  # 5 minutes


# ============================================================================
# Thread-Safe Cache Implementation
# ============================================================================

class PrefetchCache:
    """
    Thread-safe in-memory cache for pre-fetched organization resources.

    Features:
    - TTL-based expiration
    - Per-organization isolation
    - Automatic cleanup of expired entries
    """

    def __init__(self, ttl_seconds: int = DEFAULT_CACHE_TTL):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._ttl = ttl_seconds

    def get(self, organization_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached pre-fetched data for an organization if still valid.

        Args:
            organization_id: Organization identifier

        Returns:
            Cached data dict or None if not found/expired
        """
        cache_key = f"prefetch_{organization_id}"

        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and time.time() - cached.get("timestamp", 0) < self._ttl:
                logger.info("prefetch_cache_hit", organization_id=organization_id[:8])
                return cached.get("data")

            # Clean up expired entry if exists
            if cached:
                del self._cache[cache_key]
                logger.debug("prefetch_cache_expired", organization_id=organization_id[:8])

            return None

    def set(self, organization_id: str, data: Dict[str, Any]) -> None:
        """
        Cache pre-fetched data for an organization.

        Args:
            organization_id: Organization identifier
            data: Data to cache (agents, teams, environments, queues)
        """
        cache_key = f"prefetch_{organization_id}"

        with self._lock:
            self._cache[cache_key] = {
                "timestamp": time.time(),
                "data": data
            }
            logger.info("prefetch_cache_set", organization_id=organization_id[:8])

    def invalidate(self, organization_id: str) -> bool:
        """
        Invalidate (remove) cached data for an organization.

        Args:
            organization_id: Organization identifier

        Returns:
            True if entry was removed, False if not found
        """
        cache_key = f"prefetch_{organization_id}"

        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.info("prefetch_cache_invalidated", organization_id=organization_id[:8])
                return True
            return False

    def clear(self) -> int:
        """
        Clear all cached data.

        Returns:
            Number of entries cleared
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info("prefetch_cache_cleared", entries_cleared=count)
            return count

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache.

        Returns:
            Number of entries removed
        """
        current_time = time.time()
        removed = 0

        with self._lock:
            expired_keys = [
                key for key, value in self._cache.items()
                if current_time - value.get("timestamp", 0) >= self._ttl
            ]

            for key in expired_keys:
                del self._cache[key]
                removed += 1

            if removed > 0:
                logger.info("prefetch_cache_cleanup", entries_removed=removed)

        return removed

    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (size, oldest entry age, etc.)
        """
        current_time = time.time()

        with self._lock:
            if not self._cache:
                return {"size": 0, "oldest_age_seconds": 0, "ttl_seconds": self._ttl}

            ages = [
                current_time - v.get("timestamp", current_time)
                for v in self._cache.values()
            ]

            return {
                "size": len(self._cache),
                "oldest_age_seconds": max(ages) if ages else 0,
                "newest_age_seconds": min(ages) if ages else 0,
                "ttl_seconds": self._ttl
            }


# ============================================================================
# Global Cache Instance (Singleton)
# ============================================================================

_prefetch_cache: Optional[PrefetchCache] = None
_cache_lock = threading.Lock()


def get_prefetch_cache() -> PrefetchCache:
    """
    Get the global prefetch cache instance (singleton).

    Returns:
        PrefetchCache instance
    """
    global _prefetch_cache

    if _prefetch_cache is None:
        with _cache_lock:
            if _prefetch_cache is None:
                _prefetch_cache = PrefetchCache()

    return _prefetch_cache


# ============================================================================
# Convenience Functions (backward compatible)
# ============================================================================

def get_cached_prefetch(organization_id: str) -> Optional[Dict[str, Any]]:
    """Get cached pre-fetched data for an organization if still valid."""
    return get_prefetch_cache().get(organization_id)


def set_cached_prefetch(organization_id: str, data: Dict[str, Any]) -> None:
    """Cache pre-fetched data for an organization."""
    get_prefetch_cache().set(organization_id, data)


def invalidate_prefetch_cache(organization_id: str) -> bool:
    """Invalidate cached data for an organization."""
    return get_prefetch_cache().invalidate(organization_id)


def clear_prefetch_cache() -> int:
    """Clear all cached data."""
    return get_prefetch_cache().clear()
