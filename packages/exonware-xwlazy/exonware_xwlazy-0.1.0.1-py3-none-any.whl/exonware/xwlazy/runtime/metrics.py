"""
Performance metrics tracking for lazy loading system.

This module provides utilities for tracking and aggregating performance metrics.
"""

from typing import Any, Optional
from datetime import datetime
from collections import defaultdict

class MetricsCollector:
    """Collects and aggregates performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self._metrics: dict[str, list[float]] = defaultdict(list)
        self._counts: dict[str, int] = defaultdict(int)
        self._timestamps: dict[str, list[datetime]] = defaultdict(list)
    
    def record_metric(self, name: str, value: float, timestamp: Optional[datetime] = None) -> None:
        """Record a metric value."""
        self._metrics[name].append(value)
        self._counts[name] += 1
        if timestamp is None:
            timestamp = datetime.now()
        self._timestamps[name].append(timestamp)
    
    def get_metric_stats(self, name: str) -> dict[str, Any]:
        """Get statistics for a specific metric."""
        values = self._metrics.get(name, [])
        if not values:
            return {}
        
        return {
            'count': len(values),
            'total': sum(values),
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
        }
    
    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all metrics."""
        return {name: self.get_metric_stats(name) for name in self._metrics.keys()}
    
    def clear(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
        self._counts.clear()
        self._timestamps.clear()

# Global metrics collector instance
_global_metrics = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return _global_metrics

__all__ = ['MetricsCollector', 'get_metrics_collector']

