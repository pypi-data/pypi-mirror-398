"""
#exonware/xwlazy/src/exonware/xwlazy/facade.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Facade for Lazy Loading System

This module provides a unified public API facade for the lazy loading system
following GUIDE_ARCH.md structure. It consolidates all public APIs into a
single entry point.

Design Pattern: Facade Pattern
- Provides simplified interface to complex subsystem
- Hides implementation details
- Centralizes public API
"""

import os
import sys
import subprocess
import importlib
import importlib.util
from typing import Optional, Any
from types import ModuleType

# Import from contracts for types
from .defs import LazyInstallMode, LazyLoadMode, LazyModeConfig
from .defs import PRESET_MODES, get_preset_mode

# Import from new structure modules
from .package.services.config_manager import LazyInstallConfig
from .common.services import LazyStateManager
from .runtime.metrics import MetricsCollector, get_metrics_collector
from .runtime.performance import LazyPerformanceMonitor
from .package.services.manifest import get_manifest_loader, refresh_manifest_cache
from .common.logger import get_logger, log_event as _log
# Import directly from submodule bases
from .package.base import APackageHelper
from .module.base import AModuleHelper
from .runtime.base import ARuntimeHelper
# Import concrete implementations from new folder structure
from .package import XWPackageHelper
from .module import XWModuleHelper
from .runtime import XWRuntimeHelper

# Import from domain modules
from .package.services.discovery import get_lazy_discovery as _get_lazy_discovery
from .common.services.dependency_mapper import DependencyMapper
from .common.services import (
    enable_keyword_detection as _enable_keyword_detection,
    is_keyword_detection_enabled as _is_keyword_detection_enabled,
    get_keyword_detection_keyword as _get_keyword_detection_keyword,
    check_package_keywords as _check_package_keywords,
    _detect_lazy_installation,
    _detect_meta_info_mode,
)
from .package.services import (
    LazyInstallerRegistry,
    LazyInstaller,
    LazyInstallPolicy,
    is_externally_managed as _is_externally_managed,
)
from .common.cache import InstallationCache
from .module.importer_engine import (
    install_import_hook as _install_import_hook,
    uninstall_import_hook as _uninstall_import_hook,
    is_import_hook_installed as _is_import_hook_installed,
    register_lazy_module_prefix as _register_lazy_module_prefix,
    register_lazy_module_methods as _register_lazy_module_methods,
    register_lazy_package as _register_lazy_package,
    install_global_import_hook as _install_global_import_hook,
    is_global_import_hook_installed as _is_global_import_hook_installed,
    LazyImporter,
    LazyModuleRegistry,
)

logger = get_logger("xwlazy.facade")

# Global instances
_lazy_importer = LazyImporter()
_lazy_module_registry = LazyModuleRegistry()

# =============================================================================
# FACADE CLASS
# =============================================================================

class LazyModeFacade:
    """
    Facade class for managing lazy mode configuration and operations.
    
    This class provides a unified interface to all lazy loading functionality.
    """
    
    def __init__(self):
        self._enabled = False
        self._strategy = "on_demand"
        self._configs: dict[str, Any] = {}
    
    def enable(self, strategy: str = "on_demand", **kwargs) -> None:
        """Enable lazy mode with specified strategy."""
        self._enabled = True
        self._strategy = strategy
        self._configs.update(kwargs)
        logger.info(f"Lazy mode enabled with strategy: {strategy}")
    
    def disable(self) -> None:
        """Disable lazy mode and cleanup resources."""
        self._enabled = False
        logger.info("Lazy mode disabled")
    
    def is_enabled(self) -> bool:
        """Check if lazy mode is currently enabled."""
        return self._enabled
    
    def get_stats(self) -> dict[str, Any]:
        """Get lazy mode performance statistics."""
        return {
            "enabled": self._enabled,
            "strategy": self._strategy,
            "configs": self._configs.copy(),
        }

# Global facade instance
_lazy_facade = LazyModeFacade()

# =============================================================================
# FACADE FUNCTIONS
# =============================================================================

def enable_lazy_mode(strategy: str = "on_demand", **kwargs) -> None:
    """Enable lazy mode with specified strategy."""
    _lazy_facade.enable(strategy, **kwargs)

def disable_lazy_mode() -> None:
    """Disable lazy mode and cleanup resources."""
    _lazy_facade.disable()

def is_lazy_mode_enabled() -> bool:
    """Check if lazy mode is currently enabled."""
    return _lazy_facade.is_enabled()

def get_lazy_mode_stats() -> dict[str, Any]:
    """Get lazy mode performance statistics."""
    return _lazy_facade.get_stats()

def configure_lazy_mode(package_name: str, config: LazyModeConfig) -> None:
    """Configure lazy mode for a specific package."""
    # Use set() method with mode_config parameter
    LazyInstallConfig.set(package_name, True, mode_config=config)
    logger.info(f"Configured lazy mode for {package_name}")

