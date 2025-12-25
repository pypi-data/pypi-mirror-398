"""
#exonware/xwlazy/src/exonware/xwlazy/defs.py

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Generation Date: 10-Oct-2025

Type Definitions and Constants for Lazy Loading System

This module defines type definitions, constants, and TypedDict structures
for the lazy loading system following GUIDE_ARCH.md structure.
"""

from enum import Enum
from typing import TypedDict, Optional, Any
from dataclasses import dataclass, field
from types import ModuleType

# =============================================================================
# ENUMS
# =============================================================================

class LazyLoadMode(Enum):
    """Controls lazy module loading behavior."""
    NONE = "none"           # Standard imports (no lazy loading)
    AUTO = "auto"           # Lazy loading enabled (deferred module loading)
    PRELOAD = "preload"     # Preload all modules on start
    BACKGROUND = "background"  # Load modules in background threads
    CACHED = "cached"       # Cache loaded modules but allow unloading
    # Superior performance modes
    TURBO = "turbo"         # Multi-tier cache + parallel preloading + bytecode caching
    ADAPTIVE = "adaptive"   # Self-optimizing with pattern learning
    HYPERPARALLEL = "hyperparallel"  # Maximum parallelism with multi-threading
    STREAMING = "streaming" # Asynchronous background loading with streaming
    ULTRA = "ultra"         # Aggressive optimizations (pre-compiled bytecode, mmap, etc.)
    INTELLIGENT = "intelligent"  # Automatically switches to fastest mode based on load level

class LazyInstallMode(Enum):
    """Lazy installation modes."""
    # Core modes
    NONE = "none"           # No auto-installation
    SMART = "smart"         # Install on first usage (on-demand) - replaces AUTO
    FULL = "full"           # Install all dependencies on start
    CLEAN = "clean"         # Install on usage + uninstall after completion
    TEMPORARY = "temporary"  # Always uninstall after use (more aggressive than CLEAN)
    SIZE_AWARE = "size_aware"  # Install small packages, skip large ones
    
    # Special purpose modes (kept for specific use cases)
    INTERACTIVE = "interactive"  # Ask user before installing
    WARN = "warn"           # Log warning but don't install (for monitoring)
    DISABLED = "disabled"   # Don't install anything (alias for NONE, more explicit)
    DRY_RUN = "dry_run"    # Show what would be installed but don't install

class PathType(Enum):
    """Path types for validation."""
    FILE = "file"
    DIRECTORY = "directory"
    UNKNOWN = "unknown"

