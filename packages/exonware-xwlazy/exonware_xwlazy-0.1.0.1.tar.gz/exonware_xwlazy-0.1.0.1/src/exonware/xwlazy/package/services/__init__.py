"""
Package Services

Supporting services for package operations (not strategies).
"""

from .install_result import InstallStatus, InstallResult
from .install_policy import LazyInstallPolicy
from .install_utils import get_trigger_file, is_externally_managed, check_pip_audit_available
from .install_registry import LazyInstallerRegistry
from .installer_engine import InstallerEngine
from .async_install_handle import AsyncInstallHandle
from .lazy_installer import LazyInstaller
from .strategy_registry import StrategyRegistry

# Config and manifest services
from .config_manager import LazyInstallConfig
from .manifest import (
    PackageManifest,
    LazyManifestLoader,
    get_manifest_loader,
    refresh_manifest_cache,
    sync_manifest_configuration,
    _normalize_prefix,
)

# Discovery service
from .discovery import LazyDiscovery, get_lazy_discovery

# State management and keyword detection (moved to common/services)
from ...common.services import (
    LazyStateManager,
    enable_keyword_detection,
    is_keyword_detection_enabled,
    get_keyword_detection_keyword,
    check_package_keywords,
    _detect_lazy_installation,
    _detect_meta_info_mode,
)

# Host package registration
from .host_packages import (
    register_host_package,
    refresh_host_package,
)

__all__ = [
    # Install services
    'InstallStatus',
    'InstallResult',
    'LazyInstallPolicy',
    'LazyInstallerRegistry',
    'InstallerEngine',
    'AsyncInstallHandle',
    'LazyInstaller',
    'StrategyRegistry',
    'get_trigger_file',
    'is_externally_managed',
    'check_pip_audit_available',
    # Config and manifest
    'LazyInstallConfig',
    'PackageManifest',
    'LazyManifestLoader',
    'get_manifest_loader',
    'refresh_manifest_cache',
    'sync_manifest_configuration',
    '_normalize_prefix',
    # Discovery
    'LazyDiscovery',
    'get_lazy_discovery',
    # State management
    'LazyStateManager',
    # Keyword detection
    'enable_keyword_detection',
    'is_keyword_detection_enabled',
    'get_keyword_detection_keyword',
    'check_package_keywords',
    '_detect_lazy_installation',
    '_detect_meta_info_mode',
    # Host package registration
    'register_host_package',
    'refresh_host_package',
]