def preload_modules(package_name: str, modules: list[str]) -> None:
    """Preload specified modules for a package."""
    for module_name in modules:
        _lazy_importer.preload_module(module_name)
    logger.info(f"Preloaded {len(modules)} modules for {package_name}")

def optimize_lazy_mode(package_name: str) -> None:
    """Optimize lazy mode configuration for a package."""
    _lazy_module_registry.preload_frequently_used()
    logger.info(f"Optimization completed for {package_name}")

# =============================================================================
# ONE-LINE ACTIVATION API
# =============================================================================

def auto_enable_lazy(package_name: Optional[str] = None, mode: str = "smart") -> bool:
    """
    Auto-enable lazy mode for a package - ONE LINE ACTIVATION!
    
    Usage in any library's __init__.py:
        from exonware.xwlazy import auto_enable_lazy
        auto_enable_lazy(__package__)
    
    Args:
        package_name: Package name (auto-detected if None)
        mode: Lazy mode ("smart", "lite", "full", "clean", "temporary")
    
    Returns:
        True if enabled, False otherwise
    """
    import inspect
    
    # Auto-detect package name from caller
    if package_name is None:
        try:
            frame = inspect.currentframe().f_back
            package_name = (frame.f_globals.get('__package__') or 
                          frame.f_globals.get('__name__', '').split('.')[0])
        except Exception:
            logger.warning("Could not auto-detect package name")
            return False
    
    if not package_name:
        logger.warning("Package name is required")
        return False
    
    try:
        # Get preset mode configuration
        config = get_preset_mode(mode)
        if config is None:
            logger.warning(f"Unknown mode: {mode}, using 'smart'")
            config = get_preset_mode("smart")
        
        # Register package for lazy loading/installation
        _register_lazy_package(package_name, config)
        
        # Enable lazy install for this package with mode config
        # Pass mode_config through set() method (not a separate set_mode_config method)
        LazyInstallConfig.set(
            package_name, 
            True, 
            mode=mode,
            mode_config=config
        )
        
        # Install global import hook if not already installed
        if not _is_global_import_hook_installed():
            _install_global_import_hook()
        
        # Also install meta_path hook for compatibility
        _install_import_hook(package_name)
        
        logger.info(f"✅ Auto-enabled lazy mode for package: {package_name} (mode: {mode})")
        return True
    except Exception as e:
        logger.error(f"Failed to auto-enable lazy mode for {package_name}: {e}")
        return False

def attach(package_name: str, submodules: Optional[list[str]] = None, submod_attrs: Optional[dict[str, list[str]]] = None):
    """
    Attach lazily loaded submodules and attributes (lazy-loader compatible API).
    
    Returns (__getattr__, __dir__, __all__) for lazy loading.
    
    Usage:
        __getattr__, __dir__, __all__ = lazy.attach(__name__, ['submodule1'], {'module': ['attr1', 'attr2']})
    
    Args:
        package_name: Package name (typically __name__)
        submodules: List of submodule names to attach
        submod_attrs: Dict mapping submodule -> list of attributes/functions
    
    Returns:
        Tuple of (__getattr__, __dir__, __all__)
    """
    import importlib
    
    if submod_attrs is None:
        submod_attrs = {}
    if submodules is None:
        submodules = []
    
    submodules_set = set(submodules)
    attr_to_modules = {
        attr: mod for mod, attrs in submod_attrs.items() for attr in attrs
    }
    
    __all__ = sorted(submodules_set | attr_to_modules.keys())
    
    def __getattr__(name: str) -> Any:
        """Lazy load submodule or attribute on first access."""
        if name in submodules_set:
            return importlib.import_module(f"{package_name}.{name}")
        elif name in attr_to_modules:
            submod_path = f"{package_name}.{attr_to_modules[name]}"
            submod = importlib.import_module(submod_path)
            attr = getattr(submod, name)
            
            # If attribute lives in a file with same name as attribute,
            # ensure attribute (not module) is accessible
            if name == attr_to_modules[name]:
                pkg = sys.modules[package_name]
                pkg.__dict__[name] = attr
            
            return attr
        else:
            raise AttributeError(f"module {package_name!r} has no attribute {name!r}")
    
    def __dir__() -> list[str]:
        """Return list of available attributes."""
        return __all__.copy()
    
    # Eager import if EAGER_IMPORT env var is set (for debugging)
    if os.environ.get("EAGER_IMPORT", ""):
        for attr in set(attr_to_modules.keys()) | submodules_set:
            __getattr__(attr)
    
    return __getattr__, __dir__, __all__.copy()

# =============================================================================
# PUBLIC API FUNCTIONS - Installation
# =============================================================================

