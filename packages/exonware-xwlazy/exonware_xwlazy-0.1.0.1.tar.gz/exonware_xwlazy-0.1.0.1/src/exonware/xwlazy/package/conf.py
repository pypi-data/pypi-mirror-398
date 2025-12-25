"""
#exonware/xwlazy/src/exonware/xwlazy/package/conf.py

Host-facing configuration helpers for enabling lazy mode via `exonware.conf`.

This module centralizes the legacy configuration surface so host packages no
longer need to ship their own lazy bootstrap logic.  Consumers import
``exonware.conf`` as before, while the real implementation now lives in
``xwlazy.package.conf`` to keep lazy concerns within the xwlazy project.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025
"""

from __future__ import annotations

import importlib
import importlib.metadata
import subprocess
import sys
import types
import warnings
from typing import Any, Optional

# Import from new structure
from .services.host_packages import refresh_host_package
from ..facade import (
    config_package_lazy_install_enabled,
    install_import_hook,
    uninstall_import_hook,
    is_import_hook_installed,
    is_lazy_install_enabled,
)
from ..defs import get_preset_mode
from .services.config_manager import LazyInstallConfig

__all__ = ['get_conf_module', '_PackageConfig', '_FilteredStderr', '_LazyConfModule', '_setup_global_warning_filter']

class _PackageConfig:
    """Per-package configuration wrapper."""

    def __init__(self, package_name: str, parent_conf: "_LazyConfModule"):
        self._package_name = package_name
        self._parent_conf = parent_conf

    @property
    def lazy_install(self) -> bool:
        """Return lazy install status for this package."""
        return is_lazy_install_enabled(self._package_name)

    @lazy_install.setter
    def lazy_install(self, value: bool) -> None:
        """Enable/disable lazy mode for this package."""
        if value:
            # Default to "smart" mode when enabling lazy install
            # config_package_lazy_install_enabled will register package and install global hook
            config_package_lazy_install_enabled(self._package_name, True, mode="smart", install_hook=True)
            refresh_host_package(self._package_name)
        else:
            config_package_lazy_install_enabled(self._package_name, False, install_hook=False)
            uninstall_import_hook(self._package_name)

    def lazy_install_status(self) -> dict[str, Any]:
        """Return runtime status for this package."""
        return {
            "package": self._package_name,
            "enabled": is_lazy_install_enabled(self._package_name),
            "hook_installed": is_import_hook_installed(self._package_name),
            "active": is_lazy_install_enabled(self._package_name)
            and is_import_hook_installed(self._package_name),
        }

    def is_lazy_active(self) -> bool:
        """Return True if lazy install + hook are active."""
        return self.lazy_install_status()["active"]

class _FilteredStderr:
    """Stderr wrapper that filters out specific warning messages."""
    
    def __init__(self, original_stderr: Any, filter_patterns: list[str]):
        self._original = original_stderr
        self._filter_patterns = filter_patterns
    
    def write(self, text: str) -> int:
        """Write to stderr, filtering out unwanted warnings."""
        # Case-insensitive matching to catch all variations
        if any(pattern.lower() in text.lower() for pattern in self._filter_patterns):
            return len(text)  # Pretend we wrote it, but don't actually write
        return self._original.write(text)
    
    def flush(self) -> None:
        """Flush the original stderr."""
        self._original.flush()
    
    def reconfigure(self, *args, **kwargs):
        """Handle reconfigure calls - update original reference and reapply filter."""
        result = self._original.reconfigure(*args, **kwargs)
        # Ensure filter stays active
        if sys.stderr is not self:
            sys.stderr = self  # type: ignore[assignment]
        return result
    
    def __getattr__(self, name: str):
        """Delegate all other attributes to original stderr."""
        return getattr(self._original, name)

