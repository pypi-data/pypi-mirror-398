"""
Configuration management for lazy loading system.

This module contains LazyInstallConfig which manages per-package lazy installation
configuration. Extracted from lazy_core.py Section 5.
"""

from typing import Optional
from ...common.services import LazyStateManager
from ...defs import LazyLoadMode, LazyInstallMode, LazyModeConfig
from ...defs import get_preset_mode

# Lazy import to avoid circular dependency
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.config")

def _get_log_event():
    """Get log_event function (lazy import to avoid circular dependency)."""
    from ...common.logger import log_event
    return log_event

logger = None  # Will be initialized on first use
_log = None  # Will be initialized on first use

# Mode enum mapping - extracted from lazy_core.py
_MODE_ENUM_MAP = {
    # Core v1.0 modes
    "none": LazyInstallMode.NONE,
    "smart": LazyInstallMode.SMART,
    "full": LazyInstallMode.FULL,
    "clean": LazyInstallMode.CLEAN,
    "temporary": LazyInstallMode.TEMPORARY,
    "size_aware": LazyInstallMode.SIZE_AWARE,
    # Special purpose modes
    "interactive": LazyInstallMode.INTERACTIVE,
    "warn": LazyInstallMode.WARN,
    "disabled": LazyInstallMode.DISABLED,
    "dry_run": LazyInstallMode.DRY_RUN,
    # Legacy aliases
    "auto": LazyInstallMode.SMART,
    "on_demand": LazyInstallMode.SMART,
    "on-demand": LazyInstallMode.SMART,
    "lazy": LazyInstallMode.SMART,
}

