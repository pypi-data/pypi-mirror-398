"""
TTL Cache Strategy - Time-To-Live expiration.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

TTL cache implementation with expiration.
Works with ANY data type (modules, packages, etc.).
"""

import time
from typing import Optional, Any
from ...common.base import ACachingStrategy

class TTLCache(ACachingStrategy):
    """
    TTL (Time-To-Live) cache with expiration.
    
    Automatically expires entries after TTL seconds.
    Good for time-sensitive data.
    """
    
    def __init__(self, ttl_seconds: float = 3600.0):
        """
        Initialize TTL cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default: 1 hour)
        """
        self._cache: dict[str, tuple[Any, float]] = {}  # (value, expiry_time)
        self._ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (returns None if expired)."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                # Expired - remove
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        expiry = time.time() + self._ttl
        self._cache[key] = (value, expiry)
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

