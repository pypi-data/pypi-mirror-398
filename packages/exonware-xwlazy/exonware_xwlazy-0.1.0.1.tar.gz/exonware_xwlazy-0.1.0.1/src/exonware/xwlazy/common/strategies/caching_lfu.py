"""
LFU Cache Strategy - Least Frequently Used eviction.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

LFU cache implementation with size limit.
Works with ANY data type (modules, packages, etc.).
"""

from typing import Optional, Any
from collections import Counter
from ...common.base import ACachingStrategy

class LFUCache(ACachingStrategy):
    """
    LFU (Least Frequently Used) cache with size limit.
    
    Evicts least frequently accessed items when cache is full.
    Good for access pattern-based caching.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LFU cache.
        
        Args:
            max_size: Maximum number of items in cache
        """
        self._cache: dict[str, Any] = {}
        self._freq: Counter[str] = Counter()
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (increments frequency)."""
        if key in self._cache:
            self._freq[key] += 1
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache (evicts least frequent if full)."""
        if key not in self._cache and len(self._cache) >= self._max_size:
            # Evict least frequent
            if self._freq:
                least_frequent = min(self._freq.items(), key=lambda x: x[1])[0]
                self._cache.pop(least_frequent, None)
                self._freq.pop(least_frequent, None)
        
        self._cache[key] = value
        if key not in self._freq:
            self._freq[key] = 0
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        self._cache.pop(key, None)
        self._freq.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self._freq.clear()

