"""
Simple Module Manager Strategy - Basic operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Simple manager - basic module loading/unloading only.
"""

from types import ModuleType
from typing import Optional
from ...module.base import AModuleManagerStrategy
from ...contracts import ICachingStrategy, IModuleHelperStrategy

class SimpleManager(AModuleManagerStrategy):
    """
    Simple manager - basic module operations only.
    
    No hooks, no error handling, just load/unload.
    """
    
    def __init__(
        self,
        package_name: str,
        caching: ICachingStrategy,
        helper: IModuleHelperStrategy
    ):
        """
        Initialize simple manager.
        
        Args:
            package_name: Package name for isolation
            caching: Caching strategy
            helper: Helper strategy
        """
        self._package_name = package_name
        self._caching = caching
        self._helper = helper
    
    def load_module(self, module_path: str) -> ModuleType:
        """
        Load a module.
        
        Args:
            module_path: Module path to load
            
        Returns:
            Loaded module
        """
        # Check cache first
        cached = self._caching.get(module_path)
        if cached is not None:
            return cached
        
        # Load using helper
        module = self._helper.load(module_path, None)
        
        # Cache it
        self._caching.set(module_path, module)
        
        return module
    
    def unload_module(self, module_path: str) -> None:
        """
        Unload a module.
        
        Args:
            module_path: Module path to unload
        """
        self._helper.unload(module_path)
        self._caching.invalidate(module_path)
    
    def install_hook(self) -> None:
        """Install import hook (not supported in simple mode)."""
        pass
    
    def uninstall_hook(self) -> None:
        """Uninstall import hook (not supported in simple mode)."""
        pass
    
    def handle_import_error(self, module_name: str) -> Optional[ModuleType]:
        """
        Handle import error (not supported in simple mode).
        
        Args:
            module_name: Module name that failed
            
        Returns:
            None (simple mode doesn't handle errors)
        """
        return None

