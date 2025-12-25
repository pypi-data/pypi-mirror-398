"""
#exonware/xwlazy/src/exonware/xwlazy/__init__.py

xwlazy: Lazy loading and on-demand package installation for Python.

The xwlazy library provides automatic dependency installation and lazy loading
capabilities, allowing packages to declare optional dependencies that are
installed only when needed.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Generation Date: 10-Oct-2025

Main Features:
    - Automatic dependency discovery from pyproject.toml and requirements.txt
    - On-demand package installation via import hooks
    - Two-stage lazy loading for optimal performance
    - Per-package lazy mode configuration
    - Security policies and allow/deny lists
    - SBOM generation and lockfile management

Example:
    >>> from exonware.xwlazy import enable_lazy_mode, xwimport
    >>> 
    >>> # Enable lazy mode for your package
    >>> enable_lazy_mode(package_name="my_package", lazy_install_mode="smart")
    >>> 
    >>> # Import with automatic installation
    >>> pandas = xwimport("pandas")  # Installs pandas if not available
"""

# =============================================================================
# VERSION
# =============================================================================

from .version import (
    __version__,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
    VERSION_BUILD,
    VERSION_SUFFIX,
    VERSION_STRING,
    get_version,
    get_version_info,
    get_version_dict,
    is_dev_version,
    is_release_version,
)

# =============================================================================
# IMPORTS - Standard Python Imports (No Defensive Code!)
# =============================================================================

# Import from facade - provides unified public API
from .facade import (
    # Facade functions
    enable_lazy_mode,
    disable_lazy_mode,
    is_lazy_mode_enabled,
    get_lazy_mode_stats,
    configure_lazy_mode,
    preload_modules,
    optimize_lazy_mode,
    # One-line activation API
    auto_enable_lazy,
    # Lazy-loader compatible API
    attach,
    # Public API functions
    enable_lazy_install,
    disable_lazy_install,
    is_lazy_install_enabled,
    set_lazy_install_mode,
    get_lazy_install_mode,
    install_missing_package,
    install_and_import,
    get_lazy_install_stats,
    get_all_lazy_install_stats,
    lazy_import_with_install,
    xwimport,
    # Hook functions
    install_import_hook,
    uninstall_import_hook,
    is_import_hook_installed,
    # Lazy loading functions
    enable_lazy_imports,
    disable_lazy_imports,
    is_lazy_import_enabled,
    lazy_import,
    register_lazy_module,
    preload_module,
    get_lazy_module,
    get_loading_stats,
    preload_frequently_used,
    get_lazy_import_stats,
    # Configuration
    config_package_lazy_install_enabled,
    config_module_lazy_load_enabled,
    sync_manifest_configuration,
    refresh_lazy_manifests,
    # Security & Policy
    set_package_allow_list,
    set_package_deny_list,
    add_to_package_allow_list,
    add_to_package_deny_list,
    set_package_index_url,
    set_package_extra_index_urls,
    add_package_trusted_host,
    set_package_lockfile,
    generate_package_sbom,
    check_externally_managed_environment,
    register_lazy_module_prefix,
    register_lazy_module_methods,
    # Keyword-based detection
    enable_keyword_detection,
    is_keyword_detection_enabled,
    get_keyword_detection_keyword,
    check_package_keywords,
    # Discovery functions
    get_lazy_discovery,
    discover_dependencies,
    export_dependency_mappings,
)

# Import contracts and base for advanced usage
from .defs import PRESET_MODES, get_preset_mode
from .defs import (
    LazyLoadMode,
    LazyInstallMode,
    PathType,
    DependencyInfo,
    LazyModeConfig,
)
from .contracts import (
    IPackageHelper,
    IModuleHelper,
    IRuntime,
)

# Import errors
from .errors import (
    LazySystemError,
    LazyInstallError,
    LazyDiscoveryError,
    LazyHookError,
    LazySecurityError,
    ExternallyManagedError,
    DeferredImportError,
)

# Import config
from .config import LazyConfig, DEFAULT_LAZY_CONFIG

# Import abstract base classes directly from submodules
from .package.base import APackageHelper
from .module.base import AModuleHelper
from .runtime.base import ARuntimeHelper

# Import concrete implementations (lazy to prevent circular imports)
from typing import Any

def __getattr__(name: str) -> Any:
    """Lazy import for concrete facades to prevent circular dependencies."""
    if name == "XWPackageHelper":
        from .package import XWPackageHelper
        return XWPackageHelper
    elif name == "XWModuleHelper":
        from .module import XWModuleHelper
        return XWModuleHelper
    elif name == "XWRuntimeHelper":
        from .runtime import XWRuntimeHelper
        return XWRuntimeHelper
    elif name == "manifest":
        # Import manifest module for lazy access
        from .package.services import manifest
        return manifest
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# Import core classes for advanced usage
from .package.services.config_manager import LazyInstallConfig
from .package.services import LazyInstallerRegistry, AsyncInstallHandle, LazyInstaller
from .common.services.dependency_mapper import DependencyMapper
from .module.importer_engine import (
    LazyMetaPathFinder,
    WatchedPrefixRegistry,
    LazyLoader,
)
from .package.services.manifest import LazyManifestLoader, PackageManifest
from .facade import _lazy_importer

