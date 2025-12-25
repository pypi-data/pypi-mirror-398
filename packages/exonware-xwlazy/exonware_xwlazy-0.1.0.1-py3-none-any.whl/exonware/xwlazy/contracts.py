"""
#exonware/xwlazy/src/exonware/xwlazy/contracts.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Contracts for Lazy Loading System

This module defines all interfaces, enums, and protocols for the lazy loading
system following GUIDE_ARCH.md structure.
"""

from typing import Protocol, Optional, Any, runtime_checkable
from types import ModuleType

# Import enums and dataclasses from defs.py
from .defs import (
    LazyLoadMode,
    LazyInstallMode,
    PathType,
    DependencyInfo,
    LazyModeConfig,
)

# =============================================================================
# PROTOCOLS / INTERFACES (Following GUIDE_DEV.md - Use IClass naming)
# =============================================================================

# NOTE: Old interfaces have been merged into three unified interfaces:
# - IPackageHelper (package operations: discovery, installation, caching, config, manifest, mapping)
# - IModuleHelper (module operations: installation, hooks, finding, interception, loading, importing, registry, bytecode)
# - IRuntime (runtime services: state, learning, selection, metrics, monitoring, caching, registry)

class IPackageHelper(Protocol):
    """
    Unified interface for package operations.
    
    Merges functionality from IPackageDiscovery, IPackageInstaller, IPackageCache,
    IConfigManager, IManifestLoader, and IDependencyMapper.
    Provides simple, clean API for working with packages (what you pip install).
    Packages are what you install via pip: pip install pymongo, pip install msgpack, etc.
    
    This interface combines:
    - Package discovery (mapping import names to package names)
    - Package installation (installing/uninstalling packages)
    - Package caching (caching installation status and metadata)
    - Configuration management (per-package lazy installation configuration)
    - Manifest loading (loading and caching dependency manifests)
    - Dependency mapping (mapping import names to package names)
    """
    
    # ========================================================================
    # Installation Status (from IPackageInstaller + IPackageHelper)
    # ========================================================================
    
    def installed(self, package_name: str) -> bool:
        """
        Check if a package is installed.
        
        Uses cache first to avoid expensive operations.
        Checks persistent cache, then in-memory cache, then importability.
        
        Args:
            package_name: Package name to check (e.g., 'pymongo', 'msgpack')
            
        Returns:
            True if package is installed, False otherwise
        """
        ...
    
    def uninstalled(self, package_name: str) -> bool:
        """
        Check if a package is uninstalled.
        
        Uses cache first to avoid expensive operations.
        Checks persistent cache, then in-memory cache, then importability.
        
        Args:
            package_name: Package name to check (e.g., 'pymongo', 'msgpack')
            
        Returns:
            True if package is uninstalled, False otherwise
        """
        ...
    
    # ========================================================================
    # Package Installation (from IPackageInstaller + IPackageHelper)
    # ========================================================================
    
    def install(self, *package_names: str) -> None:
        """
        Install one or more packages using pip.
        
        Skips packages that are already installed (using cache).
        Only installs unique packages to avoid duplicate operations.
        Updates cache after successful installation.
        
        Args:
            *package_names: One or more package names to install (e.g., 'pymongo', 'msgpack')
            
        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        ...
    
    def install_package(self, package_name: str, module_name: Optional[str] = None) -> bool:
        """
        Install a single package (from IPackageInstaller).
        
        Args:
            package_name: Name of package to install
            module_name: Optional name of module being imported (for interactive mode)
            
        Returns:
            True if installation successful, False otherwise
        """
        ...
    
    def install_and_import(self, module_name: str, package_name: Optional[str] = None) -> tuple[Optional[ModuleType], bool]:
        """
        Install package and import module (from IPackageInstaller).
        
        Args:
            module_name: Name of module to import
            package_name: Optional package name if different from module name
            
        Returns:
            Tuple of (module_object, success_flag)
        """
        ...
    
    def uninstall(self, *package_names: str) -> None:
        """
        Uninstall one or more packages using pip.
        
        Skips packages that are already uninstalled (using cache).
        Only uninstalls unique packages to avoid duplicate operations.
        Updates cache after successful uninstallation.
        
        Args:
            *package_names: One or more package names to uninstall (e.g., 'pymongo', 'msgpack')
            
        Raises:
            subprocess.CalledProcessError: If uninstallation fails
        """
        ...
    
    # ========================================================================
    # Package Discovery (from IPackageDiscovery)
    # ========================================================================
    
    def discover_all_dependencies(self) -> dict[str, str]:
        """
        Discover all dependencies from all available sources.
        
        Discovers from pyproject.toml, requirements.txt, setup.py, etc.
        
        Returns:
            Dict mapping import_name -> package_name
        """
        ...
    
    def get_package_for_import(self, import_name: str) -> Optional[str]:
        """
        Get package name for a given import name.
        
        Args:
            import_name: Import name (e.g., 'cv2', 'PIL')
            
        Returns:
            Package name (e.g., 'opencv-python', 'Pillow') or None
        """
        ...
    
    def get_imports_for_package(self, package_name: str) -> list[str]:
        """
        Get all possible import names for a package.
        
        Args:
            package_name: Package name (e.g., 'opencv-python')
            
        Returns:
            List of import names (e.g., ['opencv-python', 'cv2'])
        """
        ...
    
    # ========================================================================
    # Package Caching (from IPackageCache)
    # ========================================================================
    
    def get_cached(self, key: str) -> Optional[Any]:
        """
        Get cached value.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        ...
    
    def set_cached(self, key: str, value: Any) -> None:
        """
        Set cached value.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        ...
    
    def clear_cache(self) -> None:
        """Clear all cached values."""
        ...
    
    def is_cache_valid(self, key: str) -> bool:
        """
        Check if cache entry is still valid.
        
        Args:
            key: Cache key
            
        Returns:
            True if valid, False otherwise
        """
        ...
    
    # ========================================================================
    # Configuration Management (from IConfigManager)
    # ========================================================================
    
    def is_enabled(self, package_name: str) -> bool:
        """
        Check if lazy install is enabled for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            True if enabled, False otherwise
        """
        ...
    
    def get_mode(self, package_name: str) -> str:
        """
        Get installation mode for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            Mode string
        """
        ...
    
    def get_load_mode(self, package_name: str) -> LazyLoadMode:
        """
        Get load mode for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            LazyLoadMode enum
        """
        ...
    
    def get_install_mode(self, package_name: str) -> LazyInstallMode:
        """
        Get install mode for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            LazyInstallMode enum
        """
        ...
    
    def get_mode_config(self, package_name: str) -> Optional[LazyModeConfig]:
        """
        Get full mode configuration for a package.
        
        Args:
            package_name: Package name
            
        Returns:
            LazyModeConfig or None
        """
        ...
    
    # ========================================================================
    # Manifest Loading (from IManifestLoader)
    # ========================================================================
    
    def get_manifest_signature(self, package_name: str) -> Optional[tuple[str, float, float]]:
        """
        Get manifest file signature (path, mtime, size).
        
        Args:
            package_name: Package name
            
        Returns:
            Tuple of (path, mtime, size) or None
        """
        ...
    
    def get_shared_dependencies(self, package_name: str, signature: Optional[tuple[str, float, float]] = None) -> dict[str, str]:
        """
        Get shared dependencies from manifest.
        
        Args:
            package_name: Package name
            signature: Optional signature for cache validation
            
        Returns:
            Dict mapping import_name -> package_name
        """
        ...
    
    def get_watched_prefixes(self, package_name: str) -> tuple[str, ...]:
        """
        Get watched prefixes from manifest.
        
        Args:
            package_name: Package name
            
        Returns:
            Tuple of watched prefixes
        """
        ...
    
    # ========================================================================
    # Dependency Mapping (from IDependencyMapper)
    # ========================================================================
    
    def get_package_name(self, import_name: str) -> Optional[str]:
        """
        Get package name for an import name (from IDependencyMapper).
        
        Note: This is similar to get_package_for_import() but uses different naming.
        Both methods serve the same purpose - mapping import names to package names.
        
        Args:
            import_name: Import name (e.g., 'cv2', 'msgpack')
            
        Returns:
            Package name (e.g., 'opencv-python', 'msgpack') or None
        """
        ...
    
    def get_import_names(self, package_name: str) -> list[str]:
        """
        Get all import names for a package (from IDependencyMapper).
        
        Note: This is similar to get_imports_for_package() but uses different naming.
        Both methods serve the same purpose - mapping package names to import names.
        
        Args:
            package_name: Package name
            
        Returns:
            List of import names
        """
        ...
    
    def is_stdlib_or_builtin(self, import_name: str) -> bool:
        """
        Check if import name is stdlib or builtin.
        
        Args:
            import_name: Import name to check
            
        Returns:
            True if stdlib/builtin, False otherwise
        """
        ...

class IModuleHelper(Protocol):
    """
    Unified interface for module operations.
    
    Merges functionality from IModuleInstaller, IImportHook, IMetaPathFinder,
    IImportInterceptor, ILazyLoader, ILazyImporter, IWatchedRegistry, and IBytecodeCache.
    Provides simple, clean API for working with modules (what you import).
    Modules are what you use in Python code: import bson, import msgpack, etc.
    
    This interface combines:
    - Module installation (installing and importing modules)
    - Import hooks (intercepting import failures)
    - Meta path finding (sys.meta_path hook for lazy installation)
    - Import interception (high-level import interception)
    - Lazy loading (deferred module loading)
    - Lazy importing (lazy module loading with strategies)
    - Watched registry (tracking watched module prefixes)
    - Bytecode caching (caching compiled Python bytecode)
    """
    
    # ========================================================================
    # Module Operations (from IModuleHelper - existing)
    # ========================================================================
    
    def to_package(self, module_name: str) -> Optional[str]:
        """
        Map module name to package name.
        
        Args:
            module_name: Module name (e.g., 'bson', 'msgpack')
            
        Returns:
            Package name (e.g., 'pymongo', 'msgpack') or None if not found
        """
        ...
    
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
        ...
    
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
        ...
    
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
        ...
    
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
        ...
    
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
        ...
    
    def unload(self, *module_names: str) -> None:
        """
        Unload one or more modules from memory.
        
        Removes modules from sys.modules and clears caches.
        Useful for freeing memory or forcing reload.
        
        Args:
            *module_names: One or more module names to unload (e.g., 'bson', 'msgpack')
        """
        ...
    
    # ========================================================================
    # Module Installation (from IModuleInstaller)
    # ========================================================================
    
    def install_and_import(self, module_name: str, package_name: Optional[str] = None) -> tuple[Optional[ModuleType], bool]:
        """
        Install package and import module (from IModuleInstaller).
        
        CONTRACT:
        1. Check persistent cache FIRST - if installed, import directly
        2. Check importability - if importable, import directly
        3. If not importable, remove finders from sys.meta_path
        4. Install package via pip
        5. Restore finders
        6. Import module
        7. Mark in persistent cache
        8. Return (module, success)
        
        Args:
            module_name: Name of module to import
            package_name: Optional package name (if different from module)
            
        Returns:
            Tuple of (module_object, success_flag)
        """
        ...
    
    def is_package_installed(self, package_name: str) -> bool:
        """
        Check if package is installed (from IModuleInstaller).
        
        CONTRACT:
        - Check persistent cache FIRST
        - Check in-memory cache second
        - Check importability last
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if installed, False otherwise
        """
        ...
    
    def mark_installed(self, package_name: str, version: Optional[str] = None) -> None:
        """
        Mark package as installed in persistent cache (from IModuleInstaller).
        
        Args:
            package_name: Package name
            version: Optional version string
        """
        ...
    
    # ========================================================================
    # Import Hooks (from IImportHook)
    # ========================================================================
    
    def install_hook(self) -> None:
        """Install the import hook into sys.meta_path."""
        ...
    
    def uninstall_hook(self) -> None:
        """Uninstall the import hook from sys.meta_path."""
        ...
    
    def is_hook_installed(self) -> bool:
        """
        Check if hook is installed.
        
        Returns:
            True if hook is in sys.meta_path, False otherwise
        """
        ...
    
    def handle_import_error(self, module_name: str) -> Optional[Any]:
        """
        Handle ImportError by attempting to install and re-import (from IImportHook).
        
        Args:
            module_name: Name of module that failed to import
            
        Returns:
            Imported module if successful, None otherwise
        """
        ...
    
    # ========================================================================
    # Meta Path Finding (from IMetaPathFinder)
    # ========================================================================
    
    def find_spec(self, fullname: str, path: Optional[str] = None, target=None) -> Optional[Any]:
        """
        Find module spec - intercepts imports to enable lazy installation (from IMetaPathFinder).
        
        CONTRACT:
        - If module is already in sys.modules: return None (let Python use it)
        - If module starts with '_': return None (skip C extensions/internal modules)
        - If lazy install is disabled: only intercept watched modules
        - If lazy install is enabled: intercept ALL missing imports
        - If module is in persistent cache as installed: return None (let Python import normally)
        - If module is missing and lazy install enabled: install it, then return None
        
        Args:
            fullname: Full module name (e.g., 'msgpack', 'yaml._yaml')
            path: Optional path (for package imports)
            target: Optional target module
            
        Returns:
            ModuleSpec if intercepted, None to let Python handle normally
        """
        ...
    
    def should_intercept(self, fullname: str) -> bool:
        """
        Determine if a module should be intercepted (from IMetaPathFinder).
        
        CONTRACT:
        - Return False if module is in sys.modules
        - Return False if module starts with '_' (C extension/internal)
        - Return False if lazy install disabled and module not watched
        - Return True if lazy install enabled and module not in cache
        
        Args:
            fullname: Full module name
            
        Returns:
            True if should intercept, False otherwise
        """
        ...
    
    def is_module_installed(self, fullname: str) -> bool:
        """
        Check if module is already installed (in cache or importable) (from IMetaPathFinder).
        
        CONTRACT:
        - Check persistent cache FIRST (fastest)
        - Check in-memory cache second
        - Check importability last (slowest)
        
        Args:
            fullname: Full module name
            
        Returns:
            True if installed, False otherwise
        """
        ...
    
    # ========================================================================
    # Import Interception (from IImportInterceptor)
    # ========================================================================
    
    def intercept_missing_import(self, module_name: str) -> Optional[ModuleType]:
        """
        Intercept a missing import and attempt to install it (from IImportInterceptor).
        
        CONTRACT:
        1. Check if module is already installed (persistent cache)
        2. If installed, return None (let Python import normally)
        3. If not installed and lazy install enabled:
           a. Install package
           b. Import module
           c. Mark in persistent cache
           d. Return module
        4. If lazy install disabled, return None
        
        Args:
            module_name: Name of module that failed to import
            
        Returns:
            Imported module if successful, None otherwise
        """
        ...
    
    def should_intercept_module(self, module_name: str) -> bool:
        """
        Determine if a module should be intercepted (from IImportInterceptor).
        
        CONTRACT:
        - Return False if module starts with '_' (C extension/internal)
        - Return False if module is stdlib/builtin
        - Return False if module is in deny list
        - Return False if lazy install disabled and module not watched
        - Return True if lazy install enabled
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if should intercept, False otherwise
        """
        ...
    
    def prevent_recursion(self, module_name: str) -> bool:
        """
        Check if we should prevent recursion for this module (from IImportInterceptor).
        
        CONTRACT:
        - Return True if installation is in progress
        - Return True if import is in progress for this module
        - Return False otherwise
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if should prevent recursion, False otherwise
        """
        ...
    
    # ========================================================================
    # Lazy Loading (from ILazyLoader)
    # ========================================================================
    
    def load_module(self, module_path: str) -> ModuleType:
        """
        Load a module lazily (from ILazyLoader).
        
        Args:
            module_path: Full module path to load
            
        Returns:
            Loaded module
        """
        ...
    
    def is_loaded(self, module_path: str) -> bool:
        """
        Check if module is already loaded (from ILazyLoader).
        
        Args:
            module_path: Module path to check
            
        Returns:
            True if loaded, False otherwise
        """
        ...
    
    def unload_module(self, module_path: str) -> None:
        """
        Unload a module from cache (from ILazyLoader).
        
        Args:
            module_path: Module path to unload
        """
        ...
    
    # ========================================================================
    # Lazy Importing (from ILazyImporter)
    # ========================================================================
    
    def import_module(self, module_name: str, package_name: Optional[str] = None) -> Any:
        """
        Import a module with lazy loading (from ILazyImporter).
        
        Args:
            module_name: Module name to import
            package_name: Optional package name
            
        Returns:
            Imported module
        """
        ...
    
    def enable_lazy_loading(self, load_mode: LazyLoadMode) -> None:
        """
        Enable lazy loading with a mode (from ILazyImporter).
        
        Args:
            load_mode: LazyLoadMode to use
        """
        ...
    
    def disable_lazy_loading(self) -> None:
        """Disable lazy loading (from ILazyImporter)."""
        ...
    
    def is_lazy_loading_enabled(self) -> bool:
        """
        Check if lazy loading is enabled (from ILazyImporter).
        
        Returns:
            True if enabled, False otherwise
        """
        ...
    
    # ========================================================================
    # Watched Registry (from IWatchedRegistry)
    # ========================================================================
    
    def has_root(self, root_name: str) -> bool:
        """
        Check if a root module name is being watched (from IWatchedRegistry).
        
        Args:
            root_name: Root module name (e.g., 'msgpack', 'yaml')
            
        Returns:
            True if watched, False otherwise
        """
        ...
    
    def get_matching_prefixes(self, fullname: str) -> tuple[str, ...]:
        """
        Get all watched prefixes that match a module name (from IWatchedRegistry).
        
        Args:
            fullname: Full module name
            
        Returns:
            Tuple of matching prefixes
        """
        ...
    
    def is_prefix_owned_by(self, prefix: str, package_name: str) -> bool:
        """
        Check if a prefix is owned by a package (from IWatchedRegistry).
        
        Args:
            prefix: Prefix to check
            package_name: Package name
            
        Returns:
            True if owned, False otherwise
        """
        ...
    
    def is_watched_registry_empty(self) -> bool:
        """
        Check if registry is empty (from IWatchedRegistry).
        
        Returns:
            True if empty, False otherwise
        """
        ...
    
    # ========================================================================
    # Bytecode Caching (from IBytecodeCache)
    # ========================================================================
    
    def get_bytecode(self, module_path: str, source_code: str) -> Optional[bytes]:
        """
        Get cached bytecode for module (from IBytecodeCache).
        
        Args:
            module_path: Module path
            source_code: Source code
            
        Returns:
            Cached bytecode or None
        """
        ...
    
    def cache_bytecode(self, module_path: str, source_code: str, bytecode: bytes) -> None:
        """
        Cache bytecode for module (from IBytecodeCache).
        
        Args:
            module_path: Module path
            source_code: Source code
            bytecode: Compiled bytecode
        """
        ...
    
    def clear_bytecode_cache(self) -> None:
        """Clear bytecode cache (from IBytecodeCache)."""
        ...

class IRuntime(Protocol):
    """
    Unified interface for runtime services.
    
    Merges functionality from IStateManager, IAdaptiveLearner, IIntelligentSelector,
    IMetricsCollector, IPerformanceMonitor, IMultiTierCache, and IRegistry.
    Provides runtime services for state management, learning, monitoring, and caching.
    
    This interface combines:
    - State management (persistent state for lazy installation)
    - Adaptive learning (learning import patterns and optimizing loading)
    - Intelligent selection (selecting optimal modes based on load characteristics)
    - Metrics collection (collecting and aggregating performance metrics)
    - Performance monitoring (monitoring lazy loading performance)
    - Multi-tier caching (L1/L2/L3 caching)
    - Registry (managing instances by key)
    """
    
    # ========================================================================
    # State Management (from IStateManager)
    # ========================================================================
    
    def get_manual_state(self) -> Optional[bool]:
        """
        Get manual state override (from IStateManager).
        
        Returns:
            True/False if manually set, None otherwise
        """
        ...
    
    def set_manual_state(self, value: Optional[bool]) -> None:
        """
        Set manual state override (from IStateManager).
        
        Args:
            value: True/False to set, None to clear
        """
        ...
    
    def get_cached_auto_state(self) -> Optional[bool]:
        """
        Get cached auto-detected state (from IStateManager).
        
        Returns:
            True/False if cached, None otherwise
        """
        ...
    
    def set_auto_state(self, value: Optional[bool]) -> None:
        """
        Set cached auto-detected state (from IStateManager).
        
        Args:
            value: True/False to cache, None to clear
        """
        ...
    
    # ========================================================================
    # Adaptive Learning (from IAdaptiveLearner)
    # ========================================================================
    
    def record_import(self, module_name: str, import_time: float) -> None:
        """
        Record an import event (from IAdaptiveLearner).
        
        Args:
            module_name: Module name that was imported
            import_time: Time taken to import (seconds)
        """
        ...
    
    def predict_next_imports(self, current_module: str, count: int = 3) -> list[str]:
        """
        Predict next likely imports based on patterns (from IAdaptiveLearner).
        
        Args:
            current_module: Current module name
            count: Number of predictions to return
            
        Returns:
            List of predicted module names
        """
        ...
    
    def get_module_score(self, module_name: str) -> float:
        """
        Get priority score for a module (from IAdaptiveLearner).
        
        Args:
            module_name: Module name
            
        Returns:
            Priority score (higher = more important)
        """
        ...
    
    # ========================================================================
    # Intelligent Selection (from IIntelligentSelector)
    # ========================================================================
    
    def detect_load_level(
        self,
        module_count: int = 0,
        total_import_time: float = 0.0,
        import_count: int = 0,
        memory_usage_mb: float = 0.0
    ) -> Any:
        """
        Detect current load level (from IIntelligentSelector).
        
        Args:
            module_count: Number of modules loaded
            total_import_time: Total import time (seconds)
            import_count: Number of imports
            memory_usage_mb: Memory usage in MB
            
        Returns:
            LoadLevel enum
        """
        ...
    
    def get_optimal_mode(self, load_level: Any) -> tuple[LazyLoadMode, LazyInstallMode]:
        """
        Get optimal mode for a load level (from IIntelligentSelector).
        
        Args:
            load_level: LoadLevel enum
            
        Returns:
            Tuple of (LazyLoadMode, LazyInstallMode)
        """
        ...
    
    def update_mode_map(self, mode_map: dict[Any, tuple[LazyLoadMode, LazyInstallMode]]) -> None:
        """
        Update mode mapping with benchmark results (from IIntelligentSelector).
        
        Args:
            mode_map: New mode mapping
        """
        ...
    
    # ========================================================================
    # Metrics Collection (from IMetricsCollector)
    # ========================================================================
    
    def record_metric(self, name: str, value: float, timestamp: Optional[Any] = None) -> None:
        """
        Record a metric value (from IMetricsCollector).
        
        Args:
            name: Metric name
            value: Metric value
            timestamp: Optional timestamp
        """
        ...
    
    def get_metric_stats(self, name: str) -> dict[str, Any]:
        """
        Get statistics for a metric (from IMetricsCollector).
        
        Args:
            name: Metric name
            
        Returns:
            Dict with count, total, average, min, max
        """
        ...
    
    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics for all metrics (from IMetricsCollector).
        
        Returns:
            Dict mapping metric name -> stats
        """
        ...
    
    def clear_metrics(self) -> None:
        """Clear all collected metrics (from IMetricsCollector)."""
        ...
    
    # ========================================================================
    # Performance Monitoring (from IPerformanceMonitor)
    # ========================================================================
    
    def record_load_time(self, module: str, load_time: float) -> None:
        """
        Record module load time (from IPerformanceMonitor).
        
        Args:
            module: Module name
            load_time: Load time in seconds
        """
        ...
    
    def record_access(self, module: str) -> None:
        """
        Record module access (from IPerformanceMonitor).
        
        Args:
            module: Module name
        """
        ...
    
    def get_performance_stats(self) -> dict[str, Any]:
        """
        Get performance statistics (from IPerformanceMonitor).
        
        Returns:
            Dict with load_times, access_counts, memory_usage
        """
        ...
    
    # ========================================================================
    # Multi-Tier Cache (from IMultiTierCache)
    # ========================================================================
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 -> L3) (from IMultiTierCache).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        ...
    
    def set_cached_value(self, key: str, value: Any) -> None:
        """
        Set value in cache (L1 and L2) (from IMultiTierCache).
        
        Args:
            key: Cache key
            value: Value to cache
        """
        ...
    
    def clear_multi_tier_cache(self) -> None:
        """Clear all cache tiers (from IMultiTierCache)."""
        ...
    
    def shutdown_cache(self) -> None:
        """Shutdown cache (flush L2, cleanup threads) (from IMultiTierCache)."""
        ...
    
    # ========================================================================
    # Registry (from IRegistry)
    # ========================================================================
    
    def get_instance(self, key: str) -> Any:
        """
        Get instance by key (from IRegistry).
        
        Args:
            key: Registry key
            
        Returns:
            Registered instance
        """
        ...
    
    def register(self, key: str, instance: Any) -> None:
        """
        Register an instance (from IRegistry).
        
        Args:
            key: Registry key
            instance: Instance to register
        """
        ...
    
    def unregister(self, key: str) -> None:
        """
        Unregister an instance (from IRegistry).
        
        Args:
            key: Registry key
        """
        ...
    
    def has_key(self, key: str) -> bool:
        """
        Check if key is registered (from IRegistry).
        
        Args:
            key: Registry key
            
        Returns:
            True if registered, False otherwise
        """
        ...