class InstallStatus(Enum):
    """Installation status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class LoadLevel(Enum):
    """Load level categories."""
    LIGHT = "light_load"
    MEDIUM = "medium_load"
    HEAVY = "heavy_load"
    ENTERPRISE = "enterprise_load"

# =============================================================================
# DATACLASSES
# =============================================================================

@dataclass
class DependencyInfo:
    """Information about a discovered dependency."""
    import_name: str
    package_name: str
    version: Optional[str] = None
    source: str = "unknown"
    category: str = "general"

@dataclass
class LazyModeConfig:
    """Two-dimensional lazy mode configuration combining load and install modes."""
    load_mode: LazyLoadMode = LazyLoadMode.NONE
    install_mode: LazyInstallMode = LazyInstallMode.NONE
    
    # Additional configuration options
    auto_uninstall_large: bool = False  # For AUTO_MODE behavior
    large_package_threshold_mb: float = 50.0  # Size threshold for SIZE_AWARE mode
    preload_priority: list[str] = field(default_factory=list)  # Priority modules for PRELOAD
    background_workers: int = 2  # Workers for BACKGROUND mode
    
    def __post_init__(self):
        """Normalize enum values."""
        if isinstance(self.load_mode, str):
            self.load_mode = LazyLoadMode(self.load_mode)
        if isinstance(self.install_mode, str):
            self.install_mode = LazyInstallMode(self.install_mode)

@dataclass
class InstallResult:
    """Result of an installation operation."""
    package_name: str
    success: bool
    status: InstallStatus
    error: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None  # "cache", "pip", "wheel", etc.

@dataclass
class LazyConfig:
    """Bridge configuration settings with the lazy package implementation."""
    packages: tuple[str, ...] = field(
        default_factory=lambda: ("default",)
    )
    
    def __post_init__(self) -> None:
        self.packages = tuple(package.lower() for package in self.packages)

@dataclass(frozen=True)
class PackageManifest:
    """Resolved manifest data for a single package."""
    package: str
    dependencies: dict[str, str] = field(default_factory=dict)
    watched_prefixes: tuple[str, ...] = ()
    async_installs: bool = False
    async_workers: int = 1
    class_wrap_prefixes: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def get_dependency(self, import_name: str) -> Optional[str]:
        """Return the declared package for the given import name."""
        if not import_name:
            return None
        direct = self.dependencies.get(import_name)
        if direct is not None:
            return direct
        # Case-insensitive fallback for convenience
        return self.dependencies.get(import_name.lower())

@dataclass(frozen=True)
class PackageData:
    """
    Immutable package data - same across all strategies.
    
    This data structure is used by all package caching, helper, and manager strategies.
    """
    name: str
    version: Optional[str] = None
    installed: bool = False
    install_time: Optional[float] = None
    access_count: int = 0
    install_mode: Optional['LazyInstallMode'] = None
    error: Optional[Exception] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ModuleData:
    """
    Immutable module data - same across all strategies.
    
    This data structure is used by all module caching, helper, and manager strategies.
    """
    path: str
    loaded_module: Optional['ModuleType'] = None
    loading: bool = False
    load_time: Optional[float] = None
    access_count: int = 0
    error: Optional[Exception] = None
    metadata: dict[str, Any] = field(default_factory=dict)

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class DependencyMapping(TypedDict, total=False):
    """Type definition for dependency mapping structure."""
    import_name: str
    package_name: str
    version: Optional[str]
    source: str
    category: str

class PackageStats(TypedDict, total=False):
    """Type definition for package statistics."""
    enabled: bool
    mode: str
    package_name: str
    installed_packages: list[str]
    failed_packages: list[str]
    total_installed: int
    total_failed: int

class LazyStatus(TypedDict, total=False):
    """Type definition for lazy mode status."""
    enabled: bool
    hook_installed: bool
    lazy_install_enabled: bool
    active: bool
    error: Optional[str]

# =============================================================================
# CONSTANTS
# =============================================================================

# Default configuration values
DEFAULT_LARGE_PACKAGE_THRESHOLD_MB: float = 50.0
DEFAULT_BACKGROUND_WORKERS: int = 2
DEFAULT_PRELOAD_PRIORITY: list[str] = []

# Common import -> package mappings (will be populated from discovery)
COMMON_IMPORT_MAPPINGS: dict[str, str] = {
    # Common mappings that are frequently used
    'cv2': 'opencv-python',
    'PIL': 'Pillow',
    'yaml': 'PyYAML',
    'toml': 'toml',
    'pandas': 'pandas',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'sklearn': 'scikit-learn',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'requests': 'requests',
    'urllib3': 'urllib3',
    'bs4': 'beautifulsoup4',
    'lxml': 'lxml',
    'jinja2': 'Jinja2',
    'flask': 'Flask',
    'django': 'Django',
    'fastapi': 'fastapi',
    'pydantic': 'pydantic',
    'sqlalchemy': 'SQLAlchemy',
    'psycopg2': 'psycopg2-binary',
    'pymongo': 'pymongo',
    'redis': 'redis',
    'celery': 'celery',
    'boto3': 'boto3',
    'azure': 'azure-storage-blob',
    'google': 'google-cloud-storage',
    'tensorflow': 'tensorflow',
    'torch': 'torch',
    'transformers': 'transformers',
    'openai': 'openai',
    'anthropic': 'anthropic',
}

# Package discovery source names
DISCOVERY_SOURCE_PYPROJECT = "pyproject.toml"
DISCOVERY_SOURCE_REQUIREMENTS = "requirements.txt"
DISCOVERY_SOURCE_SETUP = "setup.py"
DISCOVERY_SOURCE_POETRY = "poetry.lock"
DISCOVERY_SOURCE_PIPFILE = "Pipfile"
DISCOVERY_SOURCE_MANIFEST = "manifest.json"

# Installation mode aliases
INSTALL_MODE_ALIASES: dict[str, str] = {
    'auto': 'smart',
    'on_demand': 'smart',
    'on-demand': 'smart',
    'lazy': 'smart',
}

# Cache keys
CACHE_KEY_DEPENDENCIES = "dependencies"
CACHE_KEY_PACKAGE_INFO = "package_info"
CACHE_KEY_INSTALL_STATUS = "install_status"
CACHE_KEY_DISCOVERY_SOURCES = "discovery_sources"

# File patterns for discovery
PYPROJECT_PATTERN = "pyproject.toml"
REQUIREMENTS_PATTERN = "requirements*.txt"
SETUP_PATTERN = "setup.py"
POETRY_PATTERN = "poetry.lock"
PIPFILE_PATTERN = "Pipfile"

# =============================================================================
# PRESET MODE MAPPINGS
# =============================================================================

# Preset mode combinations for convenience
PRESET_MODES: dict[str, LazyModeConfig] = {
    "none": LazyModeConfig(
        load_mode=LazyLoadMode.NONE,
        install_mode=LazyInstallMode.NONE
    ),
    "lite": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.NONE
    ),
    "smart": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.SMART
    ),
    "full": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.FULL
    ),
    "clean": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.CLEAN
    ),
    "temporary": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.TEMPORARY
    ),
    "size_aware": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.SIZE_AWARE
    ),
    "auto": LazyModeConfig(
        load_mode=LazyLoadMode.AUTO,
        install_mode=LazyInstallMode.SMART,
        auto_uninstall_large=True
    ),
}

def get_preset_mode(preset_name: str) -> Optional[LazyModeConfig]:
    """Get preset mode configuration by name."""
    return PRESET_MODES.get(preset_name.lower())

# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    # Enums
    'LazyLoadMode',
    'LazyInstallMode',
    'PathType',
    'InstallStatus',
    'LoadLevel',
    # Dataclasses
    'DependencyInfo',
    'LazyModeConfig',
    'InstallResult',
    'LazyConfig',
    'PackageManifest',
    'PackageData',
    'ModuleData',
    # Type definitions
    'DependencyMapping',
    'PackageStats',
    'LazyStatus',
    # Constants
    'DEFAULT_LARGE_PACKAGE_THRESHOLD_MB',
    'DEFAULT_BACKGROUND_WORKERS',
    'DEFAULT_PRELOAD_PRIORITY',
    'COMMON_IMPORT_MAPPINGS',
    'DISCOVERY_SOURCE_PYPROJECT',
    'DISCOVERY_SOURCE_REQUIREMENTS',
    'DISCOVERY_SOURCE_SETUP',
    'DISCOVERY_SOURCE_POETRY',
    'DISCOVERY_SOURCE_PIPFILE',
    'DISCOVERY_SOURCE_MANIFEST',
    'INSTALL_MODE_ALIASES',
    'CACHE_KEY_DEPENDENCIES',
    'CACHE_KEY_PACKAGE_INFO',
    'CACHE_KEY_INSTALL_STATUS',
    'CACHE_KEY_DISCOVERY_SOURCES',
    'PYPROJECT_PATTERN',
    'REQUIREMENTS_PATTERN',
    'SETUP_PATTERN',
    'POETRY_PATTERN',
    'PIPFILE_PATTERN',
    # Preset modes
    'PRESET_MODES',
    'get_preset_mode',
]