def enable_lazy_install(package_name: str) -> None:
    """Enable lazy installation for a package."""
    LazyInstallConfig.set(package_name, True)

def disable_lazy_install(package_name: str) -> None:
    """Disable lazy installation for a package."""
    LazyInstallConfig.set(package_name, False)

def is_lazy_install_enabled(package_name: str) -> bool:
    """Check if lazy installation is enabled for a package."""
    return LazyInstallConfig.is_enabled(package_name)

def set_lazy_install_mode(package_name: str, mode: LazyInstallMode) -> None:
    """Set lazy installation mode for a package."""
    LazyInstallConfig.set_install_mode(package_name, mode)

def get_lazy_install_mode(package_name: str) -> LazyInstallMode:
    """Get lazy installation mode for a package."""
    return LazyInstallConfig.get_install_mode(package_name)

def install_missing_package(package_name: str, module_name: str, installer_package: str = 'default') -> bool:
    """Install a missing package for a module."""
    try:
        installer = LazyInstallerRegistry.get_instance(installer_package)
        if not installer.is_enabled():
            logger.debug(f"Lazy installation disabled for {installer_package}")
            return False
        return installer.install_package(package_name, module_name)
    except Exception as e:
        logger.error(f"Failed to install package {package_name} for {installer_package}: {e}")
        return False

def install_and_import(module_name: str, package_name: str = None, installer_package: str = 'default') -> tuple[Optional[ModuleType], bool]:
    """Install package and import module."""
    try:
        installer = LazyInstallerRegistry.get_instance(installer_package)
        if not installer.is_enabled():
            logger.debug(f"Lazy installation disabled for {installer_package}")
            return None, False
        return installer.install_and_import(module_name, package_name)
    except Exception as e:
        logger.error(f"Failed to install and import {module_name} for {installer_package}: {e}")
        return None, False

def get_lazy_install_stats(package_name: str) -> dict[str, Any]:
    """Get installation statistics for a package."""
    try:
        installer = LazyInstallerRegistry.get_instance(package_name)
        return installer.get_stats()
    except Exception as e:
        logger.error(f"Failed to get stats for {package_name}: {e}")
        return {
            'enabled': False,
            'mode': 'unknown',
            'package_name': package_name,
            'installed_packages': [],
            'failed_packages': [],
            'total_installed': 0,
            'total_failed': 0,
        }

def get_all_lazy_install_stats() -> dict[str, dict[str, Any]]:
    """Get installation statistics for all packages."""
    try:
        all_instances = LazyInstallerRegistry.get_all_instances()
        return {pkg_name: installer.get_stats() for pkg_name, installer in all_instances.items()}
    except Exception as e:
        logger.error(f"Failed to get all stats: {e}")
        return {}

def lazy_import_with_install(module_name: str, package_name: str = None, installer_package: str = 'default') -> tuple[Optional[ModuleType], bool]:
    """Lazy import with automatic installation."""
    try:
        installer = LazyInstallerRegistry.get_instance(installer_package)
        if not installer.is_enabled():
            logger.debug(f"Lazy installation disabled for {installer_package}")
            return None, False
        return installer.install_and_import(module_name, package_name)
    except Exception as e:
        logger.error(f"Failed to lazy import with install {module_name} for {installer_package}: {e}")
        return None, False

def xwimport(module_name: str, package_name: str = None, installer_package: str = 'default') -> Any:
    """Simple lazy import with automatic installation."""
    module, available = lazy_import_with_install(module_name, package_name, installer_package)
    if not available:
        raise ImportError(f"Module {module_name} is not available and could not be installed")
    return module

# =============================================================================
# HOOK FUNCTIONS
# =============================================================================

def install_import_hook(package_name: str = 'default') -> None:
    """Install performant import hook for automatic lazy installation."""
    try:
        _install_import_hook(package_name)
        logger.debug(f"Import hook installed for {package_name}")
    except Exception as e:
        logger.error(f"Failed to install import hook for {package_name}: {e}")
        raise

def uninstall_import_hook(package_name: str = 'default') -> None:
    """Uninstall import hook for a package."""
    try:
        _uninstall_import_hook(package_name)
        logger.debug(f"Import hook uninstalled for {package_name}")
    except Exception as e:
        logger.error(f"Failed to uninstall import hook for {package_name}: {e}")
        raise

def is_import_hook_installed(package_name: str = 'default') -> bool:
    """Check if import hook is installed for a package."""
    try:
        return _is_import_hook_installed(package_name)
    except Exception:
        return False

# =============================================================================
# LAZY LOADING FUNCTIONS
# =============================================================================

