"""
LRU Cache Strategy - Least Recently Used eviction.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

LRU cache implementation with size limit.
Works with ANY data type (modules, packages, etc.).
"""

from typing import Optional, Any
from collections import OrderedDict
from ...common.base import ACachingStrategy

class LRUCache(ACachingStrategy):
    """
    LRU (Least Recently Used) cache with size limit.
    
    Evicts least recently used items when cache is full.
    Good for general-purpose caching.
    """
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items in cache
        """
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (moves to end for LRU)."""
        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache (evicts oldest if full)."""
        if key in self._cache:
            # Update existing - move to end
            self._cache.move_to_end(key)
        else:
            # New entry - check size limit
            if len(self._cache) >= self._max_size:
                # Remove oldest (first item)
                self._cache.popitem(last=False)
        self._cache[key] = value
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

