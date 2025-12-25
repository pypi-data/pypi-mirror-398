"""
#exonware/xwlazy/src/exonware/xwlazy/module/base.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Abstract Base Class for Module Operations

This module defines the abstract base class for module operations.
"""

import sys
import threading
from abc import ABC, abstractmethod
from typing import Optional, Any
from types import ModuleType

from ..contracts import (
    IModuleHelper,
    IModuleHelperStrategy,
    IModuleManagerStrategy,
    ILoadStrategy,
)
from ..package.base import APackageHelper

# =============================================================================
# ABSTRACT MODULE (Unified - Merges AImportHook + ALazyLoader + AModuleHelper)
# =============================================================================

class AModuleHelper(IModuleHelper, ABC):
    """
    Unified abstract base for module operations.
    
    Merges functionality from AImportHook, ALazyLoader, and AModuleHelper.
    Provides comprehensive module operations: installation, hooks, finding, interception, loading, importing, registry, and bytecode caching.
    
    This abstract class combines:
    - Module installation (installing and importing modules)
    - Import hooks (intercepting import failures)
    - Meta path finding (sys.meta_path hook for lazy installation)
    - Import interception (high-level import interception)
    - Lazy loading (deferred module loading)
    - Lazy importing (lazy module loading with strategies)
    - Watched registry (tracking watched module prefixes)
    - Bytecode caching (caching compiled Python bytecode)
    """
    
    __slots__ = (
        # From AImportHook
        '_package_name', '_enabled',
        # From ALazyLoader
        '_module_path', '_cached_module', '_loading',
        # From AModuleHelper
        '_package_helper', '_dependency_mapper',
        # Common
        '_lock'
    )
    
    def __init__(self, package_name: str = 'default', package_helper: Optional[APackageHelper] = None):
        """
        Initialize unified module operations.
        
        Args:
            package_name: Package this instance is for
            package_helper: Optional package helper instance. If None, creates default.
        """
        # From AImportHook
        self._package_name = package_name
        self._enabled = True
        
        # From ALazyLoader
        self._module_path: Optional[str] = None
        self._cached_module: Optional[ModuleType] = None
        self._loading = False
        
        # From AModuleHelper
        self._package_helper = package_helper
        self._dependency_mapper = None  # Lazy init to avoid circular imports
        
        # Common
        self._lock = threading.RLock()
    
    # ========================================================================
    # Import Hook Methods (from AImportHook)
    # ========================================================================
    
    def enable(self) -> None:
        """Enable the import hook."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the import hook."""
        self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if hook is enabled."""
        return self._enabled
    
    @abstractmethod
    def install_hook(self) -> None:
        """Install the import hook into sys.meta_path (abstract method)."""
        pass
    
    @abstractmethod
    def uninstall_hook(self) -> None:
        """Uninstall the import hook from sys.meta_path (abstract method)."""
        pass
    
    @abstractmethod
    def handle_import_error(self, module_name: str) -> Optional[Any]:
        """
        Handle ImportError by attempting to install and re-import (abstract method).
        
        Args:
            module_name: Name of module that failed to import
            
        Returns:
            Imported module if successful, None otherwise
        """
        pass
    
    # ========================================================================
    # Lazy Loader Methods (from ALazyLoader)
    # ========================================================================
    
    @abstractmethod
    def load_module(self, module_path: str) -> ModuleType:
        """
        Load a module lazily (abstract method).
        
        Args:
            module_path: Full module path to load
            
        Returns:
            Loaded module
        """
        pass
    
    def is_loaded(self, module_path: str = None) -> bool:
        """
        Check if module is already loaded.
        
        Args:
            module_path: Module path to check (uses self._module_path if None)
            
        Returns:
            True if loaded, False otherwise
        """
        return self._cached_module is not None
    
    @abstractmethod
    def unload_module(self, module_path: str) -> None:
        """
        Unload a module from cache (abstract method).
        
        Args:
            module_path: Module path to unload
        """
        pass
    
    # ========================================================================
    # Module Helper Methods (from AModuleHelper)
    # ========================================================================
    
    def _get_package_helper(self) -> APackageHelper:
        """Get package helper instance (creates if needed)."""
        if self._package_helper is None:
            self._package_helper = self._create_package_helper()
        return self._package_helper
    
    def _get_dependency_mapper(self):
        """Get dependency mapper instance (lazy init)."""
        if self._dependency_mapper is None:
            from ...common.services.dependency_mapper import DependencyMapper
            self._dependency_mapper = DependencyMapper()
        return self._dependency_mapper
    
    def to_package(self, module_name: str) -> Optional[str]:
        """
        Map module name to package name.
        
        Args:
            module_name: Module name (e.g., 'bson', 'msgpack')
            
        Returns:
            Package name (e.g., 'pymongo', 'msgpack') or None if not found
        """
        mapper = self._get_dependency_mapper()
        return mapper.get_package_name(module_name)
    
    def installed(self, module_name: str) -> bool:
        """
        Check if a module is installed.
        
        Uses cache first to avoid expensive operations.
        Maps module to package and checks if package is installed.
        
        Args:
            module_name: Module name to check (e.g., 'bson')
            
        Returns:
            True if module is installed, False otherwise
        """
        # Map module name to package name
        package_name = self.to_package(module_name)
        if package_name:
            # Check if the package is installed
            return self._get_package_helper().installed(package_name)
        
        # If no mapping found, check if the module itself is importable (abstract method)
        return self._check_module_importability(module_name)
    
    def uninstalled(self, module_name: str) -> bool:
        """
        Check if a module is uninstalled.
        
        Uses cache first to avoid expensive operations.
        Maps module to package and checks if package is uninstalled.
        
        Args:
            module_name: Module name to check (e.g., 'bson')
            
        Returns:
            True if module is uninstalled, False otherwise
        """
        return not self.installed(module_name)
    
    def install(self, *module_names: str) -> None:
        """
        Install one or more modules by mapping to packages first.
        
        First deduplicates modules, then maps to packages, then installs packages.
        Skips modules that are already installed (using cache).
        
        Args:
            *module_names: One or more module names to install (e.g., 'bson', 'msgpack')
            
        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        if not module_names:
            return
        
        # First deduplicate modules (preserves order)
        unique_modules = list(dict.fromkeys(module_names))
        
        # Map all module names to package names
        package_names = []
        for name in unique_modules:
            package_name = self.to_package(name)
            if package_name:
                package_names.append(package_name)
            else:
                # If no mapping found, use the name as-is
                package_names.append(name)
        
        # Install the packages (package_helper handles deduplication and caching)
        self._get_package_helper().install(*package_names)
    
    def uninstall(self, *module_names: str) -> None:
        """
        Uninstall one or more modules by mapping to packages first.
        
        First deduplicates modules, then maps to packages, then uninstalls packages.
        Skips modules that are already uninstalled (using cache).
        
        Args:
            *module_names: One or more module names to uninstall (e.g., 'bson', 'msgpack')
            
        Raises:
            subprocess.CalledProcessError: If uninstallation fails
        """
        if not module_names:
            return
        
        # First deduplicate modules (preserves order)
        unique_modules = list(dict.fromkeys(module_names))
        
        # Map all module names to package names
        package_names = []
        for name in unique_modules:
            package_name = self.to_package(name)
            if package_name:
                package_names.append(package_name)
            else:
                # If no mapping found, use the name as-is
                package_names.append(name)
        
        # Uninstall the packages (package_helper handles deduplication and caching)
        self._get_package_helper().uninstall(*package_names)
    
    def load(self, *module_names: str) -> list[ModuleType]:
        """
        Load one or more modules into memory.
        
        Imports modules and returns them. Uses lazy loading if enabled.
        
        Args:
            *module_names: One or more module names to load (e.g., 'bson', 'msgpack')
            
        Returns:
            List of loaded module objects
            
        Raises:
            ImportError: If module cannot be loaded
        """
        loaded_modules = []
        for name in module_names:
            try:
                module = self._import_module(name)
                loaded_modules.append(module)
            except ImportError as e:
                # Try to install if not found
                if not self.installed(name):
                    self.install(name)
                    # Try importing again
                    module = self._import_module(name)
                    loaded_modules.append(module)
                else:
                    raise
        return loaded_modules
    
    def unload(self, *module_names: str) -> None:
        """
        Unload one or more modules from memory.
        
        Removes modules from sys.modules and clears caches.
        Useful for freeing memory or forcing reload.
        
        Args:
            *module_names: One or more module names to unload (e.g., 'bson', 'msgpack')
        """
        with self._lock:
            for name in module_names:
                # Remove from sys.modules
                if name in sys.modules:
                    del sys.modules[name]
                
                # Remove submodules too (e.g., 'bson.codec' if 'bson' is unloaded)
                to_remove = [mod for mod in sys.modules.keys() if mod.startswith(name + '.')]
                for mod in to_remove:
                    del sys.modules[mod]
            
            # Clear import caches (abstract method)
            self._invalidate_import_caches()
    
    @abstractmethod
    def _check_module_importability(self, module_name: str) -> bool:
        """
        Check if module is importable (abstract method).
        
        Concrete implementations should use importlib.util.find_spec or similar.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if importable, False otherwise
        """
        pass
    
    @abstractmethod
    def _import_module(self, module_name: str) -> ModuleType:
        """
        Import a module (abstract method).
        
        Concrete implementations should use importlib.import_module.
        
        Args:
            module_name: Module name to import
            
        Returns:
            Imported module
            
        Raises:
            ImportError: If module cannot be imported
        """
        pass
    
    @abstractmethod
    def _invalidate_import_caches(self) -> None:
        """
        Invalidate import caches (abstract method).
        
        Concrete implementations should use importlib.invalidate_caches().
        """
        pass
    
    @abstractmethod
    def _create_package_helper(self) -> APackageHelper:
        """
        Create a package helper instance (abstract method).
        
        Returns:
            APackageHelper instance
        """
        pass
    
    # ========================================================================
    # IModuleHelper Interface Methods (stubs - to be implemented by subclasses)
    # ========================================================================
    
    # Note: Many methods from IModuleHelper are already implemented above.
    # The following are stubs that need concrete implementations:
    
    @abstractmethod
    def install_and_import(self, module_name: str, package_name: Optional[str] = None) -> tuple[Optional[ModuleType], bool]:
        """Install package and import module (from IModuleInstaller)."""
        pass
    
    @abstractmethod
    def is_package_installed(self, package_name: str) -> bool:
        """Check if package is installed (from IModuleInstaller)."""
        pass
    
    @abstractmethod
    def mark_installed(self, package_name: str, version: Optional[str] = None) -> None:
        """Mark package as installed in persistent cache (from IModuleInstaller)."""
        pass
    
    @abstractmethod
    def is_hook_installed(self) -> bool:
        """Check if hook is installed (from IImportHook)."""
        pass
    
    @abstractmethod
    def find_spec(self, fullname: str, path: Optional[str] = None, target=None) -> Optional[Any]:
        """Find module spec (from IMetaPathFinder)."""
        pass
    
    @abstractmethod
    def should_intercept(self, fullname: str) -> bool:
        """Determine if a module should be intercepted (from IMetaPathFinder)."""
        pass
    
    @abstractmethod
    def is_module_installed(self, fullname: str) -> bool:
        """Check if module is already installed (from IMetaPathFinder)."""
        pass
    
    @abstractmethod
    def intercept_missing_import(self, module_name: str) -> Optional[ModuleType]:
        """Intercept a missing import (from IImportInterceptor)."""
        pass
    
    @abstractmethod
    def should_intercept_module(self, module_name: str) -> bool:
        """Determine if a module should be intercepted (from IImportInterceptor)."""
        pass
    
    @abstractmethod
    def prevent_recursion(self, module_name: str) -> bool:
        """Check if we should prevent recursion (from IImportInterceptor)."""
        pass
    
    @abstractmethod
    def import_module(self, module_name: str, package_name: Optional[str] = None) -> Any:
        """Import a module with lazy loading (from ILazyImporter)."""
        pass
    
    @abstractmethod
    def enable_lazy_loading(self, load_mode: Any) -> None:
        """Enable lazy loading with a mode (from ILazyImporter)."""
        pass
    
    @abstractmethod
    def disable_lazy_loading(self) -> None:
        """Disable lazy loading (from ILazyImporter)."""
        pass
    
    @abstractmethod
    def is_lazy_loading_enabled(self) -> bool:
        """Check if lazy loading is enabled (from ILazyImporter)."""
        pass
    
    @abstractmethod
    def has_root(self, root_name: str) -> bool:
        """Check if a root module name is being watched (from IWatchedRegistry)."""
        pass
    
    @abstractmethod
    def get_matching_prefixes(self, fullname: str) -> tuple[str, ...]:
        """Get all watched prefixes that match a module name (from IWatchedRegistry)."""
        pass
    
    @abstractmethod
    def is_prefix_owned_by(self, prefix: str, package_name: str) -> bool:
        """Check if a prefix is owned by a package (from IWatchedRegistry)."""
        pass
    
    @abstractmethod
    def is_watched_registry_empty(self) -> bool:
        """Check if registry is empty (from IWatchedRegistry)."""
        pass
    
    @abstractmethod
    def get_bytecode(self, module_path: str, source_code: str) -> Optional[bytes]:
        """Get cached bytecode for module (from IBytecodeCache)."""
        pass
    
    @abstractmethod
    def cache_bytecode(self, module_path: str, source_code: str, bytecode: bytes) -> None:
        """Cache bytecode for module (from IBytecodeCache)."""
        pass
    
    @abstractmethod
    def clear_bytecode_cache(self) -> None:
        """Clear bytecode cache (from IBytecodeCache)."""
        pass

