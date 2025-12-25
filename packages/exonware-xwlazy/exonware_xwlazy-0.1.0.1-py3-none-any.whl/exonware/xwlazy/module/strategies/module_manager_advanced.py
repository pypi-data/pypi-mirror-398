"""
Advanced Module Manager Strategy - Full features.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Advanced manager - with hooks, error handling, and full features.
"""

import sys
from types import ModuleType
from typing import Optional
from ...module.base import AModuleManagerStrategy
from ...contracts import ICachingStrategy, IModuleHelperStrategy
from ...package.base import APackageHelper
from ...module import importer_engine

class AdvancedManager(AModuleManagerStrategy):
    """
    Advanced manager - full features with hooks and error handling.
    
    Supports import hooks, error recovery, and all advanced features.
    """
    
    def __init__(
        self,
        package_name: str,
        package_helper: APackageHelper,
        caching: ICachingStrategy,
        helper: IModuleHelperStrategy
    ):
        """
        Initialize advanced manager.
        
        Args:
            package_name: Package name for isolation
            package_helper: Package helper instance
            caching: Caching strategy
            helper: Helper strategy
        """
        self._package_name = package_name
        self._package_helper = package_helper
        self._caching = caching
        self._helper = helper
        self._import_hook: Optional[importer_engine.LazyImportHook] = None
    
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
        module = self._helper.load(module_path, self._package_helper)
        
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
        
        # Also remove from sys.modules if present
        if module_path in sys.modules:
            del sys.modules[module_path]
    
    def install_hook(self) -> None:
        """Install import hook into sys.meta_path."""
        importer_engine.install_import_hook(self._package_name)
    
    def uninstall_hook(self) -> None:
        """Uninstall import hook from sys.meta_path."""
        importer_engine.uninstall_import_hook(self._package_name)
    
    def handle_import_error(self, module_name: str) -> Optional[ModuleType]:
        """
        Handle ImportError by attempting to install and re-import.
        
        Args:
            module_name: Name of module that failed to import
            
        Returns:
            Imported module if successful, None otherwise
        """
        if self._import_hook is None:
            self._import_hook = importer_engine.LazyImportHook(
                self._package_name,
                self._package_helper
            )
        return self._import_hook.handle_import_error(module_name)