class _LazyConfModule(types.ModuleType):
    """Configuration module for all exonware packages."""

    def __init__(self, name: str, doc: Optional[str]) -> None:
        super().__init__(name, doc)
        self._package_configs: dict[str, _PackageConfig] = {}
        self._suppress_warnings: bool = True  # Default: suppress warnings
        self._original_stderr: Optional[Any] = None
        self._filtered_stderr: Optional[_FilteredStderr] = None
        # Set up warning suppression by default
        self._setup_warning_filter()

    # ------------------------------------------------------------------ helpers
    def _is_xwlazy_installed(self) -> bool:
        try:
            importlib.metadata.distribution("exonware-xwlazy")
            return True
        except importlib.metadata.PackageNotFoundError:
            try:
                importlib.metadata.distribution("xwlazy")
                return True
            except importlib.metadata.PackageNotFoundError:
                return False
        except Exception:
            try:
                import exonware.xwlazy  # noqa: F401
                return True
            except ImportError:
                return False

    def _ensure_xwlazy_installed(self) -> None:
        if self._is_xwlazy_installed():
            return
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "exonware-xwlazy"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                print("[OK] Installed exonware-xwlazy for lazy mode")
            else:
                print(f"[WARN] Failed to install exonware-xwlazy: {result.stderr}")
        except Exception as exc:  # pragma: no cover - best effort
            print(f"[WARN] Could not install exonware-xwlazy: {exc}")

    def _uninstall_xwlazy(self) -> None:
        if not self._is_xwlazy_installed():
            return
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "exonware-xwlazy", "xwlazy"],
                capture_output=True,
                text=True,
                check=False,
            )
            print("[OK] Uninstalled exonware-xwlazy (lazy mode disabled)")
        except Exception as exc:  # pragma: no cover
            print(f"[WARN] Could not uninstall exonware-xwlazy: {exc}")

    def _get_global_lazy_status(self) -> dict[str, Any]:
        """Return aggregate status for DX tooling."""
        installed = self._is_xwlazy_installed()
        # Check all known packages, not just those in _package_configs
        # This ensures we catch hooks installed via register_host_package
        known_packages = list(self._package_configs.keys())
        # Also check common package names that might have hooks installed
        for pkg_name in ("xwsystem", "xwnode", "xwdata", "xwschema", "xwaction", "xwentity"):
            if pkg_name not in known_packages and is_import_hook_installed(pkg_name):
                known_packages.append(pkg_name)
        
        hook_installed = any(is_import_hook_installed(pkg) for pkg in known_packages)
        # Check if any package has lazy active (including those not yet in _package_configs)
        active_configs = any(cfg.is_lazy_active() for cfg in self._package_configs.values())
        # Also check directly for packages with hooks and enabled lazy install
        active_direct = any(
            is_import_hook_installed(pkg) and is_lazy_install_enabled(pkg)
            for pkg in known_packages
        )
        
        return {
            "xwlazy_installed": installed,
            "enabled": installed,
            "hook_installed": hook_installed,
            "active": active_configs or active_direct,
        }
    
    def _setup_warning_filter(self) -> None:
        """Set up or remove the stderr warning filter based on current setting."""
        global _ORIGINAL_STDERR, _FILTERED_STDERR
        if self._suppress_warnings:
            # Use global filter (already set up at module import)
            if _FILTERED_STDERR is not None and sys.stderr is not _FILTERED_STDERR:
                sys.stderr = _FILTERED_STDERR  # type: ignore[assignment]
        else:
            # Restore original stderr if we were filtering
            if _ORIGINAL_STDERR is not None and sys.stderr is _FILTERED_STDERR:
                sys.stderr = _ORIGINAL_STDERR

    # ---------------------------------------------------------------- attr API
    def __getattr__(self, name: str):
        package_names = ("xwsystem", "xwnode", "xwdata", "xwschema", "xwaction", "xwentity")
        if name in package_names:
            if name not in self._package_configs:
                self._package_configs[name] = _PackageConfig(name, self)
            return self._package_configs[name]

        if name == "lazy_install":
            return self._is_xwlazy_installed()
        if name == "lazy":
            # Return current lazy mode setting
            # Check if any package has lazy enabled and return its mode
            for pkg_name in package_names:
                if is_lazy_install_enabled(pkg_name):
                    mode_config = LazyInstallConfig.get_mode_config(pkg_name)
                    if mode_config:
                        # Return preset name if matches, otherwise return mode string
                        from ..defs import PRESET_MODES
                        for preset_name, preset_config in PRESET_MODES.items():
                            if (preset_config.load_mode == mode_config.load_mode and 
                                preset_config.install_mode == mode_config.install_mode):
                                return preset_name
                    return LazyInstallConfig.get_mode(pkg_name)
            return "none"
        if name == "lazy_install_status":
            return self._get_global_lazy_status
        if name == "is_lazy_active":
            return any(cfg.is_lazy_active() for cfg in self._package_configs.values())
        if name == "suppress_warnings":
            return self._suppress_warnings

        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        if name == "lazy_install":
            if value:
                self._ensure_xwlazy_installed()
                # Enable with "smart" mode by default
                package_names = ("xwsystem", "xwnode", "xwdata", "xwschema", "xwaction", "xwentity")
                for pkg_name in package_names:
                    config_package_lazy_install_enabled(pkg_name, True, mode="smart", install_hook=True)
            else:
                package_names = ("xwsystem", "xwnode", "xwdata", "xwschema", "xwaction", "xwentity")
                for pkg_name in package_names:
                    config_package_lazy_install_enabled(pkg_name, False, install_hook=False)
                    uninstall_import_hook(pkg_name)
                self._uninstall_xwlazy()
            return
        if name == "lazy":
            # Support exonware.conf.lazy = "lite"/"smart"/"full"/"clean"/"auto"
            mode_map = {
                "lite": "lite",
                "smart": "smart", 
                "full": "full",
                "clean": "clean",
                "auto": "auto",
                "temporary": "temporary",
                "size_aware": "size_aware",
                "none": "none",
            }
            mode = mode_map.get(str(value).lower(), "smart")  # Default to "smart" instead of "auto"
            # Apply to all known packages
            package_names = ("xwsystem", "xwnode", "xwdata", "xwschema", "xwaction", "xwentity")
            for pkg_name in package_names:
                config_package_lazy_install_enabled(pkg_name, True, mode, install_hook=True)
            return
        if name == "suppress_warnings":
            self._suppress_warnings = bool(value)
            self._setup_warning_filter()
            return
        super().__setattr__(name, value)