# Import internal utilities (for advanced usage)
from .common.services import (
    check_package_keywords,
    _detect_lazy_installation,
    _detect_meta_info_mode,
)
from .module.importer_engine import (
    _set_package_class_hints,
    _get_package_class_hints,
    _clear_all_package_class_hints,
    _spec_for_existing_module,
)
from .common.services.spec_cache import (
    _cached_stdlib_check,
    _spec_cache_get,
    _spec_cache_put,
    _spec_cache_clear,
    _cache_spec_if_missing,
    _spec_cache_prune_locked,
)
from .package.services import (
    is_externally_managed as _is_externally_managed,
    check_pip_audit_available as _check_pip_audit_available,
)
from .module.importer_engine import (
    _is_import_in_progress,
    _mark_import_started,
    _mark_import_finished,
    _lazy_aware_import_module,
    # _patch_import_module removed - deprecated, use sys.meta_path hooks instead
    _unpatch_import_module,
)

# Version info
__author__ = 'Eng. Muhammad AlShehri'
__email__ = 'connect@exonware.com'
__company__ = 'eXonware.com'

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Version
    "__version__",
    "VERSION_MAJOR",
    "VERSION_MINOR",
    "VERSION_PATCH",
    "VERSION_BUILD",
    "VERSION_SUFFIX",
    "VERSION_STRING",
    "get_version",
    "get_version_info",
    "get_version_dict",
    "is_dev_version",
    "is_release_version",
    # Facade functions
    "enable_lazy_mode",
    "disable_lazy_mode",
    "is_lazy_mode_enabled",
    "get_lazy_mode_stats",
    "configure_lazy_mode",
    "preload_modules",
    "optimize_lazy_mode",
    # One-line activation API
    "auto_enable_lazy",
    # Lazy-loader compatible API
    "attach",
    # Public API functions
    "enable_lazy_install",
    "disable_lazy_install",
    "is_lazy_install_enabled",
    "set_lazy_install_mode",
    "get_lazy_install_mode",
    "install_missing_package",
    "install_and_import",
    "get_lazy_install_stats",
    "get_all_lazy_install_stats",
    "lazy_import_with_install",
    "xwimport",
    # Hook functions
    "install_import_hook",
    "uninstall_import_hook",
    "is_import_hook_installed",
    # Lazy loading functions
    "enable_lazy_imports",
    "disable_lazy_imports",
    "is_lazy_import_enabled",
    "lazy_import",
    "register_lazy_module",
    "preload_module",
    "get_lazy_module",
    "get_loading_stats",
    "preload_frequently_used",
    "get_lazy_import_stats",
    # Configuration
    "config_package_lazy_install_enabled",
    "sync_manifest_configuration",
    "refresh_lazy_manifests",
    # Security & Policy
    "set_package_allow_list",
    "set_package_deny_list",
    "add_to_package_allow_list",
    "add_to_package_deny_list",
    "set_package_index_url",
    "set_package_extra_index_urls",
    "add_package_trusted_host",
    "set_package_lockfile",
    "generate_package_sbom",
    "check_externally_managed_environment",
    "register_lazy_module_prefix",
    "register_lazy_module_methods",
    # Keyword-based detection
    "enable_keyword_detection",
    "is_keyword_detection_enabled",
    "get_keyword_detection_keyword",
    "check_package_keywords",
    # Discovery functions
    "get_lazy_discovery",
    "discover_dependencies",
    "export_dependency_mappings",
    # Contracts
    "LazyLoadMode",
    "LazyInstallMode",
    "PathType",
    "DependencyInfo",
    "LazyModeConfig",
    "PRESET_MODES",
    "get_preset_mode",
    "IPackageHelper",
    "IModuleHelper",
    "IRuntime",
    # Abstract base classes
    "APackageHelper",
    "AModuleHelper",
    "ARuntimeHelper",
    # Concrete implementations
    "XWPackageHelper",
    "XWModuleHelper",
    "XWRuntimeHelper",
    # Errors
    "LazySystemError",
    "LazyInstallError",
    "LazyDiscoveryError",
    "LazyHookError",
    "LazySecurityError",
    "ExternallyManagedError",
    "DeferredImportError",
    # Config
    "LazyConfig",
    "DEFAULT_LAZY_CONFIG",
    # Core classes (for advanced usage)
    "LazyInstallConfig",
    "LazyInstallerRegistry",
    "AsyncInstallHandle",
    "LazyInstaller",
    "DependencyMapper",
    "LazyMetaPathFinder",
    "WatchedPrefixRegistry",
    "LazyLoader",
    "LazyManifestLoader",
    "PackageManifest",
    "manifest",
    "_lazy_importer",
    # Internal utilities (for advanced usage)
    "check_package_keywords",
    "_detect_lazy_installation",
    "_detect_meta_info_mode",
    "_set_package_class_hints",
    "_get_package_class_hints",
    "_clear_all_package_class_hints",
    "_spec_for_existing_module",
    "_cached_stdlib_check",
    "_spec_cache_get",
    "_spec_cache_put",
    "_spec_cache_clear",
    "_cache_spec_if_missing",
    "_spec_cache_prune_locked",
    "_is_externally_managed",
    "_check_pip_audit_available",
    "_is_import_in_progress",
    "_mark_import_started",
    "_mark_import_finished",
    "_lazy_aware_import_module",
    # "_patch_import_module",  # Removed - deprecated, use sys.meta_path hooks instead
    "_unpatch_import_module",
]