def enable_lazy_imports(mode: LazyLoadMode = LazyLoadMode.AUTO, package_name: Optional[str] = None) -> None:
    """
    Enable lazy imports.
    
    This is a global setting that applies to all packages. The package_name
    parameter is optional and used only for logging purposes.
    
    Args:
        mode: The lazy load mode to use (default: LazyLoadMode.AUTO)
        package_name: Optional package name for logging purposes
    """
    try:
        _lazy_importer.enable(mode)
        # Note: _patch_import_module removed - using sys.meta_path hooks instead
        if package_name:
            logger.debug(f"Lazy imports enabled for {package_name} with mode {mode}")
        else:
            logger.debug(f"Lazy imports enabled with mode {mode}")
    except Exception as e:
        if package_name:
            logger.error(f"Failed to enable lazy imports for {package_name}: {e}")
        else:
            logger.error(f"Failed to enable lazy imports: {e}")
        raise

def disable_lazy_imports(package_name: Optional[str] = None) -> None:
    """
    Disable lazy imports.
    
    This is a global setting that applies to all packages. The package_name
    parameter is optional and used only for logging purposes.
    
    Args:
        package_name: Optional package name for logging purposes
    """
    try:
        _lazy_importer.disable()
        # Also unpatch import_module (from archive)
        from .module.importer_engine import _unpatch_import_module
        _unpatch_import_module()
        if package_name:
            logger.info(f"Lazy imports disabled for {package_name}")
        else:
            logger.info("Lazy imports disabled")
    except Exception as e:
        if package_name:
            logger.error(f"Failed to disable lazy imports for {package_name}: {e}")
        else:
            logger.error(f"Failed to disable lazy imports: {e}")
        raise

def is_lazy_import_enabled(package_name: Optional[str] = None) -> bool:
    """
    Check if lazy imports are enabled.
    
    This checks a global setting that applies to all packages. The package_name
    parameter is optional and used only for logging purposes.
    
    Args:
        package_name: Optional package name for logging purposes
    
    Returns:
        True if lazy imports are enabled globally
    """
    try:
        return _lazy_importer.is_enabled()
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Error checking lazy import status: {e}")
        return False
    except Exception as e:
        # Unexpected errors - log but return False for safety
        logger.warning(f"Unexpected error checking lazy import status: {e}")
        return False

def lazy_import(module_name: str, package_name: str = None) -> Optional[ModuleType]:
    """Lazy import a module."""
    try:
        return _lazy_importer.import_module(module_name, package_name)
    except Exception as e:
        logger.error(f"Failed to lazy import {module_name}: {e}")
        return None

def register_lazy_module(module_name: str, package_name: str = None, module_path: str = None) -> None:
    """Register a lazy module loader."""
    try:
        if module_path is None:
            module_path = module_name
        _lazy_importer.register_lazy_module(module_name, module_path)
        # Also register in global registry (from archive)
        _lazy_module_registry.register_module(module_name, module_path)
        logger.info(f"Lazy module registered: {module_name}")
    except Exception as e:
        logger.error(f"Failed to register lazy module {module_name}: {e}")
        raise

def preload_module(module_name: str, package_name: str = None) -> None:
    """Preload a lazy module."""
    try:
        success = _lazy_importer.preload_module(module_name)
        if success:
            logger.info(f"Preload completed: {module_name}")
        else:
            logger.warning(f"Preload failed for {module_name}")
    except Exception as e:
        logger.error(f"Failed to preload module {module_name}: {e}")
        raise

def get_lazy_module(module_name: str, package_name: str = None) -> Optional[ModuleType]:
    """Get a lazy module if loaded."""
    # Check if module is already loaded in importer
    stats = _lazy_importer.get_stats()
    if module_name in stats.get('loaded_modules', []):
        # Module is loaded, return it via import (safe since it's cached)
        try:
            import importlib
            return importlib.import_module(module_name)
        except ImportError:
            pass
    
    # Fallback to registry
    try:
        loader = _lazy_module_registry.get_module(module_name)
        if loader.is_loaded():
            return loader.load_module()
    except KeyError:
        pass
    
    # Check sys.modules as final fallback
    import sys
    return sys.modules.get(module_name)

def get_loading_stats(package_name: str) -> dict[str, Any]:
    """Get loading statistics for a package."""
    try:
        return _lazy_module_registry.get_stats()
    except Exception as e:
        logger.error(f"Failed to get loading stats for {package_name}: {e}")
        return {
            'total_registered': 0,
            'loaded_count': 0,
            'unloaded_count': 0,
            'access_counts': {},
            'load_times': {},
        }

def preload_frequently_used(package_name: str) -> None:
    """Preload frequently used modules for a package."""
    try:
        _lazy_module_registry.preload_frequently_used()
        logger.info(f"Preload frequently used completed for {package_name}")
    except Exception as e:
        logger.error(f"Failed to preload frequently used for {package_name}: {e}")