_CONF_INSTANCE: Optional[_LazyConfModule] = None
_ORIGINAL_STDERR: Optional[Any] = None
_FILTERED_STDERR: Optional[_FilteredStderr] = None

def _setup_global_warning_filter() -> None:
    """Set up global stderr filter for decimal module warnings (called at module import)."""
    global _ORIGINAL_STDERR, _FILTERED_STDERR
    # Check if a filter is already active (e.g., from exonware/__init__.py or conf.py)
    # Check for both our filter class and the early filter class
    if (hasattr(sys.stderr, '_original') or 
        isinstance(sys.stderr, _FilteredStderr) or
        type(sys.stderr).__name__ == '_EarlyStderrFilter'):
        # Filter already active, use existing one
        _FILTERED_STDERR = sys.stderr  # type: ignore[assignment]
        return
    if _ORIGINAL_STDERR is None:
        # If stderr has _original, it's already wrapped - use that as original
        if hasattr(sys.stderr, '_original'):
            _ORIGINAL_STDERR = sys.stderr._original
        else:
            _ORIGINAL_STDERR = sys.stderr
    if _FILTERED_STDERR is None:
        _FILTERED_STDERR = _FilteredStderr(
            _ORIGINAL_STDERR,
            ["mpd_setminalloc", "MPD_MINALLOC", "ignoring request to set", "libmpdec", "context.c:57"]
        )
    if sys.stderr is not _FILTERED_STDERR:
        sys.stderr = _FILTERED_STDERR  # type: ignore[assignment]

# Set up warning filter immediately when module is imported (default: suppress warnings)
# Note: conf.py may have already set up a filter, which is fine
_setup_global_warning_filter()

def get_conf_module(name: str = "exonware.conf", doc: Optional[str] = None) -> types.ModuleType:
    """Return (and memoize) the shared conf module instance."""
    global _CONF_INSTANCE
    if _CONF_INSTANCE is None:
        _CONF_INSTANCE = _LazyConfModule(name, doc)
    return _CONF_INSTANCE
