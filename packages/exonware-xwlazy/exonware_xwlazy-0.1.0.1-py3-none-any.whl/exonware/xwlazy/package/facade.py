"""
Package Operations Facade

Main facade: XWPackageHelper extends APackageHelper
Provides concrete implementation for all package operations.
Uses strategy pattern for caching, helper, and manager strategies.
"""

import sys
import subprocess
import importlib
import importlib.util
from typing import Optional

from .base import APackageHelper
from .services import InstallerEngine, LazyInstaller
from .services.strategy_registry import StrategyRegistry
from ..common.cache import InstallationCache
from ..common.logger import get_logger

logger = get_logger("xwlazy.package.facade")

# Import strategy interfaces
from ..contracts import (
    ICachingStrategy,
    IPackageHelperStrategy,
    IPackageManagerStrategy,
    IInstallExecutionStrategy,
    IInstallTimingStrategy,
    IDiscoveryStrategy,
    IPolicyStrategy,
    IMappingStrategy,
)

# Import default strategies
from ..common.strategies import InstallationCacheWrapper
from .strategies import (
    # Execution strategies
    PipExecution,
    # Timing strategies
    SmartTiming,
    # Discovery strategies
    HybridDiscovery,
    # Policy strategies
    PermissivePolicy,
    # Mapping strategies
    ManifestFirstMapping,
)

