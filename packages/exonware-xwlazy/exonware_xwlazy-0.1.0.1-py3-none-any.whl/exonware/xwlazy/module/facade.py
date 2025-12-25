"""
Module Operations Facade

Main facade: XWModuleHelper extends AModuleHelper
Provides concrete implementation for all module operations.
Uses strategy pattern for caching, helper, and manager strategies.
"""

import sys
import importlib
import importlib.util
from typing import Optional
from types import ModuleType

from .base import AModuleHelper, APackageHelper
# Lazy import to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..package.facade import XWPackageHelper

# Import from importer_engine for hook and module operations
from . import importer_engine

# Import strategy interfaces
from ..contracts import ICachingStrategy, IModuleHelperStrategy, IModuleManagerStrategy

# Import default strategies
from ..common.strategies import LRUCache
from .strategies import LazyHelper, AdvancedManager
from ..package.services.strategy_registry import StrategyRegistry

class XWModuleHelper(AModuleHelper):
    """
    Concrete implementation of AModuleHelper.
    
    Provides simple, clean API for working with modules (what you import).
    Uses XWPackageHelper for package operations and DependencyMapper for module-to-package mapping.
    """
    
    def __init__(
        self,
        package_name: str = 'default',
        package_helper: Optional[APackageHelper] = None,
        *,
        # Strategy injection
        caching_strategy: Optional[ICachingStrategy] = None,
        helper_strategy: Optional[IModuleHelperStrategy] = None,
        manager_strategy: Optional[IModuleManagerStrategy] = None
    ):
        """
        Initialize XW module helper.
        
        Args:
            package_name: Package name for isolation (defaults to 'default')
            package_helper: Optional package helper instance. If None, creates XWPackageHelper.
            caching_strategy: Optional caching strategy. If None, uses LRUCache.
            helper_strategy: Optional helper strategy. If None, uses LazyHelper.
            manager_strategy: Optional manager strategy. If None, uses AdvancedManager.
        """
        if package_helper is None:
            # Lazy import to avoid circular dependency
            from ..package.facade import XWPackageHelper
            package_helper = XWPackageHelper(package_name)
        super().__init__(package_name, package_helper)
        self._package_name = package_name
        self._package_helper = package_helper
        
        # Check registry for stored strategies, otherwise use defaults
        if caching_strategy is None:
            caching_strategy = StrategyRegistry.get_module_strategy(package_name, 'caching')
            if caching_strategy is None:
                caching_strategy = LRUCache(max_size=1000)
        if helper_strategy is None:
            helper_strategy = StrategyRegistry.get_module_strategy(package_name, 'helper')
            if helper_strategy is None:
                helper_strategy = LazyHelper()
        if manager_strategy is None:
            manager_strategy = StrategyRegistry.get_module_strategy(package_name, 'manager')
            if manager_strategy is None:
                manager_strategy = AdvancedManager(
                    package_name,
                    package_helper,
                    caching_strategy,
                    helper_strategy
                )
        
        # Store strategies
        self._caching = caching_strategy
        self._helper = helper_strategy
        self._manager = manager_strategy
    
    def _check_module_importability(self, module_name: str) -> bool:
        """
        Check if module is importable.
        
        Uses importlib.util.find_spec to check if module can be imported.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if importable, False otherwise
        """
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ValueError, AttributeError, ImportError):
            return False
    
    def _import_module(self, module_name: str) -> ModuleType:
        """
        Import a module.
        
        Uses importlib.import_module to import the module.
        
        Args:
            module_name: Module name to import
            
        Returns:
            Imported module
            
        Raises:
            ImportError: If module cannot be imported
        """
        return importlib.import_module(module_name)
    
    def _invalidate_import_caches(self) -> None:
        """
        Invalidate import caches.
        
        Uses importlib.invalidate_caches() to clear Python's import caches.
        """
        importlib.invalidate_caches()
        sys.path_importer_cache.clear()
    
    def _create_package_helper(self) -> APackageHelper:
        """
        Create a package helper instance.
        
        Returns:
            XWPackageHelper instance
        """
        from ..package.facade import XWPackageHelper
        return XWPackageHelper(self._package_name)
    
    # Strategy swapping methods
    def swap_cache_strategy(self, new_strategy: ICachingStrategy) -> None:
        """
        Swap cache strategy at runtime.
        
        Args:
            new_strategy: New caching strategy to use
        """
        self._caching = new_strategy
        # Update manager if it uses caching
        if hasattr(self._manager, '_caching'):
            self._manager._caching = new_strategy
    
    def swap_helper_strategy(self, new_strategy: IModuleHelperStrategy) -> None:
        """
        Swap helper/engine strategy at runtime.
        
        Args:
            new_strategy: New helper strategy to use
        """
        self._helper = new_strategy
        # Update manager if it uses helper
        if hasattr(self._manager, '_helper'):
            self._manager._helper = new_strategy
    
    def swap_manager_strategy(self, new_strategy: IModuleManagerStrategy) -> None:
        """
        Swap manager strategy at runtime.
        
        Args:
            new_strategy: New manager strategy to use
        """
        self._manager = new_strategy
    
    # Abstract methods from AModule that need implementation
    def install_hook(self) -> None:
        """
        Install the import hook into sys.meta_path.
        
        Delegates to manager strategy.
        """
        self._manager.install_hook()
    
    def uninstall_hook(self) -> None:
        """
        Uninstall the import hook from sys.meta_path.
        
        Delegates to manager strategy.
        """
        self._manager.uninstall_hook()
    
    def is_hook_installed(self) -> bool:
        """
        Check if import hook is installed.
        
        Uses importer_engine.is_import_hook_installed() to check hook status.
        
        Returns:
            True if hook is installed, False otherwise
        """
        return importer_engine.is_import_hook_installed(self._package_name)
    
    def handle_import_error(self, module_name: str) -> Optional[ModuleType]:
        """
        Handle ImportError by attempting to install and re-import.
        
        Delegates to manager strategy.
        
        Args:
            module_name: Name of module that failed to import
            
        Returns:
            Imported module if successful, None otherwise
        """
        return self._manager.handle_import_error(module_name)
    
    def load_module(self, module_path: str) -> ModuleType:
        """
        Load a module lazily.
        
        Delegates to manager strategy.
        
        Args:
            module_path: Full module path to load
            
        Returns:
            Loaded module
        """
        return self._manager.load_module(module_path)
    
    def unload_module(self, module_path: str) -> None:
        """
        Unload a module from cache.
        
        Delegates to manager strategy.
        
        Args:
            module_path: Module path to unload
        """
        self._manager.unload_module(module_path)