# =============================================================================
# STRATEGY INTERFACES (New Strategy Pattern)
# =============================================================================

@runtime_checkable
class ICachingStrategy(Protocol):
    """
    Generic caching strategy interface - works with ANY data type.
    
    Used by both modules and packages for caching strategies.
    """
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        ...
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        ...
    
    def invalidate(self, key: str) -> None:
        """Invalidate cached value."""
        ...
    
    def clear(self) -> None:
        """Clear all cached values."""
        ...

@runtime_checkable
class IModuleHelperStrategy(Protocol):
    """
    Module helper strategy interface.
    
    Operations on a single module (loading, unloading, checking).
    """
    def load(self, module_path: str, package_helper: Any) -> ModuleType:
        """Load the module."""
        ...
    
    def unload(self, module_path: str) -> None:
        """Unload the module."""
        ...
    
    def check_importability(self, path: str) -> bool:
        """Check if module is importable."""
        ...

@runtime_checkable
class IPackageHelperStrategy(Protocol):
    """
    Package helper strategy interface.
    
    Operations on a single package (installing, uninstalling, checking).
    """
    def install(self, package_name: str) -> bool:
        """Install the package."""
        ...
    
    def uninstall(self, package_name: str) -> None:
        """Uninstall the package."""
        ...
    
    def check_installed(self, name: str) -> bool:
        """Check if package is installed."""
        ...
    
    def get_version(self, name: str) -> Optional[str]:
        """Get installed version."""
        ...

