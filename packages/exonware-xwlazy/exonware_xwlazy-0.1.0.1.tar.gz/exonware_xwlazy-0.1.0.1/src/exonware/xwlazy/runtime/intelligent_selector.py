"""
#exonware/xwlazy/src/exonware/xwlazy/loading/intelligent_utils.py

Intelligent mode utilities for automatic mode switching.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 19-Nov-2025

This module provides intelligent mode switching based on load level.
"""

from typing import Optional

from ..defs import LazyLoadMode, LazyInstallMode, LoadLevel

# Lazy import to avoid circular dependency
logger = None

def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    global logger
    if logger is None:
        from ..common.logger import get_logger
        logger = get_logger("xwlazy.loading.intelligent")
    return logger

# Optimal mode mappings based on benchmark results (updated from consistency test)
# Format: {LoadLevel: (LazyLoadMode, LazyInstallMode)}
# Updated: 2025-11-19 - Based on 20-iteration consistency test averages
# Light: ultra+full (0.568ms avg), Medium: hyperparallel+full (5.134ms avg)
# Heavy: preload+size_aware (18.475ms avg), Enterprise: preload+full (44.742ms avg)
INTELLIGENT_MODE_MAP: dict[LoadLevel, tuple[LazyLoadMode, LazyInstallMode]] = {
    LoadLevel.LIGHT: (LazyLoadMode.ULTRA, LazyInstallMode.FULL),  # Winner: 0.568ms avg (±26.1% CV)
    LoadLevel.MEDIUM: (LazyLoadMode.HYPERPARALLEL, LazyInstallMode.FULL),  # Winner: 5.134ms avg (±4.7% CV)
    LoadLevel.HEAVY: (LazyLoadMode.PRELOAD, LazyInstallMode.SIZE_AWARE),  # Winner: 18.475ms avg (±10.2% CV)
    LoadLevel.ENTERPRISE: (LazyLoadMode.PRELOAD, LazyInstallMode.FULL),  # Winner: 44.742ms avg (±1.5% CV)
}

class IntelligentModeSelector:
    """Selects optimal mode based on current load characteristics."""
    
    def __init__(self, mode_map: Optional[dict[LoadLevel, tuple[LazyLoadMode, LazyInstallMode]]] = None):
        """
        Initialize intelligent mode selector.
        
        Args:
            mode_map: Custom mode mapping (defaults to INTELLIGENT_MODE_MAP)
        """
        self._mode_map = mode_map or INTELLIGENT_MODE_MAP.copy()
        self._current_load_level: Optional[LoadLevel] = None
        self._module_count = 0
        self._total_import_time = 0.0
        self._import_count = 0
    
    def update_mode_map(self, mode_map: dict[LoadLevel, tuple[LazyLoadMode, LazyInstallMode]]) -> None:
        """Update the mode mapping with benchmark results."""
        self._mode_map = mode_map.copy()
        _get_logger().info(f"Updated INTELLIGENT mode mapping: {mode_map}")
    
    def detect_load_level(
        self,
        module_count: int = 0,
        total_import_time: float = 0.0,
        import_count: int = 0,
        memory_usage_mb: float = 0.0
    ) -> LoadLevel:
        """
        Detect current load level based on system characteristics.
        
        Args:
            module_count: Number of modules loaded
            total_import_time: Total time spent on imports (seconds)
            import_count: Number of imports performed
            memory_usage_mb: Current memory usage in MB
            
        Returns:
            Detected LoadLevel
        """
        # Update internal state
        self._module_count = module_count
        self._total_import_time = total_import_time
        self._import_count = import_count
        
        # Simple heuristics based on module count and import patterns
        # These thresholds can be tuned based on actual usage patterns
        
        if import_count == 0:
            # Initial state - default to light
            self._current_load_level = LoadLevel.LIGHT
        elif module_count < 5 and import_count < 10:
            # Light load: few modules, few imports
            self._current_load_level = LoadLevel.LIGHT
        elif module_count < 20 and import_count < 50:
            # Medium load: moderate number of modules/imports
            self._current_load_level = LoadLevel.MEDIUM
        elif module_count < 100 and import_count < 200:
            # Heavy load: many modules, many imports
            self._current_load_level = LoadLevel.HEAVY
        else:
            # Enterprise load: very large scale
            self._current_load_level = LoadLevel.ENTERPRISE
        
        # Override based on memory usage if significant
        if memory_usage_mb > 300:
            self._current_load_level = LoadLevel.ENTERPRISE
        elif memory_usage_mb > 150:
            self._current_load_level = LoadLevel.HEAVY
        
        return self._current_load_level
    
    def get_optimal_mode(self, load_level: Optional[LoadLevel] = None) -> tuple[LazyLoadMode, LazyInstallMode]:
        """
        Get optimal mode combination for given load level.
        
        Args:
            load_level: Load level (if None, uses detected level)
            
        Returns:
            Tuple of (LazyLoadMode, LazyInstallMode)
        """
        if load_level is None:
            load_level = self._current_load_level or LoadLevel.LIGHT
        
        optimal = self._mode_map.get(load_level)
        if optimal is None:
            # Fallback to default
            _get_logger().warning(f"No optimal mode found for {load_level}, using default")
            optimal = (LazyLoadMode.AUTO, LazyInstallMode.SMART)
        
        return optimal
    
    def should_switch_mode(
        self,
        current_mode: tuple[LazyLoadMode, LazyInstallMode],
        detected_level: LoadLevel
    ) -> bool:
        """
        Determine if mode should be switched based on detected load level.
        
        Args:
            current_mode: Current (load_mode, install_mode) tuple
            detected_level: Detected load level
            
        Returns:
            True if mode should be switched
        """
        optimal_mode = self.get_optimal_mode(detected_level)
        return current_mode != optimal_mode
    
    def get_stats(self) -> Dict:
        """Get intelligent mode statistics."""
        return {
            'current_load_level': self._current_load_level.value if self._current_load_level else None,
            'module_count': self._module_count,
            'import_count': self._import_count,
            'total_import_time': self._total_import_time,
            'mode_map': {
                level.value: {
                    'load_mode': mode[0].value,
                    'install_mode': mode[1].value
                }
                for level, mode in self._mode_map.items()
            }
        }

__all__ = ['LoadLevel', 'INTELLIGENT_MODE_MAP', 'IntelligentModeSelector']

