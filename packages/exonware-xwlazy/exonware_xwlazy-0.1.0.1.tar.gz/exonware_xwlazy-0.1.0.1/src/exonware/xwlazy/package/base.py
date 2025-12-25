"""
#exonware/xwlazy/src/exonware/xwlazy/package/base.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Abstract Base Class for Package Operations

This module defines the abstract base class for package operations.
"""

import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
from types import ModuleType

from ..defs import (
    DependencyInfo,
    LazyInstallMode,
)
from ..contracts import (
    IPackageHelper,
    IPackageHelperStrategy,
    IPackageManagerStrategy,
    IInstallExecutionStrategy,
    IInstallTimingStrategy,
    IDiscoveryStrategy,
    IPolicyStrategy,
    IMappingStrategy,
    IInstallStrategy,
)

# =============================================================================
# ABSTRACT PACKAGE (Unified - Merges APackageDiscovery + APackageInstaller + APackageCache + APackageHelper)
# =============================================================================

class APackageHelper(IPackageHelper, ABC):
    """
    Unified abstract base for package operations.
    
    Merges functionality from APackageDiscovery, APackageInstaller, APackageCache, and APackageHelper.
    Provides comprehensive package operations: discovery, installation, caching, configuration, manifest loading, and dependency mapping.
    
    This abstract class combines:
    - Package discovery (mapping import names to package names)
    - Package installation (installing/uninstalling packages)
    - Package caching (caching installation status and metadata)
    - Configuration management (per-package lazy installation configuration)
    - Manifest loading (loading and caching dependency manifests)
    - Dependency mapping (mapping import names to package names)
    """
    
    __slots__ = (
        # From APackageDiscovery
        'project_root', 'discovered_dependencies', '_discovery_sources', 
        '_cached_dependencies', '_file_mtimes', '_cache_valid',
        # From APackageInstaller
        '_package_name', '_enabled', '_mode', '_installed_packages', 
        '_failed_packages',
        # From APackageCache
        '_cache',
        # From APackageHelper
        '_uninstalled_packages',
        # Common
        '_lock'
    )
    
    def __init__(self, package_name: str = 'default', project_root: Optional[str] = None):
        """
        Initialize unified package operations.
        
        Args:
            package_name: Name of package this instance is for (for isolation)
            project_root: Root directory of project (auto-detected if None)
        """
        # From APackageDiscovery
        self.project_root = Path(project_root) if project_root else self._find_project_root()
        self.discovered_dependencies: dict[str, DependencyInfo] = {}
        self._discovery_sources: list[str] = []
        self._cached_dependencies: dict[str, str] = {}
        self._file_mtimes: dict[str, float] = {}
        self._cache_valid = False
        
        # From APackageInstaller
        self._package_name = package_name
        self._enabled = False
        self._mode = LazyInstallMode.SMART
        self._installed_packages: set[str] = set()
        self._failed_packages: set[str] = set()
        
        # From APackageCache
        self._cache: dict[str, Any] = {}
        
        # From APackageHelper
        self._uninstalled_packages: set[str] = set()
        
        # Common
        self._lock = threading.RLock()
    
    # ========================================================================
    # Package Discovery Methods (from APackageDiscovery)
    # ========================================================================
    
    def _find_project_root(self) -> Path:
        """
        Find the project root directory by looking for markers.
        
        Uses the shared utility function from common.utils.
        """
        from ..common.utils import find_project_root
        return find_project_root()
    
    def discover_all_dependencies(self) -> dict[str, str]:
        """
        Template method: Discover all dependencies from all sources.
        
        Workflow:
        1. Check if cache is valid
        2. If not, discover from sources
        3. Add common mappings
        4. Update cache
        5. Return dependencies
        
        Returns:
            Dict mapping import_name -> package_name
        """
        # Return cached result if still valid
        if self._is_cache_valid():
            return self._cached_dependencies.copy()
        
        # Cache invalid - rediscover
        self.discovered_dependencies.clear()
        self._discovery_sources.clear()
        
        # Discover from all sources (abstract method)
        self._discover_from_sources()
        
        # Add common mappings
        self._add_common_mappings()
        
        # Convert to simple dict format and cache
        result = {}
        for import_name, dep_info in self.discovered_dependencies.items():
            result[import_name] = dep_info.package_name
        
        # Update cache
        self._cached_dependencies = result.copy()
        self._cache_valid = True
        self._update_file_mtimes()
        
        return result
    
    @abstractmethod
    def _discover_from_sources(self) -> None:
        """
        Discover dependencies from all sources (abstract step).
        
        Implementations should discover from:
        - pyproject.toml
        - requirements.txt
        - setup.py
        - custom config files
        """
        pass
    
    @abstractmethod
    def _is_cache_valid(self) -> bool:
        """
        Check if cached dependencies are still valid (abstract step).
        
        Returns:
            True if cache is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def _add_common_mappings(self) -> None:
        """Add common import -> package mappings (abstract step)."""
        pass
    
    @abstractmethod
    def _update_file_mtimes(self) -> None:
        """Update file modification times for cache validation (abstract step)."""
        pass
    
    def get_discovery_sources(self) -> list[str]:
        """Get list of sources used for discovery."""
        return self._discovery_sources.copy()
    
    # ========================================================================
    # Package Installation Methods (from APackageInstaller)
    # ========================================================================
    
    def get_package_name(self, import_name: Optional[str] = None) -> Optional[str]:
        """
        Get package name.
        If import_name is None, returns the package name this instance is for.
        If import_name is provided, maps it to a package name (via IDependencyMapper).
        """
        if import_name is None:
            return self._package_name
        
        # For IDependencyMapper implementation - must be implemented by subclasses
        # Note: This method signature conflicts with the property getter, so subclasses
        # should implement this variant if they implement IDependencyMapper
        raise NotImplementedError("Subclasses must implement get_package_name(import_name)")
    
    def set_mode(self, mode: LazyInstallMode) -> None:
        """Set the installation mode."""
        with self._lock:
            self._mode = mode
    
    def get_mode(self) -> LazyInstallMode:
        """Get the current installation mode."""
        return self._mode
    
    def enable(self) -> None:
        """Enable lazy installation."""
        with self._lock:
            self._enabled = True
    
    def disable(self) -> None:
        """Disable lazy installation."""
        with self._lock:
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if lazy installation is enabled."""
        return self._enabled
    
    @abstractmethod
    def install_package(self, package_name: str, module_name: Optional[str] = None) -> bool:
        """
        Install a package (abstract method).
        
        Args:
            package_name: Name of package to install
            module_name: Name of module being imported (for interactive mode)
            
        Returns:
            True if installation successful, False otherwise
        """
        pass
    
    @abstractmethod
    def _check_security_policy(self, package_name: str) -> tuple[bool, str]:
        """
        Check security policy for package (abstract method).
        
        Args:
            package_name: Package to check
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        pass
    
    @abstractmethod
    def _run_pip_install(self, package_name: str, args: list[str]) -> bool:
        """
        Run pip install with arguments (abstract method).
        
        Args:
            package_name: Package to install
            args: Additional pip arguments
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    def get_stats(self) -> dict[str, Any]:
        """Get installation statistics."""
        with self._lock:
            return {
                'enabled': self._enabled,
                'mode': self._mode.value,
                'package_name': self._package_name,
                'installed_packages': list(self._installed_packages),
                'failed_packages': list(self._failed_packages),
                'total_installed': len(self._installed_packages),
                'total_failed': len(self._failed_packages)
            }
    
    # ========================================================================
    # Package Caching Methods (from APackageCache)
    # ========================================================================
    
    def get_cached(self, key: str) -> Optional[Any]:
        """
        Get cached value (abstract method).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        with self._lock:
            return self._cache.get(key)
    
    def set_cached(self, key: str, value: Any) -> None:
        """
        Set cached value (abstract method).
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
    
    @abstractmethod
    def is_cache_valid(self, key: str) -> bool:
        """
        Check if cache entry is still valid (abstract method).
        
        Args:
            key: Cache key
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    # ========================================================================
    # Package Helper Methods (from APackageHelper)
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
        # Check in-memory cache first (fast)
        with self._lock:
            if package_name in self._installed_packages:
                return True
            if package_name in self._uninstalled_packages:
                return False
        
        # Check persistent cache (abstract method)
        if self._check_persistent_cache(package_name):
            with self._lock:
                self._installed_packages.add(package_name)
                self._uninstalled_packages.discard(package_name)
            return True
        
        # Check actual installation (expensive) - abstract method
        is_installed = self._check_importability(package_name)
        
        # Update caches
        with self._lock:
            if is_installed:
                self._installed_packages.add(package_name)
                self._uninstalled_packages.discard(package_name)
                self._mark_installed_in_persistent_cache(package_name)
            else:
                self._uninstalled_packages.add(package_name)
                self._installed_packages.discard(package_name)
        
        return is_installed
    
    def uninstalled(self, package_name: str) -> bool:
        """
        Check if a package is uninstalled.
        
        Uses cache first to avoid expensive operations.
        
        Args:
            package_name: Package name to check (e.g., 'pymongo', 'msgpack')
            
        Returns:
            True if package is uninstalled, False otherwise
        """
        return not self.installed(package_name)
    
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
        if not package_names:
            return
        
        # Get unique packages only (preserves order while removing duplicates)
        unique_names = list(dict.fromkeys(package_names))
        
        # Filter out packages that are already installed (check cache first)
        to_install = []
        with self._lock:
            for name in unique_names:
                if name not in self._installed_packages:
                    # Double-check if not in cache
                    if not self.installed(name):
                        to_install.append(name)
        
        if not to_install:
            # All packages already installed
            return
        
        # Install packages (abstract method)
        self._run_install(*to_install)
        
        # Update cache after successful installation
        with self._lock:
            for name in to_install:
                self._installed_packages.add(name)
                self._uninstalled_packages.discard(name)
                self._mark_installed_in_persistent_cache(name)
    
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
        if not package_names:
            return
        
        # Get unique packages only (preserves order while removing duplicates)
        unique_names = list(dict.fromkeys(package_names))
        
        # Filter out packages that are already uninstalled (check cache first)
        to_uninstall = []
        with self._lock:
            for name in unique_names:
                if name not in self._uninstalled_packages:
                    # Double-check if not uninstalled
                    if self.installed(name):
                        to_uninstall.append(name)
        
        if not to_uninstall:
            # All packages already uninstalled
            return
        
        # Uninstall packages (abstract method)
        self._run_uninstall(*to_uninstall)
        
        # Update cache after successful uninstallation
        with self._lock:
            for name in to_uninstall:
                self._uninstalled_packages.add(name)
                self._installed_packages.discard(name)
                self._mark_uninstalled_in_persistent_cache(name)
    
    @abstractmethod
    def _check_importability(self, package_name: str) -> bool:
        """
        Check if package is importable (abstract method).
        
        Concrete implementations should use importlib.util.find_spec or similar.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if importable, False otherwise
        """
        pass
    
    @abstractmethod
    def _check_persistent_cache(self, package_name: str) -> bool:
        """
        Check persistent cache for package installation status (abstract method).
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if found in persistent cache as installed, False otherwise
        """
        pass
    
    @abstractmethod
    def _mark_installed_in_persistent_cache(self, package_name: str) -> None:
        """
        Mark package as installed in persistent cache (abstract method).
        
        Args:
            package_name: Package name to mark
        """
        pass
    
    @abstractmethod
    def _mark_uninstalled_in_persistent_cache(self, package_name: str) -> None:
        """
        Mark package as uninstalled in persistent cache (abstract method).
        
        Args:
            package_name: Package name to mark
        """
        pass
    
    @abstractmethod
    def _run_install(self, *package_names: str) -> None:
        """
        Run pip install for packages (abstract method).
        
        Args:
            *package_names: Package names to install
            
        Raises:
            subprocess.CalledProcessError: If installation fails
        """
        pass
    
    @abstractmethod
    def _run_uninstall(self, *package_names: str) -> None:
        """
        Run pip uninstall for packages (abstract method).
        
        Args:
            *package_names: Package names to uninstall
            
        Raises:
            subprocess.CalledProcessError: If uninstallation fails
        """
        pass
    
    # ========================================================================
    # IPackageHelper Interface Methods (stubs - to be implemented by subclasses)
    # ========================================================================
    
    # Note: Many methods from IPackageHelper are already implemented above.
    # The following are stubs that need concrete implementations:
    
    @abstractmethod
    def install_and_import(self, module_name: str, package_name: Optional[str] = None) -> tuple[Optional[ModuleType], bool]:
        """Install package and import module (from IPackageInstaller)."""
        pass
    
    @abstractmethod
    def get_package_for_import(self, import_name: str) -> Optional[str]:
        """Get package name for a given import name (from IPackageDiscovery)."""
        pass
    
    @abstractmethod
    def get_imports_for_package(self, package_name: str) -> list[str]:
        """Get all possible import names for a package (from IPackageDiscovery)."""
        pass
    
    # def get_package_name(self, import_name: str) -> Optional[str]:
    #    """Get package name for an import name (from IDependencyMapper)."""
    #    raise NotImplementedError("Subclasses must implement get_package_name")
    
    @abstractmethod
    def get_import_names(self, package_name: str) -> list[str]:
        """Get all import names for a package (from IDependencyMapper)."""
        pass
    
    @abstractmethod
    def is_stdlib_or_builtin(self, import_name: str) -> bool:
        """Check if import name is stdlib or builtin (from IDependencyMapper)."""
        pass
    
    # Note: is_enabled(package_name) from IConfigManager is removed to avoid conflict
    # with is_enabled() instance method. Use LazyInstallConfig.is_enabled(package_name) instead.
    
    @abstractmethod
    def get_mode(self, package_name: str) -> str:
        """Get installation mode for a package (from IConfigManager)."""
        pass
    
    @abstractmethod
    def get_load_mode(self, package_name: str) -> Any:
        """Get load mode for a package (from IConfigManager)."""
        pass
    
    @abstractmethod
    def get_install_mode(self, package_name: str) -> Any:
        """Get install mode for a package (from IConfigManager)."""
        pass
    
    @abstractmethod
    def get_mode_config(self, package_name: str) -> Optional[Any]:
        """Get full mode configuration for a package (from IConfigManager)."""
        pass
    
    @abstractmethod
    def get_manifest_signature(self, package_name: str) -> Optional[tuple[str, float, float]]:
        """Get manifest file signature (from IManifestLoader)."""
        pass
    
    @abstractmethod
    def get_shared_dependencies(self, package_name: str, signature: Optional[tuple[str, float, float]] = None) -> dict[str, str]:
        """Get shared dependencies from manifest (from IManifestLoader)."""
        pass
    
    @abstractmethod
    def get_watched_prefixes(self, package_name: str) -> tuple[str, ...]:
        """Get watched prefixes from manifest (from IManifestLoader)."""
        pass

# =============================================================================
# DEPRECATED CLASSES (for backward compatibility)
# =============================================================================

# =============================================================================
# ABSTRACT PACKAGE HELPER STRATEGY
# =============================================================================

class APackageHelperStrategy(IPackageHelperStrategy, ABC):
    """
    Abstract base class for package helper strategies.
    
    Operations on a single package (installing, uninstalling, checking).
    All package helper strategies must extend this class.
    """
    
    @abstractmethod
    def install(self, package_name: str) -> bool:
        """Install the package."""
        ...
    
    @abstractmethod
    def uninstall(self, package_name: str) -> None:
        """Uninstall the package."""
        ...
    
    @abstractmethod
    def check_installed(self, name: str) -> bool:
        """Check if package is installed."""
        ...
    
    @abstractmethod
    def get_version(self, name: str) -> Optional[str]:
        """Get installed version."""
        ...

# =============================================================================
# ABSTRACT PACKAGE MANAGER STRATEGY
# =============================================================================

class APackageManagerStrategy(IPackageManagerStrategy, ABC):
    """
    Abstract base class for package manager strategies.
    
    Orchestrates multiple packages (installation, discovery, policy).
    All package manager strategies must extend this class.
    """
    
    @abstractmethod
    def install_package(self, package_name: str, module_name: Optional[str] = None) -> bool:
        """Install a package."""
        ...
    
    @abstractmethod
    def uninstall_package(self, package_name: str) -> None:
        """Uninstall a package."""
        ...
    
    @abstractmethod
    def discover_dependencies(self) -> dict[str, str]:
        """Discover dependencies."""
        ...
    
    @abstractmethod
    def check_security_policy(self, package_name: str) -> tuple[bool, str]:
        """Check security policy."""
        ...

# =============================================================================
# ABSTRACT INSTALLATION EXECUTION STRATEGY
# =============================================================================

class AInstallExecutionStrategy(IInstallExecutionStrategy, ABC):
    """
    Abstract base class for installation execution strategies.
    
    HOW to execute installation (pip, wheel, cached, async).
    """
    
    @abstractmethod
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """Execute installation of a package."""
        ...
    
    @abstractmethod
    def execute_uninstall(self, package_name: str) -> bool:
        """Execute uninstallation of a package."""
        ...

# =============================================================================
# ABSTRACT INSTALLATION TIMING STRATEGY
# =============================================================================

class AInstallTimingStrategy(IInstallTimingStrategy, ABC):
    """
    Abstract base class for installation timing strategies.
    
    WHEN to install packages (on-demand, upfront, temporary, etc.).
    """
    
    @abstractmethod
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """Determine if package should be installed now."""
        ...
    
    @abstractmethod
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """Determine if package should be uninstalled after use."""
        ...
    
    @abstractmethod
    def get_install_priority(self, packages: list[str]) -> list[str]:
        """Get priority order for installing packages."""
        ...

# =============================================================================
# ABSTRACT DISCOVERY STRATEGY
# =============================================================================

class ADiscoveryStrategy(IDiscoveryStrategy, ABC):
    """
    Abstract base class for discovery strategies.
    
    HOW to discover dependencies (from files, manifest, auto-detect).
    """
    
    @abstractmethod
    def discover(self, project_root: Any) -> dict[str, str]:
        """Discover dependencies from sources."""
        ...
    
    @abstractmethod
    def get_source(self, import_name: str) -> Optional[str]:
        """Get the source of a discovered dependency."""
        ...

# =============================================================================
# ABSTRACT POLICY STRATEGY
# =============================================================================

class APolicyStrategy(IPolicyStrategy, ABC):
    """
    Abstract base class for policy strategies.
    
    WHAT can be installed (security/policy enforcement).
    """
    
    @abstractmethod
    def is_allowed(self, package_name: str) -> tuple[bool, str]:
        """Check if package is allowed to be installed."""
        ...
    
    @abstractmethod
    def get_pip_args(self, package_name: str) -> list[str]:
        """Get pip arguments based on policy."""
        ...

# =============================================================================
# ABSTRACT MAPPING STRATEGY
# =============================================================================

class AMappingStrategy(IMappingStrategy, ABC):
    """
    Abstract base class for mapping strategies.
    
    HOW to map import names to package names.
    """
    
    @abstractmethod
    def map_import_to_package(self, import_name: str) -> Optional[str]:
        """Map import name to package name."""
        ...
    
    @abstractmethod
    def map_package_to_imports(self, package_name: str) -> list[str]:
        """Map package name to possible import names."""
        ...

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    'APackageHelper',
    'APackageHelperStrategy',
    'APackageManagerStrategy',
    'AInstallExecutionStrategy',
    'AInstallTimingStrategy',
    'ADiscoveryStrategy',
    'APolicyStrategy',
    'AMappingStrategy',
    # Enhanced Strategy Interfaces for Runtime Swapping
    'AInstallStrategy',
]

# =============================================================================
# ABSTRACT INSTALLATION STRATEGY (Enhanced for Runtime Swapping)
# =============================================================================

class AInstallStrategy(IInstallStrategy, ABC):
    """
    Abstract base class for installation strategies.
    
    Enables runtime strategy swapping for different installation methods
    (pip, wheel, async, cached, etc.).
    """
    
    @abstractmethod
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
        
        Default implementation returns True.
        Override for strategy-specific logic.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if can install, False otherwise
        """
        return True
    
    @abstractmethod
    def uninstall(self, package_name: str) -> bool:
        """
        Uninstall a package.
        
        Args:
            package_name: Package name to uninstall
            
        Returns:
            True if uninstallation successful, False otherwise
        """
        ...

