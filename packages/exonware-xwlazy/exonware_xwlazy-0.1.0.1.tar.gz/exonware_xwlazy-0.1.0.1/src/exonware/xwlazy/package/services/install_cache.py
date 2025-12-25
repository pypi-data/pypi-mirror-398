"""
Installation Cache Mixin

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Mixin for cache management (wheels, install trees, known missing modules).
Uses shared utilities from common/services/install_cache_utils.
"""

import os
import time
from pathlib import Path
from typing import Optional
from collections import OrderedDict

# Import shared utilities
from ...common.services.install_cache_utils import (
    get_cache_dir,
    get_wheel_path,
    get_install_tree_dir,
    get_site_packages_dir,
    pip_install_from_path,
    ensure_cached_wheel,
    install_from_cached_tree as _install_from_cached_tree_util,
    materialize_cached_tree as _materialize_cached_tree_util,
    has_cached_install_tree as _has_cached_install_tree_util,
    install_from_cached_wheel as _install_from_cached_wheel_util,
)

# Lazy imports
def _get_spec_cache_clear():
    """Get spec_cache_clear function (lazy import to avoid circular dependency)."""
    from ...common.services.spec_cache import _spec_cache_clear
    return _spec_cache_clear

_spec_cache_clear = None

# Environment variables
_KNOWN_MISSING_CACHE_LIMIT = int(os.environ.get("XWLAZY_MISSING_CACHE_MAX", "128") or 128)
_KNOWN_MISSING_CACHE_TTL = float(os.environ.get("XWLAZY_MISSING_CACHE_TTL", "120") or 120.0)

def _ensure_spec_cache_initialized():
    """Ensure spec cache utilities are initialized."""
    global _spec_cache_clear
    if _spec_cache_clear is None:
        _spec_cache_clear = _get_spec_cache_clear()

class InstallCacheMixin:
    """Mixin for cache management (wheels, install trees, known missing modules)."""
    
    def _prune_known_missing(self) -> None:
        """Remove stale entries from the known-missing cache."""
        if not self._known_missing:  # type: ignore[attr-defined]
            return
        now = time.monotonic()
        with self._lock:  # type: ignore[attr-defined]
            while self._known_missing:  # type: ignore[attr-defined]
                _, ts = next(iter(self._known_missing.items()))  # type: ignore[attr-defined]
                if now - ts <= _KNOWN_MISSING_CACHE_TTL:
                    break
                self._known_missing.popitem(last=False)  # type: ignore[attr-defined]
    
    def _mark_module_missing(self, module_name: str) -> None:
        """Remember modules that failed to import recently."""
        _ensure_spec_cache_initialized()
        with self._lock:  # type: ignore[attr-defined]
            self._prune_known_missing()
            _spec_cache_clear(module_name)
            self._known_missing[module_name] = time.monotonic()  # type: ignore[attr-defined]
            while len(self._known_missing) > _KNOWN_MISSING_CACHE_LIMIT:  # type: ignore[attr-defined]
                self._known_missing.popitem(last=False)  # type: ignore[attr-defined]
    
    def _clear_module_missing(self, module_name: str) -> None:
        """Remove a module from the known-missing cache."""
        with self._lock:  # type: ignore[attr-defined]
            self._known_missing.pop(module_name, None)  # type: ignore[attr-defined]
    
    def is_module_known_missing(self, module_name: str) -> bool:
        """Return True if module recently failed to import."""
        self._prune_known_missing()
        with self._lock:  # type: ignore[attr-defined]
            return module_name in self._known_missing  # type: ignore[attr-defined]
    
    def _get_async_cache_dir(self) -> Path:
        """Get the async cache directory."""
        return get_cache_dir(self._async_cache_dir)  # type: ignore[attr-defined]
    
    def _cached_wheel_name(self, package_name: str) -> Path:
        """Get the cached wheel file path for a package."""
        return get_wheel_path(package_name, self._async_cache_dir)  # type: ignore[attr-defined]
    
    def _install_from_cached_wheel(self, package_name: str, policy_args: Optional[list[str]] = None) -> bool:
        """Install from a cached wheel file."""
        return _install_from_cached_wheel_util(
            package_name,
            policy_args,
            self._async_cache_dir  # type: ignore[attr-defined]
        )
    
    def _pip_install_from_path(self, wheel_path: Path, policy_args: Optional[list[str]] = None) -> bool:
        """Install a wheel file using pip."""
        return pip_install_from_path(wheel_path, policy_args)
    
    def _ensure_cached_wheel(self, package_name: str, policy_args: Optional[list[str]] = None) -> Optional[Path]:
        """Ensure a wheel is cached, downloading it if necessary."""
        return ensure_cached_wheel(
            package_name,
            policy_args,
            self._async_cache_dir  # type: ignore[attr-defined]
        )
    
    def _cached_install_dir(self, package_name: str) -> Path:
        """Get the cached install directory for a package."""
        return get_install_tree_dir(package_name, self._async_cache_dir)  # type: ignore[attr-defined]
    
    def _has_cached_install_tree(self, package_name: str) -> bool:
        """Check if a cached install tree exists."""
        return _has_cached_install_tree_util(
            package_name,
            self._async_cache_dir  # type: ignore[attr-defined]
        )
    
    def _site_packages_dir(self) -> Path:
        """Get the site-packages directory."""
        return get_site_packages_dir()
    
    def _install_from_cached_tree(self, package_name: str) -> bool:
        """Install from a cached install tree."""
        return _install_from_cached_tree_util(
            package_name,
            self._async_cache_dir  # type: ignore[attr-defined]
        )
    
    def _materialize_cached_tree(self, package_name: str, wheel_path: Path) -> None:
        """Materialize a cached install tree from a wheel file."""
        _materialize_cached_tree_util(
            package_name,
            wheel_path,
            self._async_cache_dir  # type: ignore[attr-defined]
        )