@runtime_checkable
class IModuleManagerStrategy(Protocol):
    """
    Module manager strategy interface.
    
    Orchestrates multiple modules (loading, hooks, error handling).
    """
    def load_module(self, module_path: str) -> ModuleType:
        """Load a module."""
        ...
    
    def unload_module(self, module_path: str) -> None:
        """Unload a module."""
        ...
    
    def install_hook(self) -> None:
        """Install import hook."""
        ...
    
    def uninstall_hook(self) -> None:
        """Uninstall import hook."""
        ...
    
    def handle_import_error(self, module_name: str) -> Optional[ModuleType]:
        """Handle import error."""
        ...

@runtime_checkable
class IPackageManagerStrategy(Protocol):
    """
    Package manager strategy interface.
    
    Orchestrates multiple packages (installation, discovery, policy).
    """
    def install_package(self, package_name: str, module_name: Optional[str] = None) -> bool:
        """Install a package."""
        ...
    
    def uninstall_package(self, package_name: str) -> None:
        """Uninstall a package."""
        ...
    
    def discover_dependencies(self) -> dict[str, str]:
        """Discover dependencies."""
        ...
    
    def check_security_policy(self, package_name: str) -> tuple[bool, str]:
        """Check security policy."""
        ...

# =============================================================================
# NEW PACKAGE STRATEGY TYPES (Redesigned Architecture)
# =============================================================================

