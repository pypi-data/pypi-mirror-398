"""
Dict Cache Strategy - Simple dictionary-based caching.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Simple dict-based cache implementation.
Works with ANY data type (modules, packages, etc.).
"""

from typing import Optional, Any
from ...common.base import ACachingStrategy

class DictCache(ACachingStrategy):
    """
    Simple dictionary-based cache.
    
    No eviction policy - grows unbounded.
    Use for small applications or when memory is not a concern.
    """
    
    def __init__(self):
        """Initialize dict cache."""
        self._cache: dict[str, Any] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

