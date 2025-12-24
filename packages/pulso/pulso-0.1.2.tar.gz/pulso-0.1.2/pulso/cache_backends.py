"""Cache backend implementations for different storage systems."""

import json
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cache entry by key."""
        pass

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set cache entry."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete cache entry."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries matching pattern."""
        pass


class RedisBackend(CacheBackend):
    """Redis-based cache backend for distributed caching."""

    def __init__(self, redis_url: str, session_id: str = "default"):
        try:
            import redis
        except ImportError:
            raise ImportError(
                "Redis backend requires redis package. Install with: pip install redis"
            )

        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.session_id = session_id

    def _make_key(self, key: str) -> str:
        """Create session-scoped Redis key."""
        return f"pulso:{self.session_id}:{key}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cache entry from Redis."""
        redis_key = self._make_key(key)
        data = self.redis.get(redis_key)

        if data is None:
            return None

        return json.loads(data.decode('utf-8'))

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set cache entry in Redis."""
        redis_key = self._make_key(key)
        data = json.dumps(value).encode('utf-8')

        if ttl:
            self.redis.setex(redis_key, ttl, data)
        else:
            self.redis.set(redis_key, data)

    def delete(self, key: str) -> None:
        """Delete cache entry from Redis."""
        redis_key = self._make_key(key)
        self.redis.delete(redis_key)

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        redis_key = self._make_key(key)
        return bool(self.redis.exists(redis_key))

    def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries matching pattern."""
        if pattern:
            search_pattern = self._make_key(pattern)
        else:
            search_pattern = self._make_key("*")

        # Get all keys matching pattern
        keys = self.redis.keys(search_pattern)

        # Delete in batches
        if keys:
            self.redis.delete(*keys)

    def get_html(self, key: str) -> Optional[str]:
        """Get HTML content from Redis."""
        html_key = f"{key}:html"
        redis_key = self._make_key(html_key)
        data = self.redis.get(redis_key)

        if data is None:
            return None

        return data.decode('utf-8')

    def set_html(self, key: str, html: str, ttl: Optional[int] = None) -> None:
        """Set HTML content in Redis."""
        html_key = f"{key}:html"
        redis_key = self._make_key(html_key)
        data = html.encode('utf-8')

        if ttl:
            self.redis.setex(redis_key, ttl, data)
        else:
            self.redis.set(redis_key, data)


class MemoryBackend(CacheBackend):
    """In-memory cache backend for testing/development."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self._cache: Dict[str, tuple[Dict[str, Any], Optional[float]]] = {}

    def _make_key(self, key: str) -> str:
        """Create session-scoped key."""
        return f"{self.session_id}:{key}"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cache entry from memory."""
        cache_key = self._make_key(key)
        entry = self._cache.get(cache_key)

        if entry is None:
            return None

        value, expiry = entry

        # Check if expired
        if expiry and time.time() > expiry:
            del self._cache[cache_key]
            return None

        return value

    def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Set cache entry in memory."""
        cache_key = self._make_key(key)
        expiry = time.time() + ttl if ttl else None
        self._cache[cache_key] = (value, expiry)

    def delete(self, key: str) -> None:
        """Delete cache entry from memory."""
        cache_key = self._make_key(key)
        self._cache.pop(cache_key, None)

    def exists(self, key: str) -> bool:
        """Check if key exists in memory."""
        cache_key = self._make_key(key)
        return cache_key in self._cache

    def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries matching pattern."""
        if pattern is None:
            # Clear all entries for this session
            prefix = f"{self.session_id}:"
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
        else:
            # Match pattern
            search_key = self._make_key(pattern)
            # Simple wildcard matching
            if "*" in pattern:
                prefix = search_key.split("*")[0]
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            else:
                keys_to_delete = [search_key] if search_key in self._cache else []

        for key in keys_to_delete:
            del self._cache[key]