def get_lazy_import_stats(package_name: str) -> dict[str, Any]:
    """Get lazy import statistics for a package."""
    try:
        return _lazy_importer.get_stats()
    except Exception as e:
        logger.error(f"Failed to get lazy import stats for {package_name}: {e}")
        return {
            'enabled': False,
            'registered_modules': [],
            'loaded_modules': [],
            'access_counts': {},
            'total_registered': 0,
            'total_loaded': 0,
        }

# =============================================================================
# CONFIGURATION FUNCTIONS
# =============================================================================

def config_package_lazy_install_enabled(
    package_name: str, 
    enabled: bool = None,
    mode: str = "auto",
    install_hook: bool = True,
    load_mode: Optional[LazyLoadMode] = None,
    install_mode: Optional[LazyInstallMode] = None,
    mode_config: Optional[LazyModeConfig] = None,
    # Strategy parameters
    execution_strategy: Optional[Any] = None,
    timing_strategy: Optional[Any] = None,
    discovery_strategy: Optional[Any] = None,
    policy_strategy: Optional[Any] = None,
    mapping_strategy: Optional[Any] = None,
) -> bool:
    """
    Configure lazy installation for a package.
    
    Args:
        package_name: Package name to configure
        enabled: Whether lazy installation is enabled (None = auto-detect)
        mode: Installation mode string (e.g., "smart", "full", "clean")
        install_hook: Whether to install the import hook
        load_mode: Optional explicit load mode
        install_mode: Optional explicit install mode
        mode_config: Optional full mode configuration
        execution_strategy: Optional custom execution strategy instance
        timing_strategy: Optional custom timing strategy instance
        discovery_strategy: Optional custom discovery strategy instance
        policy_strategy: Optional custom policy strategy instance
        mapping_strategy: Optional custom mapping strategy instance
        
    Returns:
        True if enabled, False otherwise
    """
    try:
        # Store strategies if provided
        from .package.services.strategy_registry import StrategyRegistry
        if execution_strategy is not None:
            StrategyRegistry.set_package_strategy(package_name, 'execution', execution_strategy)
        if timing_strategy is not None:
            StrategyRegistry.set_package_strategy(package_name, 'timing', timing_strategy)
        if discovery_strategy is not None:
            StrategyRegistry.set_package_strategy(package_name, 'discovery', discovery_strategy)
        if policy_strategy is not None:
            StrategyRegistry.set_package_strategy(package_name, 'policy', policy_strategy)
        if mapping_strategy is not None:
            StrategyRegistry.set_package_strategy(package_name, 'mapping', mapping_strategy)
        
        manual_override = enabled is not None
        if enabled is None:
            enabled = _detect_lazy_installation(package_name)
        
        # Check meta info for mode override
        if mode == "auto" and enabled:
            meta_mode = _detect_meta_info_mode(package_name)
            if meta_mode:
                mode = meta_mode
        
        # Resolve preset mode if provided
        if load_mode is None and install_mode is None and mode_config is None:
            preset = get_preset_mode(mode)
            if preset:
                mode_config = preset
        
        LazyInstallConfig.set(
            package_name,
            enabled,
            mode,
            install_hook=install_hook,
            manual=manual_override,
            load_mode=load_mode,
            install_mode=install_mode,
            mode_config=mode_config,
        )
        
        # Register package for global __import__ hook (for module-level imports)
        if enabled:
            try:
                from .module.importer_engine import register_lazy_package, install_global_import_hook
                # Register package for global hook
                register_lazy_package(package_name, mode_config)
                # Install global hook if not already installed
                install_global_import_hook()
            except Exception as global_hook_error:
                logger.warning(f"Failed to register package for global hook {package_name}: {global_hook_error}")
        
        # Install meta_path hook if requested and enabled
        if install_hook and enabled:
            try:
                install_import_hook(package_name)
            except Exception as hook_error:
                logger.warning(f"Failed to install import hook for {package_name}: {hook_error}")
        
        result = LazyInstallConfig.is_enabled(package_name)
        logger.debug(f"Configured lazy installation for {package_name}: enabled={result}, mode={mode}")
        return result
    except Exception as e:
        logger.error(f"Failed to configure lazy installation for {package_name}: {e}")
        raise

