"""
Performance monitoring for lazy loading system.

This module contains LazyPerformanceMonitor extracted from lazy_core.py Section 4.
"""

from typing import Any

class LazyPerformanceMonitor:
    """Performance monitor for lazy loading operations."""
    
    __slots__ = ('_load_times', '_access_counts', '_memory_usage')
    
    def __init__(self):
        """Initialize performance monitor."""
        self._load_times: dict[str, float] = {}
        self._access_counts: dict[str, int] = {}
        self._memory_usage: dict[str, Any] = {}
    
    def record_load_time(self, module: str, load_time: float) -> None:
        """Record module load time."""
        self._load_times[module] = load_time
    
    def record_access(self, module: str) -> None:
        """Record module access."""
        self._access_counts[module] = self._access_counts.get(module, 0) + 1
    
    def get_stats(self) -> dict[str, Any]:
        """Get performance statistics."""
        return {
            'load_times': self._load_times.copy(),
            'access_counts': self._access_counts.copy(),
            'memory_usage': self._memory_usage.copy()
        }

__all__ = ['LazyPerformanceMonitor']

