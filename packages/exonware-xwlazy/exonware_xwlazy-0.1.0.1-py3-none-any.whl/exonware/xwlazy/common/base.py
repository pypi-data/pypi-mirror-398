"""
Common Abstract Base Classes

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Abstract base classes for shared/common strategies.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from ..contracts import ICachingStrategy, ICacheStrategy

# =============================================================================
# ABSTRACT CACHING STRATEGY
# =============================================================================

class ACachingStrategy(ICachingStrategy, ABC):
    """
    Abstract base class for caching strategies (legacy name).
    
    Note: Use ACacheStrategy for new code (ICacheStrategy interface).
    """
    pass

class ACacheStrategy(ICacheStrategy, ABC):
    """
    Abstract base class for caching strategies.
    
    Works with ANY data type (modules, packages, etc.).
    All caching strategies must extend this class.
    """
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        ...
    
    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        ...
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        ...

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    'ACachingStrategy',  # Legacy name
    'ACacheStrategy',    # New name for ICacheStrategy interface
]

