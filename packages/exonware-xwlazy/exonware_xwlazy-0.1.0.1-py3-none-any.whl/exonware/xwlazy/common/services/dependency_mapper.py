"""
Dependency Mapper for package discovery.

This module contains DependencyMapper class extracted from lazy_core.py Section 1.
"""

import threading
from typing import Optional

# Lazy import to avoid circular dependency
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.discovery")

logger = None  # Will be initialized on first use

# Import from spec_cache (same directory)
from .spec_cache import (
    _cached_stdlib_check,
    _spec_cache_get,
    _cache_spec_if_missing,
    get_stdlib_module_set,
)

_STDLIB_MODULE_SET = get_stdlib_module_set()

# Import from manifest (package/services - avoid circular import)
def get_manifest_loader():
    """Get manifest loader (lazy import to avoid circular dependency)."""
    from ...package.services.manifest import get_manifest_loader as _get_manifest_loader
    return _get_manifest_loader()

# Import from discovery (package/services - avoid circular import)
def get_lazy_discovery():
    """Get discovery instance."""
    from ...package.services.discovery import get_lazy_discovery as _get_lazy_discovery
    return _get_lazy_discovery()

class DependencyMapper:
    """
    Maps import names to package names using dynamic discovery.
    Optimized with caching to avoid repeated file I/O.
    """
    
    __slots__ = (
        '_discovery',
        '_package_import_mapping',
        '_import_package_mapping',
        '_cached',
        '_lock',
        '_package_name',
        '_manifest_generation',
        '_manifest_dependencies',
        '_manifest_signature',
        '_manifest_empty',
    )
    
    def __init__(self, package_name: str = 'default'):
        """Initialize dependency mapper."""
        self._discovery = None  # Lazy init to avoid circular imports
        self._package_import_mapping: dict[str, list[str]] = {}
        self._import_package_mapping: dict[str, str] = {}
        self._cached = False
        self._lock = threading.RLock()
        self._package_name = package_name
        self._manifest_generation = -1
        self._manifest_dependencies: dict[str, str] = {}
        self._manifest_signature: Optional[tuple[str, float, float]] = None
        self._manifest_empty = False

    def set_package_name(self, package_name: str) -> None:
        """Update the owning package name (affects manifest lookups)."""
        normalized = (package_name or 'default').strip().lower() or 'default'
        if normalized != self._package_name:
            self._package_name = normalized
            self._manifest_generation = -1
            self._manifest_dependencies = {}
    
    def _get_discovery(self):
        """Get discovery instance (lazy init)."""
        if self._discovery is None:
            self._discovery = get_lazy_discovery()
        return self._discovery
    
    def _ensure_mappings_cached(self) -> None:
        """Ensure mappings are cached (lazy initialization)."""
        if self._cached:
            return
        
        with self._lock:
            if self._cached:
                return
            
            discovery = self._get_discovery()
            self._package_import_mapping = discovery.get_package_import_mapping()
            self._import_package_mapping = discovery.get_import_package_mapping()
            self._cached = True
    
    def _ensure_manifest_cached(self, loader=None) -> None:
        if loader is None:
            loader = get_manifest_loader()
        signature = loader.get_manifest_signature(self._package_name)
        if signature == self._manifest_signature and (self._manifest_dependencies or self._manifest_empty):
            return
        
        shared = loader.get_shared_dependencies(self._package_name, signature)
        if shared is not None:
            self._manifest_generation = loader.generation
            self._manifest_signature = signature
            self._manifest_dependencies = shared
            self._manifest_empty = len(shared) == 0
            return

        manifest = loader.get_manifest(self._package_name)
        current_generation = loader.generation

        dependencies: dict[str, str] = {}
        manifest_empty = True
        if manifest and manifest.dependencies:
            dependencies = {
                key.lower(): value
                for key, value in manifest.dependencies.items()
                if key and value
            }
            manifest_empty = False

        self._manifest_generation = current_generation
        self._manifest_signature = signature
        self._manifest_dependencies = dependencies
        self._manifest_empty = manifest_empty
    
    @staticmethod
    def _is_stdlib_or_builtin(module_name: str) -> bool:
        """Return True if the module is built-in or part of the stdlib."""
        root = module_name.split('.', 1)[0]
        needs_cache = False
        if module_name in _STDLIB_MODULE_SET or root in _STDLIB_MODULE_SET:
            return True
        if _cached_stdlib_check(module_name):
            needs_cache = True
        if needs_cache:
            _cache_spec_if_missing(module_name)
        return needs_cache

    DENY_LIST: set[str] = {
        # POSIX-only modules that don't exist on Windows but try to auto-install
        "pwd",
        "grp",
        "spwd",
        "nis",
        "termios",
        "tty",
        "pty",
        "fcntl",
        # Windows-only internals
        "winreg",
        "winsound",
        "_winapi",
        "_dbm",
        # Internal optional modules that must never trigger auto-install
        "compression",
        "socks",
        "wimlib",
        # Optional dependencies with Python 2 compatibility shims (Python 3.8+ only)
        "inspect2",  # Python 2 compatibility shim, not needed on Python 3.8+
        "rich",      # Optional CLI enhancement for httpx, not required for core functionality
    }

    def _should_skip_auto_install(self, import_name: str) -> bool:
        """Determine whether an import should bypass lazy installation."""
        global logger
        if logger is None:
            logger = _get_logger()
        
        if self._is_stdlib_or_builtin(import_name):
            logger.debug("Skipping lazy install for stdlib module '%s'", import_name)
            return True

        if import_name in self.DENY_LIST:
            logger.debug("Skipping lazy install for denied module '%s'", import_name)
            return True

        return False

    def get_package_name(self, import_name: str) -> Optional[str]:
        """
        Get package name from import name.
        
        Priority order (manifest takes precedence):
        1. Skip checks (stdlib, deny list)
        2. Manifest dependencies (explicit user configuration - highest priority)
        3. Spec cache (module already exists - skip auto-install)
        4. Discovery mappings (automatic discovery from project configs)
        5. Common mappings (quick access list - works without project configs)
        6. Fallback to import_name itself
        """
        if self._should_skip_auto_install(import_name):
            return None
        
        # Check manifest FIRST - explicit user configuration takes precedence
        loader = get_manifest_loader()
        generation_changed = self._manifest_generation != loader.generation
        manifest_uninitialized = not self._manifest_dependencies and not self._manifest_empty
        if generation_changed or manifest_uninitialized:
            self._ensure_manifest_cached(loader)
        manifest_hit = self._manifest_dependencies.get(import_name.lower())
        if manifest_hit:
            return manifest_hit
        
        # Check common mappings BEFORE spec cache (common mappings are reliable)
        # This is important for exonware projects to work immediately
        # Common mappings take precedence over spec cache because spec cache can be stale
        discovery = self._get_discovery()
        common_mappings = getattr(discovery, 'COMMON_MAPPINGS', {})
        common_hit = common_mappings.get(import_name)
        if common_hit:
            return common_hit
        
        # Check spec cache - if module already exists AND we don't have a common mapping, skip auto-install
        # Note: We check this AFTER common mappings because spec cache can be stale after uninstallation
        if _spec_cache_get(import_name):
            return None

        # Try discovery mappings (from project configs)
        self._ensure_mappings_cached()
        discovery_hit = self._import_package_mapping.get(import_name)
        if discovery_hit:
            return discovery_hit
        
        # Fallback: assume import name matches package name
        return import_name
    
    def get_import_names(self, package_name: str) -> list[str]:
        """Get all possible import names for a package."""
        self._ensure_mappings_cached()
        return self._package_import_mapping.get(package_name, [package_name])
    
    def get_package_import_mapping(self) -> dict[str, list[str]]:
        """Get complete package to import names mapping."""
        self._ensure_mappings_cached()
        return self._package_import_mapping.copy()
    
    def get_import_package_mapping(self) -> dict[str, str]:
        """Get complete import to package name mapping."""
        self._ensure_mappings_cached()
        return self._import_package_mapping.copy()

__all__ = ['DependencyMapper']