@runtime_checkable
class IInstallExecutionStrategy(Protocol):
    """
    Installation execution strategy - HOW to execute installation.
    
    Defines the mechanism for actually installing packages (pip, wheel, cached, async).
    """
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """Execute installation of a package."""
        ...
    
    def execute_uninstall(self, package_name: str) -> bool:
        """Execute uninstallation of a package."""
        ...

@runtime_checkable
class IInstallTimingStrategy(Protocol):
    """
    Installation timing strategy - WHEN to install packages.
    
    Defines when packages should be installed (on-demand, upfront, temporary, etc.).
    """
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """Determine if package should be installed now."""
        ...
    
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """Determine if package should be uninstalled after use."""
        ...
    
    def get_install_priority(self, packages: list[str]) -> list[str]:
        """Get priority order for installing packages."""
        ...

@runtime_checkable
class IDiscoveryStrategy(Protocol):
    """
    Discovery strategy - HOW to discover dependencies.
    
    Defines how to find dependencies (from files, manifest, auto-detect).
    """
    def discover(self, project_root: Any) -> dict[str, str]:
        """Discover dependencies from sources."""
        ...
    
    def get_source(self, import_name: str) -> Optional[str]:
        """Get the source of a discovered dependency."""
        ...

@runtime_checkable
class IPolicyStrategy(Protocol):
    """
    Policy strategy - WHAT can be installed (security/policy).
    
    Defines security policies and what packages are allowed/denied.
    """
    def is_allowed(self, package_name: str) -> tuple[bool, str]:
        """Check if package is allowed to be installed."""
        ...
    
    def get_pip_args(self, package_name: str) -> list[str]:
        """Get pip arguments based on policy."""
        ...