class XWPackageHelper(APackageHelper):
    """
    Concrete implementation of APackageHelper.
    
    Provides simple, clean API for working with packages (what you pip install).
    Uses xwlazy's InstallationCache for persistent caching and LazyInstaller for installation.
    """
    
    def __init__(
        self,
        package_name: str = 'default',
        project_root: Optional[str] = None,
        *,
        # Legacy strategy injection (for backward compatibility)
        caching_strategy: Optional[ICachingStrategy] = None,
        helper_strategy: Optional[IPackageHelperStrategy] = None,
        manager_strategy: Optional[IPackageManagerStrategy] = None,
        # New strategy types
        execution_strategy: Optional[IInstallExecutionStrategy] = None,
        timing_strategy: Optional[IInstallTimingStrategy] = None,
        discovery_strategy: Optional[IDiscoveryStrategy] = None,
        policy_strategy: Optional[IPolicyStrategy] = None,
        mapping_strategy: Optional[IMappingStrategy] = None,
    ):
        """
        Initialize XW package helper.
        
        Args:
            package_name: Package name for isolation (defaults to 'default')
            project_root: Root directory of project (auto-detected if None)
            caching_strategy: Optional caching strategy. If None, uses InstallationCache.
            helper_strategy: Optional helper strategy (legacy, deprecated).
            manager_strategy: Optional manager strategy (legacy, deprecated).
            execution_strategy: Optional execution strategy. If None, uses PipExecution.
            timing_strategy: Optional timing strategy. If None, uses SmartTiming.
            discovery_strategy: Optional discovery strategy. If None, uses HybridDiscovery.
            policy_strategy: Optional policy strategy. If None, uses PermissivePolicy.
            mapping_strategy: Optional mapping strategy. If None, uses ManifestFirstMapping.
        """
        super().__init__(package_name, project_root)
        
        # Default strategies (legacy - deprecated, kept for backward compatibility)
        if caching_strategy is None:
            caching_strategy = InstallationCacheWrapper()
        # Legacy helper_strategy and manager_strategy are deprecated
        # They are kept for backward compatibility but not used
        
        # Check registry for stored strategies, otherwise use defaults
        if execution_strategy is None:
            execution_strategy = StrategyRegistry.get_package_strategy(package_name, 'execution')
            if execution_strategy is None:
                execution_strategy = PipExecution()
        if timing_strategy is None:
            timing_strategy = StrategyRegistry.get_package_strategy(package_name, 'timing')
            if timing_strategy is None:
                timing_strategy = SmartTiming()
        if discovery_strategy is None:
            discovery_strategy = StrategyRegistry.get_package_strategy(package_name, 'discovery')
            if discovery_strategy is None:
                discovery_strategy = HybridDiscovery(package_name, project_root)
        if policy_strategy is None:
            policy_strategy = StrategyRegistry.get_package_strategy(package_name, 'policy')
            if policy_strategy is None:
                policy_strategy = PermissivePolicy()
        if mapping_strategy is None:
            mapping_strategy = StrategyRegistry.get_package_strategy(package_name, 'mapping')
            if mapping_strategy is None:
                mapping_strategy = ManifestFirstMapping(package_name)
        
        # Store strategies
        self._caching = caching_strategy
        self._helper = helper_strategy  # Legacy, deprecated
        self._manager = manager_strategy  # Legacy, deprecated
        self._execution = execution_strategy
        self._timing = timing_strategy
        self._discovery = discovery_strategy
        self._policy = policy_strategy
        self._mapping = mapping_strategy
        
        # Legacy support (for backward compatibility)
        self._install_cache = InstallationCache()
        self._installer = None  # Lazy init to avoid circular imports
        self._install_engine = InstallerEngine(package_name)
    
    def _get_installer(self):
        """Get lazy installer instance (lazy init)."""
        if self._installer is None:
            self._installer = LazyInstaller(self._package_name)
        return self._installer
    
    def _check_importability(self, package_name: str) -> bool:
        """
        Check if package is importable.
        
        Uses importlib.util.find_spec to check if package can be imported.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if importable, False otherwise
        """
        try:
            spec = importlib.util.find_spec(package_name)
            return spec is not None
        except (ValueError, AttributeError, ImportError):
            return False
    
    def _check_persistent_cache(self, package_name: str) -> bool:
        """
        Check persistent cache for package installation status.
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if found in persistent cache as installed, False otherwise
        """
        return self._install_cache.is_installed(package_name)
    
    def _mark_installed_in_persistent_cache(self, package_name: str) -> None:
        """
        Mark package as installed in persistent cache.
        
        Args:
            package_name: Package name to mark
        """
        version = self._get_installer()._get_installed_version(package_name)
        self._install_cache.mark_installed(package_name, version)
    
    def _mark_uninstalled_in_persistent_cache(self, package_name: str) -> None:
        """
        Mark package as uninstalled in persistent cache.
        
        Args:
            package_name: Package name to mark
        """
        self._install_cache.mark_uninstalled(package_name)
    
    def _run_install(self, *package_names: str) -> None:
        """
        Run pip install for packages.
        
        Uses execution strategy and timing strategy to determine when/how to install.
        
        Args:
            *package_names: Package names to install
            
        Raises:
            RuntimeError: If installation fails
        """
        if not package_names:
            return
        
        # Get policy args for each package
        policy_args_map = {}
        for package_name in package_names:
            # Check if should install now (timing strategy)
            if not self._timing.should_install_now(package_name, None):
                continue
            
            # Get pip args from policy strategy
            policy_args = self._policy.get_pip_args(package_name)
            policy_args_map[package_name] = policy_args
        
        # Execute installations using execution strategy
        for package_name, policy_args in policy_args_map.items():
            result = self._execution.execute_install(package_name, policy_args)
            
            # Handle result
            if hasattr(result, 'success') and result.success:
                with self._lock:
                    self._installed_packages.add(package_name)
                    self._uninstalled_packages.discard(package_name)
                    self._mark_installed_in_persistent_cache(package_name)
            else:
                with self._lock:
                    self._failed_packages.add(package_name)
                    error_msg = getattr(result, 'error', 'Unknown error') if hasattr(result, 'error') else str(result)
                    raise RuntimeError(f"Failed to install {package_name}: {error_msg}")
    
    def _run_uninstall(self, *package_names: str) -> None:
        """
        Run pip uninstall for packages.
        
        Uses execution strategy for uninstallation.
        
        Args:
            *package_names: Package names to uninstall
            
        Raises:
            RuntimeError: If uninstallation fails
        """
        if not package_names:
            return
        
        for package_name in package_names:
            # Check if should uninstall (timing strategy)
            if self._timing.should_uninstall_after(package_name, None):
                success = self._execution.execute_uninstall(package_name)
                if success:
                    with self._lock:
                        self._installed_packages.discard(package_name)
                        self._uninstalled_packages.add(package_name)
                        self._mark_uninstalled_in_persistent_cache(package_name)
                else:
                    raise RuntimeError(f"Failed to uninstall {package_name}")
    
    # Abstract methods from APackage that need implementation
    def _discover_from_sources(self) -> None:
        """Discover dependencies from all sources."""
        # Use discovery strategy
        deps = self._discovery.discover(self._project_root)
        # Convert to DependencyInfo format
        from ..defs import DependencyInfo
        for import_name, package_name in deps.items():
            self.discovered_dependencies[import_name] = DependencyInfo(
                import_name=import_name,
                package_name=package_name,
                source=self._discovery.get_source(import_name) or 'discovery',
                category='discovered'
            )
    
    def _is_cache_valid(self) -> bool:
        """Check if cached dependencies are still valid."""
        # Delegate to discovery strategy which has cache validation logic
        if hasattr(self._discovery, '_is_cache_valid'):
            return self._discovery._is_cache_valid()
        # Fallback: if discovery doesn't support cache validation, assume invalid
        return False
    
    def _add_common_mappings(self) -> None:
        """Add common import -> package mappings."""
        # Use mapping strategy to discover mappings
        # This is called during initialization to populate common mappings
        # The mapping strategy handles this internally
        pass
    
    def _update_file_mtimes(self) -> None:
        """Update file modification times for cache validation."""
        # Delegate to discovery strategy which tracks file modification times
        if hasattr(self._discovery, '_update_file_mtimes'):
            self._discovery._update_file_mtimes()
    
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
    
    def swap_helper_strategy(self, new_strategy: IPackageHelperStrategy) -> None:
        """
        Swap helper/installer strategy at runtime.
        
        Args:
            new_strategy: New helper strategy to use
        """
        self._helper = new_strategy
        # Update manager if it uses helper
        if hasattr(self._manager, '_helper'):
            self._manager._helper = new_strategy
    
    def swap_manager_strategy(self, new_strategy: IPackageManagerStrategy) -> None:
        """
        Swap manager strategy at runtime.
        
        Args:
            new_strategy: New manager strategy to use
        """
        self._manager = new_strategy
    
    def swap_execution_strategy(self, new_strategy: IInstallExecutionStrategy) -> None:
        """
        Swap execution strategy at runtime.
        
        Args:
            new_strategy: New execution strategy to use
        """
        self._execution = new_strategy
    
    def swap_timing_strategy(self, new_strategy: IInstallTimingStrategy) -> None:
        """
        Swap timing strategy at runtime.
        
        Args:
            new_strategy: New timing strategy to use
        """
        self._timing = new_strategy
    
    def swap_discovery_strategy(self, new_strategy: IDiscoveryStrategy) -> None:
        """
        Swap discovery strategy at runtime.
        
        Args:
            new_strategy: New discovery strategy to use
        """
        self._discovery = new_strategy
    
    def swap_policy_strategy(self, new_strategy: IPolicyStrategy) -> None:
        """
        Swap policy strategy at runtime.
        
        Args:
            new_strategy: New policy strategy to use
        """
        self._policy = new_strategy
    
    def swap_mapping_strategy(self, new_strategy: IMappingStrategy) -> None:
        """
        Swap mapping strategy at runtime.
        
        Args:
            new_strategy: New mapping strategy to use
        """
        self._mapping = new_strategy
    
    def install_package(self, package_name: str, module_name: Optional[str] = None) -> bool:
        """
        Install a package.
        
        Uses timing strategy to determine if should install now,
        then uses execution strategy to perform installation.
        
        Args:
            package_name: Package name to install
            module_name: Optional module name (for mapping)
            
        Returns:
            True if installed successfully, False otherwise
        """
        # Map module name to package name if needed (using mapping strategy)
        if module_name and not package_name:
            package_name = self._mapping.map_import_to_package(module_name) or module_name
        
        # Check timing strategy
        if not self._timing.should_install_now(package_name, {'module_name': module_name}):
            return False
        
        # Check policy strategy
        allowed, reason = self._policy.is_allowed(package_name)
        if not allowed:
            raise RuntimeError(f"Package {package_name} blocked by policy: {reason}")
        
        # Get pip args from policy
        policy_args = self._policy.get_pip_args(package_name)
        
        # Execute installation
        result = self._execution.execute_install(package_name, policy_args)
        
        # Handle result
        if hasattr(result, 'success') and result.success:
            with self._lock:
                self._installed_packages.add(package_name)
                self._uninstalled_packages.discard(package_name)
                self._mark_installed_in_persistent_cache(package_name)
            return True
        else:
            with self._lock:
                self._failed_packages.add(package_name)
            return False
    
    def _check_security_policy(self, package_name: str):
        """Check security policy for package."""
        # Use policy strategy
        return self._policy.is_allowed(package_name)
    
    def _run_pip_install(self, package_name: str, args: list) -> bool:
        """Run pip install with arguments."""
        try:
            self._run_install(package_name)
            return True
        except (RuntimeError, subprocess.CalledProcessError, OSError) as e:
            logger.debug(f"Failed to install {package_name}: {e}")
            return False
        except Exception as e:
            # Catch-all for unexpected errors, but log them
            logger.warning(f"Unexpected error installing {package_name}: {e}")
            return False
    
    def is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        # Use caching strategy if it supports validation
        if hasattr(self._caching, 'is_valid') and self._caching is not None:
            return self._caching.is_valid(key)
        # Fallback: check if key exists in cache
        return self.get_cached(key) is not None
    
    # IConfigManager methods (delegate to LazyInstallConfig)
    def is_enabled(self, package_name: str) -> bool:
        """
        Check if lazy install is enabled for a package (from IConfigManager).
        
        This method delegates to LazyInstallConfig to avoid method name conflict
        with the instance method is_enabled().
        
        Args:
            package_name: Package name to check
            
        Returns:
            True if enabled, False otherwise
        """
        from .services.config_manager import LazyInstallConfig
        return LazyInstallConfig.is_enabled(package_name)
    
    def get_mode(self, package_name: str) -> str:
        """Get installation mode for a package (from IConfigManager)."""
        from .services.config_manager import LazyInstallConfig
        return LazyInstallConfig.get_mode(package_name)
    
    def get_load_mode(self, package_name: str):
        """Get load mode for a package (from IConfigManager)."""
        from .services.config_manager import LazyInstallConfig
        return LazyInstallConfig.get_load_mode(package_name)
    
    def get_install_mode(self, package_name: str):
        """Get install mode for a package (from IConfigManager)."""
        from .services.config_manager import LazyInstallConfig
        return LazyInstallConfig.get_install_mode(package_name)
    
    def get_mode_config(self, package_name: str):
        """Get full mode configuration for a package (from IConfigManager)."""
        from .services.config_manager import LazyInstallConfig
        return LazyInstallConfig.get_mode_config(package_name)