# =============================================================================
# ABSTRACT MODULE HELPER STRATEGY
# =============================================================================

class AModuleHelperStrategy(IModuleHelperStrategy, ABC):
    """
    Abstract base class for module helper strategies.
    
    Operations on a single module (loading, unloading, checking).
    All module helper strategies must extend this class.
    """
    
    @abstractmethod
    def load(self, module_path: str, package_helper: Any) -> ModuleType:
        """Load the module."""
        ...
    
    @abstractmethod
    def unload(self, module_path: str) -> None:
        """Unload the module."""
        ...
    
    @abstractmethod
    def check_importability(self, path: str) -> bool:
        """Check if module is importable."""
        ...

# =============================================================================
# ABSTRACT MODULE MANAGER STRATEGY
# =============================================================================

class AModuleManagerStrategy(IModuleManagerStrategy, ABC):
    """
    Abstract base class for module manager strategies.
    
    Orchestrates multiple modules (loading, hooks, error handling).
    All module manager strategies must extend this class.
    """
    
    @abstractmethod
    def load_module(self, module_path: str) -> ModuleType:
        """Load a module."""
        ...
    
    @abstractmethod
    def unload_module(self, module_path: str) -> None:
        """Unload a module."""
        ...
    
    @abstractmethod
    def install_hook(self) -> None:
        """Install import hook."""
        ...
    
    @abstractmethod
    def uninstall_hook(self) -> None:
        """Uninstall import hook."""
        ...
    
    @abstractmethod
    def handle_import_error(self, module_name: str) -> Optional[ModuleType]:
        """Handle import error."""
        ...

# =============================================================================
# EXPORT ALL
# =============================================================================

# =============================================================================
# ABSTRACT LOADING STRATEGY (Enhanced for Runtime Swapping)
# =============================================================================

class ALoadStrategy(ILoadStrategy, ABC):
    """
    Abstract base class for module loading strategies.
    
    Enables runtime strategy swapping for different loading methods
    (lazy, simple, advanced, etc.).
    """
    
    @abstractmethod
    def load(self, module_name: str) -> ModuleType:
        """
        Load a module.
        
        Args:
            module_name: Module name to load
            
        Returns:
            Loaded module
        """
        ...
    
    def should_lazy_load(self, module_name: str) -> bool:
        """
        Determine if module should be lazy loaded.
        
        Default implementation returns True.
        Override for strategy-specific logic.
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if should lazy load, False otherwise
        """
        return True
    
    @abstractmethod
    def unload(self, module_name: str) -> None:
        """
        Unload a module.
        
        Args:
            module_name: Module name to unload
        """
        ...

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    'AModuleHelper',
    'AModuleHelperStrategy',
    'AModuleManagerStrategy',
    # Enhanced Strategy Interfaces for Runtime Swapping
    'ALoadStrategy',
]