def config_module_lazy_load_enabled(
    package_name: str,
    enabled: bool = True,
    load_mode: Optional[LazyLoadMode] = None,
    # Strategy parameters
    helper_strategy: Optional[Any] = None,
    manager_strategy: Optional[Any] = None,
    caching_strategy: Optional[Any] = None,
) -> bool:
    """
    Configure lazy loading for modules in a package.
    
    Args:
        package_name: Package name to configure
        enabled: Whether lazy loading is enabled (default: True)
        load_mode: Optional explicit load mode
        helper_strategy: Optional custom helper strategy instance
        manager_strategy: Optional custom manager strategy instance
        caching_strategy: Optional custom caching strategy instance
        
    Returns:
        True if enabled, False otherwise
    """
    try:
        # Store strategies if provided
        from .package.services.strategy_registry import StrategyRegistry
        if helper_strategy is not None:
            StrategyRegistry.set_module_strategy(package_name, 'helper', helper_strategy)
        if manager_strategy is not None:
            StrategyRegistry.set_module_strategy(package_name, 'manager', manager_strategy)
        if caching_strategy is not None:
            StrategyRegistry.set_module_strategy(package_name, 'caching', caching_strategy)
        
        # Enable lazy imports if requested
        if enabled:
            if load_mode is None:
                load_mode = LazyLoadMode.AUTO
            enable_lazy_imports(load_mode, package_name=package_name)
        else:
            disable_lazy_imports(package_name=package_name)
        
        logger.info(f"Configured lazy loading for {package_name}: enabled={enabled}, load_mode={load_mode}")
        return enabled
    except Exception as e:
        logger.error(f"Failed to configure lazy loading for {package_name}: {e}")
        raise

def sync_manifest_configuration(package_name: str) -> None:
    """
    Sync configuration from manifest for a specific package.
    
    This syncs all manifest settings including:
    - Dependencies
    - Watched prefixes
    - Class wrap prefixes (registered as package class hints)
    - Async configuration
    """
    try:
        from .module.importer_engine import _set_package_class_hints
        
        from .package.services.manifest import _normalize_package_name, get_manifest_loader as _get_manifest_loader
        package_key = _normalize_package_name(package_name)
        
        # Get the loader instance - this ensures we use the same instance throughout
        # This is critical for tests that patch get_manifest_loader
        loader = _get_manifest_loader()
        
        # Sync manifest configuration using the loader instance directly
        # This ensures we use the same loader instance that we'll use to get the manifest
        loader.sync_manifest_configuration(package_name)
        
        # Register class wrap prefixes from manifest as package class hints
        # After sync, the manifest cache is cleared, so get_manifest will reload it
        manifest = loader.get_manifest(package_key)
        if manifest and manifest.class_wrap_prefixes:
            _set_package_class_hints(package_key, manifest.class_wrap_prefixes)
        
        logger.debug(f"Manifest configuration synced for {package_name}")
    except Exception as e:
        logger.error(f"Failed to sync manifest configuration for {package_name}: {e}")
        raise

def refresh_lazy_manifests() -> None:
    """Refresh all lazy manifest caches."""
    try:
        refresh_manifest_cache()
        logger.info("Refreshed all lazy manifest caches")
    except Exception as e:
        logger.error(f"Failed to refresh lazy manifest caches: {e}")
        raise

# =============================================================================
# SECURITY & POLICY FUNCTIONS
# =============================================================================

def set_package_allow_list(package_name: str, allowed_packages: list[str]) -> None:
    """Set allow list for a package."""
    try:
        LazyInstallPolicy.set_allow_list(package_name, allowed_packages)
        logger.debug(f"Set allow list for {package_name}: {allowed_packages}")
    except Exception as e:
        logger.error(f"Failed to set allow list for {package_name}: {e}")
        raise

def set_package_deny_list(package_name: str, denied_packages: list[str]) -> None:
    """Set deny list for a package."""
    try:
        LazyInstallPolicy.set_deny_list(package_name, denied_packages)
        logger.debug(f"Set deny list for {package_name}: {denied_packages}")
    except Exception as e:
        logger.error(f"Failed to set deny list for {package_name}: {e}")
        raise

def add_to_package_allow_list(package_name: str, allowed_package: str) -> None:
    """Add single package to allow list."""
    try:
        LazyInstallPolicy.add_to_allow_list(package_name, allowed_package)
        logger.debug(f"Added {allowed_package} to allow list for {package_name}")
    except Exception as e:
        logger.error(f"Failed to add {allowed_package} to allow list for {package_name}: {e}")
        raise

def add_to_package_deny_list(package_name: str, denied_package: str) -> None:
    """Add single package to deny list."""
    try:
        LazyInstallPolicy.add_to_deny_list(package_name, denied_package)
        logger.debug(f"Added {denied_package} to deny list for {package_name}")
    except Exception as e:
        logger.error(f"Failed to add {denied_package} to deny list for {package_name}: {e}")
        raise

def set_package_index_url(package_name: str, index_url: str) -> None:
    """Set package index URL for a package."""
    try:
        LazyInstallPolicy.set_index_url(package_name, index_url)
        logger.debug(f"Set index URL for {package_name}: {index_url}")
    except Exception as e:
        logger.error(f"Failed to set index URL for {package_name}: {e}")
        raise

def set_package_extra_index_urls(package_name: str, extra_index_urls: list[str]) -> None:
    """Set extra index URLs for a package."""
    try:
        LazyInstallPolicy.set_extra_index_urls(package_name, extra_index_urls)
        logger.debug(f"Set extra index URLs for {package_name}: {extra_index_urls}")
    except Exception as e:
        logger.error(f"Failed to set extra index URLs for {package_name}: {e}")
        raise