@runtime_checkable
class IMappingStrategy(Protocol):
    """
    Mapping strategy - HOW to map import names to package names.
    
    Defines how to map import names (e.g., 'cv2') to package names (e.g., 'opencv-python').
    """
    def map_import_to_package(self, import_name: str) -> Optional[str]:
        """Map import name to package name."""
        ...
    
    def map_package_to_imports(self, package_name: str) -> list[str]:
        """Map package name to possible import names."""
        ...

# =============================================================================
# STRATEGY INTERFACES FOR RUNTIME SWAPPING (Enhanced)
# =============================================================================

@runtime_checkable
class IInstallStrategy(Protocol):
    """
    Installation strategy interface for swappable installation algorithms.
    
    Enables runtime strategy swapping for different installation methods
    (pip, wheel, async, cached, etc.).
    """
    def install(self, package_name: str, version: Optional[str] = None) -> bool:
        """
        Install a package.
        
        Args:
            package_name: Package name to install
            version: Optional version specification
            
        Returns:
            True if installation successful, False otherwise
        """
        ...
    
    def can_install(self, package_name: str) -> bool:
        """
        Check if this strategy can install a package.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if can install, False otherwise
        """
        ...
    
    def uninstall(self, package_name: str) -> bool:
        """
        Uninstall a package.
        
        Args:
            package_name: Package name to uninstall
            
        Returns:
            True if uninstallation successful, False otherwise
        """
        ...

