"""
Lazy Module Helper Strategy - Deferred loading.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Lazy loading - loads module on first access with caching.
"""

import importlib
import importlib.util
import threading
from types import ModuleType
from typing import Any, Optional
from ...module.base import AModuleHelperStrategy
from ..data import ModuleData

class LazyHelper(AModuleHelperStrategy):
    """
    Lazy helper - deferred loading with caching.
    
    Loads module on first access and caches it.
    Thread-safe with circular import detection.
    """
    
    def __init__(self):
        """Initialize lazy helper."""
        self._cache: dict[str, ModuleType] = {}
        self._loading: dict[str, bool] = {}
        self._lock = threading.RLock()
    
    def load(self, module_path: str, package_helper: Any) -> ModuleType:
        """
        Load the module lazily (with caching).
        
        Args:
            module_path: Module path to load
            package_helper: Package helper (unused)
            
        Returns:
            Loaded module
        """
        # Check cache first
        if module_path in self._cache:
            return self._cache[module_path]
        
        with self._lock:
            # Double-check after acquiring lock
            if module_path in self._cache:
                return self._cache[module_path]
            
            # Check for circular import
            if self._loading.get(module_path, False):
                raise ImportError(f"Circular import detected for {module_path}")
            
            try:
                self._loading[module_path] = True
                module = importlib.import_module(module_path)
                self._cache[module_path] = module
                return module
            finally:
                self._loading[module_path] = False
    
    def unload(self, module_path: str) -> None:
        """
        Unload the module from cache.
        
        Args:
            module_path: Module path to unload
        """
        with self._lock:
            self._cache.pop(module_path, None)
            self._loading.pop(module_path, None)
    
    def check_importability(self, path: str) -> bool:
        """
        Check if module is importable.
        
        Args:
            path: Module path to check
            
        Returns:
            True if importable, False otherwise
        """
        try:
            spec = importlib.util.find_spec(path)
            return spec is not None
        except (ValueError, AttributeError, ImportError):
            return False

