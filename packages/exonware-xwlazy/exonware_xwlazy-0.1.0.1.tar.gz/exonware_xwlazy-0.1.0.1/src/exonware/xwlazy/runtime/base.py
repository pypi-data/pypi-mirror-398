"""
#exonware/xwlazy/src/exonware/xwlazy/runtime/base.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Abstract Base Class for Runtime Services

This module defines the abstract base class for runtime services.
"""

import threading
from abc import ABC, abstractmethod
from typing import Optional, Any

from ..contracts import (
    IRuntime,
)

# =============================================================================
# ABSTRACT RUNTIME (Unified - Merges all runtime services)
# =============================================================================

class ARuntimeHelper(IRuntime, ABC):
    """
    Unified abstract base for runtime services.
    
    Merges functionality from all runtime service interfaces.
    Provides runtime services for state management, learning, monitoring, and caching.
    
    This abstract class combines:
    - State management (persistent state for lazy installation)
    - Adaptive learning (learning import patterns and optimizing loading)
    - Intelligent selection (selecting optimal modes based on load characteristics)
    - Metrics collection (collecting and aggregating performance metrics)
    - Performance monitoring (monitoring lazy loading performance)
    - Multi-tier caching (L1/L2/L3 caching)
    - Registry (managing instances by key)
    """
    
    __slots__ = (
        # From IStateManager
        '_manual_state', '_auto_state',
        # From IMetricsCollector
        '_metrics',
        # From IPerformanceMonitor
        '_load_times', '_access_counts',
        # From IMultiTierCache
        '_l1_cache', '_l2_cache', '_l3_cache',
        # From IRegistry
        '_registry',
        # Common
        '_lock'
    )
    
    def __init__(self):
        """Initialize unified runtime services."""
        # From IStateManager
        self._manual_state: Optional[bool] = None
        self._auto_state: Optional[bool] = None
        
        # From IMetricsCollector
        self._metrics: dict[str, list[float]] = {}
        
        # From IPerformanceMonitor
        self._load_times: dict[str, list[float]] = {}
        self._access_counts: dict[str, int] = {}
        
        # From IMultiTierCache
        self._l1_cache: dict[str, Any] = {}
        self._l2_cache: dict[str, Any] = {}
        self._l3_cache: dict[str, Any] = {}
        
        # From IRegistry
        self._registry: dict[str, Any] = {}
        
        # Common
        self._lock = threading.RLock()
    
    # ========================================================================
    # State Management Methods (from IStateManager)
    # ========================================================================
    
    def get_manual_state(self) -> Optional[bool]:
        """Get manual state override (from IStateManager)."""
        return self._manual_state
    
    def set_manual_state(self, value: Optional[bool]) -> None:
        """Set manual state override (from IStateManager)."""
        with self._lock:
            self._manual_state = value
    
    def get_cached_auto_state(self) -> Optional[bool]:
        """Get cached auto-detected state (from IStateManager)."""
        return self._auto_state
    
    def set_auto_state(self, value: Optional[bool]) -> None:
        """Set cached auto-detected state (from IStateManager)."""
        with self._lock:
            self._auto_state = value
    
    # ========================================================================
    # Adaptive Learning Methods (from IAdaptiveLearner)
    # ========================================================================
    
    @abstractmethod
    def record_import(self, module_name: str, import_time: float) -> None:
        """Record an import event (from IAdaptiveLearner)."""
        pass
    
    @abstractmethod
    def predict_next_imports(self, current_module: str, count: int = 3) -> list[str]:
        """Predict next likely imports based on patterns (from IAdaptiveLearner)."""
        pass
    
    @abstractmethod
    def get_module_score(self, module_name: str) -> float:
        """Get priority score for a module (from IAdaptiveLearner)."""
        pass
    
    # ========================================================================
    # Intelligent Selection Methods (from IIntelligentSelector)
    # ========================================================================
    
    @abstractmethod
    def detect_load_level(
        self,
        module_count: int = 0,
        total_import_time: float = 0.0,
        import_count: int = 0,
        memory_usage_mb: float = 0.0
    ) -> Any:
        """Detect current load level (from IIntelligentSelector)."""
        pass
    
    @abstractmethod
    def get_optimal_mode(self, load_level: Any) -> tuple[Any, Any]:
        """Get optimal mode for a load level (from IIntelligentSelector)."""
        pass
    
    @abstractmethod
    def update_mode_map(self, mode_map: dict[Any, tuple[Any, Any]]) -> None:
        """Update mode mapping with benchmark results (from IIntelligentSelector)."""
        pass
    
    # ========================================================================
    # Metrics Collection Methods (from IMetricsCollector)
    # ========================================================================
    
    def record_metric(self, name: str, value: float, timestamp: Optional[Any] = None) -> None:
        """Record a metric value (from IMetricsCollector)."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(value)
    
    @abstractmethod
    def get_metric_stats(self, name: str) -> dict[str, Any]:
        """Get statistics for a metric (from IMetricsCollector)."""
        pass
    
    @abstractmethod
    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all metrics (from IMetricsCollector)."""
        pass
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics (from IMetricsCollector)."""
        with self._lock:
            self._metrics.clear()
    
    # ========================================================================
    # Performance Monitoring Methods (from IPerformanceMonitor)
    # ========================================================================
    
    def record_load_time(self, module: str, load_time: float) -> None:
        """Record module load time (from IPerformanceMonitor)."""
        with self._lock:
            if module not in self._load_times:
                self._load_times[module] = []
            self._load_times[module].append(load_time)
    
    def record_access(self, module: str) -> None:
        """Record module access (from IPerformanceMonitor)."""
        with self._lock:
            self._access_counts[module] = self._access_counts.get(module, 0) + 1
    
    @abstractmethod
    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics (from IPerformanceMonitor)."""
        pass
    
    # ========================================================================
    # Multi-Tier Cache Methods (from IMultiTierCache)
    # ========================================================================
    
    def get_multi_tier_cached(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2 -> L3) (from IMultiTierCache)."""
        with self._lock:
            # Check L1 first
            if key in self._l1_cache:
                return self._l1_cache[key]
            # Check L2
            if key in self._l2_cache:
                value = self._l2_cache[key]
                # Promote to L1
                self._l1_cache[key] = value
                return value
            # Check L3
            if key in self._l3_cache:
                value = self._l3_cache[key]
                # Promote to L2
                self._l2_cache[key] = value
                return value
            return None
    
    def set_multi_tier_cached(self, key: str, value: Any) -> None:
        """Set value in cache (L1 and L2) (from IMultiTierCache)."""
        with self._lock:
            self._l1_cache[key] = value
            self._l2_cache[key] = value
    
    def clear_multi_tier_cache(self) -> None:
        """Clear all cache tiers (from IMultiTierCache)."""
        with self._lock:
            self._l1_cache.clear()
            self._l2_cache.clear()
            self._l3_cache.clear()
    
    @abstractmethod
    def shutdown_multi_tier_cache(self) -> None:
        """Shutdown cache (flush L2, cleanup threads) (from IMultiTierCache)."""
        pass
    
    # Alias method for backward compatibility
    def shutdown_cache(self) -> None:
        """Alias for shutdown_multi_tier_cache (backward compatibility)."""
        self.shutdown_multi_tier_cache()
    
    # ========================================================================
    # Registry Methods (from IRegistry)
    # ========================================================================
    
    def get_instance(self, key: str) -> Any:
        """Get instance by key (from IRegistry)."""
        with self._lock:
            return self._registry.get(key)
    
    def register(self, key: str, instance: Any) -> None:
        """Register an instance (from IRegistry)."""
        with self._lock:
            self._registry[key] = instance
    
    def unregister(self, key: str) -> None:
        """Unregister an instance (from IRegistry)."""
        with self._lock:
            self._registry.pop(key, None)
    
    def has_key(self, key: str) -> bool:
        """Check if key is registered (from IRegistry)."""
        with self._lock:
            return key in self._registry

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    'ARuntimeHelper',
]