def add_package_trusted_host(package_name: str, host: str) -> None:
    """Add trusted host for a package."""
    try:
        LazyInstallPolicy.add_trusted_host(package_name, host)
        logger.debug(f"Added trusted host {host} for {package_name}")
    except Exception as e:
        logger.error(f"Failed to add trusted host {host} for {package_name}: {e}")
        raise

def set_package_lockfile(package_name: str, lockfile_path: str) -> None:
    """Set lockfile path for a package."""
    try:
        LazyInstallPolicy.set_lockfile_path(package_name, lockfile_path)
        logger.debug(f"Set lockfile path for {package_name}: {lockfile_path}")
    except Exception as e:
        logger.error(f"Failed to set lockfile path for {package_name}: {e}")
        raise

def generate_package_sbom(package_name: str, output_path: Optional[str] = None) -> dict[str, Any]:
    """Generate SBOM for a package."""
    try:
        installer = LazyInstallerRegistry.get_instance(package_name)
        sbom = installer.generate_sbom()
        if output_path:
            installer.export_sbom(output_path)
        return sbom
    except Exception as e:
        logger.error(f"Failed to generate SBOM for {package_name}: {e}")
        return {
            "metadata": {
                "format": "xwlazy-sbom",
                "version": "1.0",
                "error": str(e)
            },
            "packages": []
        }

def check_externally_managed_environment(package_name: str = 'default') -> bool:
    """Check if environment is externally managed."""
    try:
        return _is_externally_managed()
    except Exception as e:
        logger.error(f"Failed to check externally managed environment: {e}")
        return False

def register_lazy_module_prefix(prefix: str) -> None:
    """Register a module prefix mapping."""
    try:
        _register_lazy_module_prefix(prefix)
        logger.debug(f"Registered lazy module prefix: {prefix}")
    except Exception as e:
        logger.error(f"Failed to register lazy module prefix {prefix}: {e}")
        raise

def register_lazy_module_methods(prefix: str, methods: tuple[str, ...]) -> None:
    """Register methods for a lazy module."""
    try:
        _register_lazy_module_methods(prefix, methods)
        logger.debug(f"Registered lazy module methods for prefix {prefix}: {methods}")
    except Exception as e:
        logger.error(f"Failed to register lazy module methods for {prefix}: {e}")
        raise

# =============================================================================
# MODULE REGISTRATION DOMAIN - Internal Utilities
# =============================================================================

# Note: Internal utility functions are available from hooks.finder module
# They are used internally by the lazy loading system and don't need facade wrappers

# =============================================================================
# KEYWORD-BASED DETECTION FUNCTIONS
# =============================================================================

def enable_keyword_detection(enabled: bool = True, keyword: Optional[str] = None, package_name: Optional[str] = None) -> None:
    """
    Enable keyword-based package detection.
    
    This is a global setting that applies to all packages. The package_name
    parameter is optional and used only for logging purposes.
    
    Args:
        enabled: Whether to enable keyword detection (default: True)
        keyword: Custom keyword to check (default: "xwlazy-enabled")
        package_name: Optional package name for logging purposes
    """
    try:
        _enable_keyword_detection(enabled, keyword)
        if package_name:
            logger.info(f"Keyword detection {'enabled' if enabled else 'disabled'} for {package_name}")
        else:
            logger.info(f"Keyword detection {'enabled' if enabled else 'disabled'}")
    except Exception as e:
        if package_name:
            logger.error(f"Failed to enable keyword detection for {package_name}: {e}")
        else:
            logger.error(f"Failed to enable keyword detection: {e}")
        raise

def is_keyword_detection_enabled(package_name: Optional[str] = None) -> bool:
    """
    Check if keyword detection is enabled.
    
    This checks a global setting that applies to all packages. The package_name
    parameter is optional and used only for logging purposes.
    
    Args:
        package_name: Optional package name for logging purposes
    
    Returns:
        True if keyword detection is enabled globally
    """
    try:
        return _is_keyword_detection_enabled()
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Error checking keyword detection status: {e}")
        return False
    except Exception as e:
        # Unexpected errors - log but return False for safety
        logger.warning(f"Unexpected error checking keyword detection status: {e}")
        return False

def get_keyword_detection_keyword(package_name: Optional[str] = None) -> Optional[str]:
    """
    Get keyword used for detection.
    
    This returns the global keyword setting. The package_name parameter is
    optional and used only for logging purposes.
    
    Args:
        package_name: Optional package name for logging purposes
    
    Returns:
        The keyword being checked for auto-detection
    """
    try:
        return _get_keyword_detection_keyword()
    except Exception as e:
        logger.error(f"Failed to get keyword detection keyword: {e}")
        return None