@runtime_checkable
class ILoadStrategy(Protocol):
    """
    Module loading strategy interface for swappable loading algorithms.
    
    Enables runtime strategy swapping for different loading methods
    (lazy, simple, advanced, etc.).
    """
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
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if should lazy load, False otherwise
        """
        ...
    
    def unload(self, module_name: str) -> None:
        """
        Unload a module.
        
        Args:
            module_name: Module name to unload
        """
        ...

@runtime_checkable
class ICacheStrategy(Protocol):
    """
    Caching strategy interface for swappable caching algorithms.
    
    Enables runtime strategy swapping for different caching methods
    (LRU, LFU, TTL, multi-tier, etc.).
    """
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        ...
    
    def put(self, key: str, value: Any) -> None:
        """
        Put value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        ...
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate cached value.
        
        Args:
            key: Cache key to invalidate
        """
        ...
    
    def clear(self) -> None:
        """Clear all cached values."""
        ...

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    # Interfaces/Protocols (Unified)
    'IPackageHelper',  # Merges: IPackageDiscovery, IPackageInstaller, IPackageCache, IConfigManager, IManifestLoader, IDependencyMapper
    'IModuleHelper',  # Merges: IModuleInstaller, IImportHook, IMetaPathFinder, IImportInterceptor, ILazyLoader, ILazyImporter, IWatchedRegistry, IBytecodeCache
    'IRuntime',  # Merges: IStateManager, IAdaptiveLearner, IIntelligentSelector, IMetricsCollector, IPerformanceMonitor, IMultiTierCache, IRegistry
    # Strategy Interfaces (New)
    'ICachingStrategy',
    'IModuleHelperStrategy',
    'IModuleManagerStrategy',
    'IPackageHelperStrategy',
    'IPackageManagerStrategy',
    # New Package Strategy Types
    'IInstallExecutionStrategy',
    'IInstallTimingStrategy',
    'IDiscoveryStrategy',
    'IPolicyStrategy',
    'IMappingStrategy',
    # Enhanced Strategy Interfaces for Runtime Swapping
    'IInstallStrategy',
    'ILoadStrategy',
    'ICacheStrategy',
]

