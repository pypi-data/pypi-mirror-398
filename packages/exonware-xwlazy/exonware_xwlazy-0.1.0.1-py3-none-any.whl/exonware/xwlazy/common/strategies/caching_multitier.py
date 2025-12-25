"""
Multi-Tier Cache Strategy - Wrapper for existing MultiTierCache.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Wraps existing MultiTierCache to implement ICaching interface.
Works with ANY data type (modules, packages, etc.).
"""

from typing import Optional, Any
from pathlib import Path
from ...common.cache import MultiTierCache
from ...common.base import ACachingStrategy

class MultiTierCacheStrategy(ACachingStrategy):
    """
    Multi-tier cache strategy (L1 memory + L2 disk + L3 predictive).
    
    Wraps existing MultiTierCache to implement ICachingStrategy interface.
    High-performance caching with multiple tiers.
    """
    
    def __init__(self, l1_size: int = 1000, l2_dir: Optional[Path] = None, enable_l3: bool = True):
        """
        Initialize multi-tier cache.
        
        Args:
            l1_size: Maximum size of L1 (memory) cache
            l2_dir: Directory for L2 (disk) cache
            enable_l3: Enable L3 (predictive) cache
        """
        self._cache = MultiTierCache(l1_size=l1_size, l2_dir=l2_dir, enable_l3=enable_l3)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2 -> L3)."""
        return self._cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache (L1 + L2 batched)."""
        self._cache.set(key, value)
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        # MultiTierCache doesn't have invalidate, so we set to None
        # Or we could extend MultiTierCache to add invalidate
        self._cache.set(key, None)
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
    
    def shutdown(self) -> None:
        """Shutdown cache (flush L2, cleanup threads)."""
        self._cache.shutdown()

