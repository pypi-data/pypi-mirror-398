"""
Simple Module Helper Strategy - Basic synchronous loading.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Simple synchronous module loading - no lazy loading.
"""

import importlib
from types import ModuleType
from typing import Any
from ...module.base import AModuleHelperStrategy

class SimpleHelper(AModuleHelperStrategy):
    """
    Simple helper - standard synchronous import.
    
    No lazy loading, no caching, just direct importlib.import_module.
    """
    
    def load(self, module_path: str, package_helper: Any) -> ModuleType:
        """
        Load the module synchronously.
        
        Args:
            module_path: Module path to load
            package_helper: Package helper (unused in simple mode)
            
        Returns:
            Loaded module
        """
        return importlib.import_module(module_path)
    
    def unload(self, module_path: str) -> None:
        """
        Unload the module.
        
        Args:
            module_path: Module path to unload
        """
        # Simple mode doesn't track loaded modules
        # Could remove from sys.modules if needed
        pass
    
    def check_importability(self, path: str) -> bool:
        """
        Check if module is importable.
        
        Args:
            path: Module path to check
            
        Returns:
            True if importable, False otherwise
        """
        import importlib.util
        try:
            spec = importlib.util.find_spec(path)
            return spec is not None
        except (ValueError, AttributeError, ImportError):
            return False