class LazyInstallConfig:
    """Global configuration for lazy installation per package."""
    _configs: dict[str, bool] = {}
    _modes: dict[str, str] = {}
    _load_modes: dict[str, LazyLoadMode] = {}
    _install_modes: dict[str, LazyInstallMode] = {}
    _mode_configs: dict[str, LazyModeConfig] = {}
    _initialized: dict[str, bool] = {}
    _manual_overrides: dict[str, bool] = {}
    
    @classmethod
    def set(
        cls,
        package_name: str,
        enabled: bool,
        mode: str = "auto",
        install_hook: bool = True,
        manual: bool = False,
        load_mode: Optional[LazyLoadMode] = None,
        install_mode: Optional[LazyInstallMode] = None,
        mode_config: Optional[LazyModeConfig] = None,
    ) -> None:
        """Enable or disable lazy installation for a specific package."""
        package_key = package_name.lower()
        state_manager = LazyStateManager(package_name)
        
        if manual:
            cls._manual_overrides[package_key] = True
            state_manager.set_manual_state(enabled)
        elif cls._manual_overrides.get(package_key):
            global logger
            if logger is None:
                logger = _get_logger()
            logger.debug(
                f"Lazy install config for {package_key} already overridden manually; skipping auto configuration."
            )
            return
        else:
            state_manager.set_manual_state(None)
        
        cls._configs[package_key] = enabled
        cls._modes[package_key] = mode
        
        # Handle two-dimensional mode configuration
        if mode_config:
            cls._mode_configs[package_key] = mode_config
            cls._load_modes[package_key] = mode_config.load_mode
            cls._install_modes[package_key] = mode_config.install_mode
        elif load_mode is not None or install_mode is not None:
            # Explicit mode specification
            if load_mode is None:
                load_mode = LazyLoadMode.AUTO  # Default
            if install_mode is None:
                install_mode = _MODE_ENUM_MAP.get(mode.lower(), LazyInstallMode.SMART)
            cls._load_modes[package_key] = load_mode
            cls._install_modes[package_key] = install_mode
            cls._mode_configs[package_key] = LazyModeConfig(
                load_mode=load_mode,
                install_mode=install_mode
            )
        else:
            # Legacy mode string - try to resolve to preset or default
            preset = get_preset_mode(mode)
            if preset:
                cls._mode_configs[package_key] = preset
                cls._load_modes[package_key] = preset.load_mode
                cls._install_modes[package_key] = preset.install_mode
            else:
                # Fallback to legacy behavior
                install_mode_enum = _MODE_ENUM_MAP.get(mode.lower(), LazyInstallMode.SMART)
                cls._load_modes[package_key] = LazyLoadMode.AUTO
                cls._install_modes[package_key] = install_mode_enum
                cls._mode_configs[package_key] = LazyModeConfig(
                    load_mode=LazyLoadMode.AUTO,
                    install_mode=install_mode_enum
                )
        
        cls._initialize_package(package_key, enabled, mode, install_hook=install_hook)
    
    @classmethod
    def _initialize_package(cls, package_key: str, enabled: bool, mode: str, install_hook: bool = True) -> None:
        """Initialize lazy installation for a specific package."""
        global logger, _log
        if logger is None:
            logger = _get_logger()
        if _log is None:
            _log = _get_log_event()
        
        # Deferred imports to avoid circular dependency
        from .install_registry import LazyInstallerRegistry
        from ...facade import (
            enable_lazy_install,
            disable_lazy_install,
            set_lazy_install_mode,
            enable_lazy_imports,
            install_import_hook,
            uninstall_import_hook,
            is_import_hook_installed,
            sync_manifest_configuration,
        )
        import asyncio
        
        if enabled:
            try:
                # Don't call enable_lazy_install() here - it would create infinite recursion
                # The config is already set by LazyInstallConfig.set() above
                
                # Use explicitly set install_mode from config, or derive from mode string
                # Check if install_mode was explicitly set by checking if package_key exists in _install_modes
                if package_key in cls._install_modes:
                    # install_mode was explicitly set in set() method, don't override it
                    mode_enum = cls._install_modes[package_key]
                else:
                    # Not explicitly set, derive from mode string
                    mode_enum = _MODE_ENUM_MAP.get(mode.lower(), LazyInstallMode.SMART)
                    set_lazy_install_mode(package_key, mode_enum)
                
                # Get load mode from config
                load_mode = cls.get_load_mode(package_key)
                
                # Enable lazy imports with appropriate load mode (skip if NONE mode)
                if load_mode != LazyLoadMode.NONE:
                    enable_lazy_imports(load_mode, package_name=package_key)
                
                # Enable async for modes that support it
                installer = LazyInstallerRegistry.get_instance(package_key)
                if installer:
                    # CRITICAL: Enable the installer (it's disabled by default)
                    installer.enable()
                    
                    if mode_enum in (LazyInstallMode.SMART, LazyInstallMode.FULL, LazyInstallMode.CLEAN, LazyInstallMode.TEMPORARY):
                        installer._async_enabled = True
                        installer._ensure_async_loop()
                        
                        # For FULL mode, install all dependencies on start
                        if mode_enum == LazyInstallMode.FULL:
                            loop = installer._async_loop
                            if loop:
                                asyncio.run_coroutine_threadsafe(installer.install_all_dependencies(), loop)
                
                if install_hook:
                    if not is_import_hook_installed(package_key):
                        install_import_hook(package_key)
                    _log("config", logger.info, f"✅ Lazy installation initialized for {package_key} (install_mode: {mode}, load_mode: {load_mode.value}, hook: installed)")
                else:
                    uninstall_import_hook(package_key)
                    _log("config", logger.info, f"✅ Lazy installation initialized for {package_key} (install_mode: {mode}, load_mode: {load_mode.value}, hook: disabled)")
                
                cls._initialized[package_key] = True
                sync_manifest_configuration(package_key)
            except ImportError as e:
                if logger is None:
                    logger = _get_logger()
                logger.warning(f"⚠️ Could not enable lazy install for {package_key}: {e}")
        else:
            try:
                disable_lazy_install(package_key)
            except ImportError:
                pass
            uninstall_import_hook(package_key)
            cls._initialized[package_key] = False
            _log("config", logger.info, f"❌ Lazy installation disabled for {package_key}")
            sync_manifest_configuration(package_key)
    
    @classmethod
    def is_enabled(cls, package_name: str) -> bool:
        """Check if lazy installation is enabled for a package."""
        return cls._configs.get(package_name.lower(), False)
    
    @classmethod
    def get_mode(cls, package_name: str) -> str:
        """Get the lazy installation mode for a package."""
        return cls._modes.get(package_name.lower(), "auto")
    
    @classmethod
    def get_mode_config(cls, package_name: str) -> Optional[LazyModeConfig]:
        """Get the full mode configuration for a package."""
        return cls._mode_configs.get(package_name.lower())
    
    @classmethod
    def get_load_mode(cls, package_name: str) -> LazyLoadMode:
        """Get the load mode for a package."""
        return cls._load_modes.get(package_name.lower(), LazyLoadMode.NONE)
    
    @classmethod
    def get_install_mode(cls, package_name: str) -> LazyInstallMode:
        """Get the install mode for a package."""
        return cls._install_modes.get(package_name.lower(), LazyInstallMode.NONE)
    
    @classmethod
    def set_install_mode(cls, package_name: str, mode: LazyInstallMode) -> None:
        """Set the install mode for a package."""
        package_key = package_name.lower()
        cls._install_modes[package_key] = mode
        # Update mode config if it exists
        if package_key in cls._mode_configs:
            mode_config = cls._mode_configs[package_key]
            cls._mode_configs[package_key] = LazyModeConfig(
                load_mode=mode_config.load_mode,
                install_mode=mode
            )