def check_package_keywords(package_name: Optional[str] = None, keywords: Optional[list[str]] = None) -> bool:
    """
    Check if a package (or any package) has the specified keyword in its metadata.
    
    Args:
        package_name: The package name to check (or None to check all packages)
        keywords: Optional list of keywords to check (uses first keyword if provided)
    
    Returns:
        True if the keyword is found in the package's metadata
    """
    try:
        keyword = keywords[0] if keywords else None
        return _check_package_keywords(package_name, keyword)
    except Exception as e:
        if package_name:
            logger.error(f"Failed to check package keywords for {package_name}: {e}")
        else:
            logger.error(f"Failed to check package keywords: {e}")
        return False

# =============================================================================
# DISCOVERY FUNCTIONS
# =============================================================================

def get_lazy_discovery(package_name: str = 'default') -> Optional[APackageHelper]:
    """Get discovery instance for a package."""
    try:
        return _get_lazy_discovery()
    except Exception as e:
        logger.error(f"Failed to get discovery instance for {package_name}: {e}")
        return None

def discover_dependencies(package_name: str = 'default') -> dict[str, str]:
    """Discover dependencies for a package."""
    try:
        discovery = _get_lazy_discovery()
        if discovery:
            return discovery.discover_all_dependencies()
    except Exception as e:
        logger.error(f"Failed to discover dependencies for {package_name}: {e}")
    return {}

def export_dependency_mappings(package_name: str = 'default', output_path: Optional[str] = None) -> None:
    """Export dependency mappings to file."""
    try:
        discovery = _get_lazy_discovery()
        if discovery:
            if output_path:
                discovery.export_to_json(output_path)
            else:
                # Default output path
                from pathlib import Path
                output_path = Path.cwd() / f"{package_name}_dependencies.json"
                discovery.export_to_json(str(output_path))
            logger.info(f"Dependency mappings exported for {package_name} to {output_path}")
        else:
            logger.warning(f"No discovery instance available for {package_name}")
    except Exception as e:
        logger.error(f"Failed to export dependency mappings for {package_name}: {e}")
        raise

# =============================================================================
# PUBLIC API EXPORTS
# =============================================================================

__all__ = [
    # Facade class
    'LazyModeFacade',
    # Facade functions
    'enable_lazy_mode',
    'disable_lazy_mode',
    'is_lazy_mode_enabled',
    'get_lazy_mode_stats',
    'configure_lazy_mode',
    'preload_modules',
    'optimize_lazy_mode',
    # One-line activation API
    'auto_enable_lazy',
    # Lazy-loader compatible API
    'attach',
    # Public API functions
    'enable_lazy_install',
    'disable_lazy_install',
    'is_lazy_install_enabled',
    'set_lazy_install_mode',
    'get_lazy_install_mode',
    'install_missing_package',
    'install_and_import',
    'get_lazy_install_stats',
    'get_all_lazy_install_stats',
    'lazy_import_with_install',
    'xwimport',
    # Hook functions
    'install_import_hook',
    'uninstall_import_hook',
    'is_import_hook_installed',
    # Lazy loading functions
    'enable_lazy_imports',
    'disable_lazy_imports',
    'is_lazy_import_enabled',
    'lazy_import',
    'register_lazy_module',
    'preload_module',
    'get_lazy_module',
    'get_loading_stats',
    'preload_frequently_used',
    'get_lazy_import_stats',
    # Configuration
    'config_package_lazy_install_enabled',
    'config_module_lazy_load_enabled',
    'sync_manifest_configuration',
    'refresh_lazy_manifests',
    # Security & Policy
    'set_package_allow_list',
    'set_package_deny_list',
    'add_to_package_allow_list',
    'add_to_package_deny_list',
    'set_package_index_url',
    'set_package_extra_index_urls',
    'add_package_trusted_host',
    'set_package_lockfile',
    'generate_package_sbom',
    'check_externally_managed_environment',
    'register_lazy_module_prefix',
    'register_lazy_module_methods',
    # Keyword-based detection
    'enable_keyword_detection',
    'is_keyword_detection_enabled',
    'get_keyword_detection_keyword',
    'check_package_keywords',
    # Discovery functions
    'get_lazy_discovery',
    'discover_dependencies',
    'export_dependency_mappings',
    # Helper classes
    'XWPackageHelper',
    'XWModuleHelper',
]

# =============================================================================
# CONCRETE HELPER IMPLEMENTATIONS (Simple API Pattern)
# =============================================================================

# XWPackageHelper moved to package/facade.py
# This is now just an alias (defined above)
# Removed duplicate class definition - use the one from package/facade.py
# XWModuleHelper moved to module/facade.py
# This is now just an alias (defined above)
# Removed duplicate class definition - use the one from module/facade.py

# Global helper instances
_package_helper = XWPackageHelper()
_module_helper = XWModuleHelper()
