"""
#exonware/xwlazy/src/exonware/xwlazy/config.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

Configuration for Lazy Loading System

This module defines configuration classes for the lazy loading system
following GUIDE_ARCH.md structure.
"""

from __future__ import annotations

from typing import Optional, Any

# Import LazyConfig dataclass from defs.py
from .defs import LazyConfig as _LazyConfigBase

# Extend LazyConfig with methods (dataclass is in defs.py)
class LazyConfig(_LazyConfigBase):
    """Bridge configuration settings with the lazy package implementation."""
    
    def __post_init__(self) -> None:
        """Normalize package names."""
        super().__post_init__()

    # High-level API -----------------------------------------------------
    @property
    def lazy_import(self) -> bool:
        """Return whether lazy mode is currently active."""
        # Import from facade
        from .facade import is_lazy_mode_enabled
        return is_lazy_mode_enabled()

    @lazy_import.setter
    def lazy_import(self, value: bool) -> None:
        self.set_lazy_import(bool(value))

    def set_lazy_import(
        self,
        enabled: bool,
        *,
        lazy_imports: bool = True,
        lazy_install: bool = True,
        install_hook: bool = True,
        mode: str = "auto",
    ) -> None:
        """
        Toggle lazy mode with optional fine-grained controls.
        
        Includes re-hooking support: If lazy is enabled and install_hook is True,
        ensures the import hook is installed even if it wasn't installed initially.
        """
        # Import from facade
        from .facade import (
            config_package_lazy_install_enabled,
            disable_lazy_mode,
            enable_lazy_mode,
            is_import_hook_installed,
            install_import_hook,
        )
        
        if enabled:
            self._configure_packages(True, mode=mode, install_hook=install_hook)
            enable_lazy_mode(
                package_name=self.packages[0],
                enable_lazy_imports=lazy_imports,
                enable_lazy_install=lazy_install,
                install_hook=install_hook,
                lazy_install_mode=mode,
            )
            # Re-hook: Install hook if lazy is enabled and hook not already installed
            # Root cause: Hook not installed when lazy enabled after package load
            # Priority impact: Usability (#2) - Users expect lazy to work when enabled
            if install_hook:
                self._ensure_hook_installed()
        else:
            disable_lazy_mode()
            self._configure_packages(False, install_hook=False)

    def enable(
        self,
        *,
        lazy_imports: bool = True,
        lazy_install: bool = True,
        install_hook: bool = True,
        mode: str = "auto",
    ) -> None:
        """Enable lazy mode using the provided options."""
        self.set_lazy_import(
            True,
            lazy_imports=lazy_imports,
            lazy_install=lazy_install,
            install_hook=install_hook,
            mode=mode,
        )

    def disable(self) -> None:
        """Disable lazy mode entirely."""
        self.set_lazy_import(False)

    # DX: Status check methods -------------------------------------------
    def get_lazy_status(self) -> dict:
        """
        Get detailed lazy installation status (DX enhancement).
        
        Returns:
            Dictionary with lazy mode status information
        """
        # Import from facade
        from .facade import (
            is_import_hook_installed,
            is_lazy_install_enabled,
        )
        
        try:
            primary_package = self.packages[0] if self.packages else "default"
            return {
                'enabled': self.lazy_import,
                'hook_installed': is_import_hook_installed(primary_package),
                'lazy_install_enabled': is_lazy_install_enabled(primary_package),
                'active': self.lazy_import and is_import_hook_installed(primary_package)
            }
        except Exception:
            return {
                'enabled': self.lazy_import,
                'hook_installed': False,
                'lazy_install_enabled': False,
                'active': False,
                'error': 'Could not check hook status'
            }
    
    def is_lazy_active(self) -> bool:
        """
        Check if lazy mode is active (DX enhancement).
        
        Returns:
            True if lazy mode is enabled and hook is installed
        """
        # Import from facade
        from .facade import is_import_hook_installed
        
        try:
            primary_package = self.packages[0] if self.packages else "default"
            return self.lazy_import and is_import_hook_installed(primary_package)
        except Exception:
            return False

    # Internal helpers ---------------------------------------------------
    def _configure_packages(
        self,
        enabled: bool,
        *,
        mode: str = "auto",
        install_hook: bool = True,
    ) -> None:
        # Import from facade
        from .facade import config_package_lazy_install_enabled
        
        for package in self.packages:
            config_package_lazy_install_enabled(
                package,
                enabled,
                mode,
                install_hook=install_hook,
            )
    
    def _ensure_hook_installed(self) -> None:
        """
        Ensure import hook is installed for primary package.
        
        Re-hooking support: Install hook if not already installed.
        """
        # Import from facade
        from .facade import (
            is_import_hook_installed,
            install_import_hook,
        )
        
        try:
            primary_package = self.packages[0] if self.packages else "default"
            if not is_import_hook_installed(primary_package):
                install_import_hook(primary_package)
        except Exception:
            # Fail silently - hook installation failure shouldn't break package
            pass

DEFAULT_LAZY_CONFIG = LazyConfig()

