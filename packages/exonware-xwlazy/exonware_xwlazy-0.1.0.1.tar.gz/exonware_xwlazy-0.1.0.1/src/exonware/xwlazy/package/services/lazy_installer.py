"""
Lazy Installer

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Lazy installer that automatically installs missing packages on import failure.
Each instance is isolated per package to prevent interference.
"""

import os
import sys
import time
import asyncio
import threading
import subprocess
import importlib
import importlib.util
from pathlib import Path
from typing import Optional, Any
from collections import OrderedDict
from types import ModuleType

from ..base import APackageHelper
from .config_manager import LazyInstallConfig
from .manifest import PackageManifest
from ...defs import LazyInstallMode
from ...common.cache import InstallationCache
from .install_policy import LazyInstallPolicy
from .install_utils import (
    get_trigger_file,
    is_externally_managed,
    check_pip_audit_available
)
from .async_install_handle import AsyncInstallHandle
from .install_interactive import InteractiveInstallMixin
from .install_cache import InstallCacheMixin
from .install_async import AsyncInstallMixin
from .install_sbom import SBOMAuditMixin

# Lazy import for DependencyMapper to avoid circular dependency
def _get_dependency_mapper():
    """Get DependencyMapper (lazy import to avoid circular dependency)."""
    from ...common.services.dependency_mapper import DependencyMapper
    return DependencyMapper

DependencyMapper = None  # Will be initialized on first use

# Lazy imports to avoid circular dependency
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.lazy_installer")

def _get_log_event():
    """Get log_event function (lazy import to avoid circular dependency)."""
    from ...common.logger import log_event
    return log_event

def _get_print_formatted():
    """Get print_formatted function (lazy import to avoid circular dependency)."""
    from ...common.logger import print_formatted
    return print_formatted

def _get_installing_state():
    """Get installing state (lazy import to avoid circular dependency)."""
    from ...module.importer_engine import get_installing_state
    return get_installing_state()

def _get_spec_cache_put():
    """Get spec_cache_put function (lazy import to avoid circular dependency)."""
    from ...common.services.spec_cache import _spec_cache_put
    return _spec_cache_put

def _get_spec_cache_clear():
    """Get spec_cache_clear function (lazy import to avoid circular dependency)."""
    from ...common.services.spec_cache import _spec_cache_clear
    return _spec_cache_clear

logger = None  # Will be initialized on first use
_log = None  # Will be initialized on first use
print_formatted = None  # Will be initialized on first use
_installing = None  # Will be initialized on first use
_spec_cache_put = None  # Will be initialized on first use
_spec_cache_clear = None  # Will be initialized on first use

# Environment variables
_ENV_ASYNC_INSTALL = os.environ.get("XWLAZY_ASYNC_INSTALL", "").strip().lower() in {"1", "true", "yes", "on"}
_ENV_ASYNC_WORKERS = int(os.environ.get("XWLAZY_ASYNC_WORKERS", "0") or 0)
_KNOWN_MISSING_CACHE_LIMIT = int(os.environ.get("XWLAZY_MISSING_CACHE_MAX", "128") or 128)
_KNOWN_MISSING_CACHE_TTL = float(os.environ.get("XWLAZY_MISSING_CACHE_TTL", "120") or 120.0)
_DEFAULT_ASYNC_CACHE_DIR = Path(
    os.environ.get(
        "XWLAZY_ASYNC_CACHE_DIR",
        os.path.join(os.path.expanduser("~"), ".xwlazy", "wheel-cache"),
    )
)

def _ensure_logging_initialized():
    """Ensure logging utilities are initialized (lazy init to avoid circular imports)."""
    global logger, _log, print_formatted, _installing, _spec_cache_put, _spec_cache_clear
    if logger is None:
        logger = _get_logger()
    if _log is None:
        _log = _get_log_event()
    if print_formatted is None:
        print_formatted = _get_print_formatted()
    if _installing is None:
        _installing = _get_installing_state()
    if _spec_cache_put is None:
        _spec_cache_put = _get_spec_cache_put()
    if _spec_cache_clear is None:
        _spec_cache_clear = _get_spec_cache_clear()

class LazyInstaller(
    APackageHelper,
    InteractiveInstallMixin,
    InstallCacheMixin,
    AsyncInstallMixin,
    SBOMAuditMixin
):
    """
    Lazy installer that automatically installs missing packages on import failure.
    Each instance is isolated per package to prevent interference.
    
    This class extends APackageHelper and provides comprehensive installation functionality.
    """
    
    __slots__ = APackageHelper.__slots__ + (
        '_dependency_mapper',
        '_auto_approve_all',
        '_async_enabled',
        '_async_workers',
        '_async_loop',
        '_async_tasks',
        '_known_missing',
        '_async_cache_dir',
        '_loop_thread',
        '_install_cache',
    )
    
    def __init__(self, package_name: str = 'default'):
        """Initialize lazy installer for a specific package."""
        super().__init__(package_name)
        # Lazy init to avoid circular dependency
        global DependencyMapper
        if DependencyMapper is None:
            DependencyMapper = _get_dependency_mapper()
        self._dependency_mapper = DependencyMapper(package_name)
        self._auto_approve_all = False
        self._async_enabled = False
        self._async_workers = 1
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._async_tasks: dict[str, Any] = {}
        self._known_missing: OrderedDict[str, float] = OrderedDict()
        self._async_cache_dir = _DEFAULT_ASYNC_CACHE_DIR
        self._loop_thread: Optional[threading.Thread] = None
        # Hard force disable async installs to prevent any potential issues
        # This overrides any env vars or manifest settings
        self._async_enabled = False
        
        # ROOT CAUSE FIX: Load persistent installation cache
        # This cache tracks installed packages across Python restarts
        # and prevents unnecessary importability checks and installations
        self._install_cache = InstallationCache()
    
    def install_package(self, package_name: str, module_name: str = None) -> bool:
        """Install a package using pip."""
        sys.stderr.write(f"DEBUG: install_package called for {package_name}\n")
        _ensure_logging_initialized()
        # CRITICAL: Set flag FIRST before ANY operations to prevent recursion
        if getattr(_installing, 'active', False):
            print(f"[DEBUG] Installation already in progress, skipping {package_name} to prevent recursion")
            return False
        
        # Check global recursion depth to prevent infinite recursion
        from ...module.importer_engine import _installation_depth, _installation_depth_lock
        with _installation_depth_lock:
            if _installation_depth > 0:
                print(f"[DEBUG] Installation recursion detected (depth={_installation_depth}), skipping {package_name}")
                return False
            _installation_depth += 1
        
        # Set flag IMMEDIATELY to prevent any imports during installation from triggering recursion
        _installing.active = True
        
        try:
            with self._lock:
                if package_name in self._installed_packages:
                    return True
                
                # ROOT CAUSE FIX: Check if already importable (handles pre-installed packages not in cache)
                # This prevents unnecessary pip calls and handles cache desync
                check_name = module_name or package_name.replace('-', '_')
                if check_name and self._is_module_importable(check_name):
                    _log("install", logger.info, f"Package {package_name} found in environment, marking as installed")
                    # Update caches
                    self._installed_packages.add(package_name)
                    version = self._get_installed_version(package_name)
                    self._install_cache.mark_installed(package_name, version)
                    return True
                
                if package_name in self._failed_packages:
                    return False
                
                if self._mode == LazyInstallMode.DISABLED or self._mode == LazyInstallMode.NONE:
                    _log("install", logger.info, f"Lazy installation disabled for {self._package_name}, skipping {package_name}")
                    return False
                
                if self._mode == LazyInstallMode.WARN:
                    logger.warning(
                        f"[WARN] Package '{package_name}' is missing but WARN mode is active - not installing"
                    )
                    print(
                        f"[WARN] ({self._package_name}): Package '{package_name}' is missing "
                        f"(not installed in WARN mode)"
                    )
                    return False
                
                if self._mode == LazyInstallMode.DRY_RUN:
                    print(f"[DRY RUN] ({self._package_name}): Would install package '{package_name}'")
                    return False
                
                if self._mode == LazyInstallMode.INTERACTIVE:
                    if not self._ask_user_permission(package_name, module_name or package_name):
                        _log("install", logger.info, f"User declined installation of {package_name}")
                        self._failed_packages.add(package_name)
                        return False
                
                # Security checks
                if is_externally_managed():
                    logger.error(f"Cannot install {package_name}: Environment is externally managed (PEP 668)")
                    print(f"\n[ERROR] This Python environment is externally managed (PEP 668)")
                    print(f"Package '{package_name}' cannot be installed in this environment.")
                    print(f"\nSuggested solutions:")
                    print(f"  1. Create a virtual environment:")
                    print(f"     python -m venv .venv")
                    print(f"     .venv\\Scripts\\activate  # Windows")
                    print(f"     source .venv/bin/activate  # Linux/macOS")
                    print(f"  2. Use pipx for isolated installs:")
                    print(f"     pipx install {package_name}")
                    print(f"  3. Override with --break-system-packages (NOT RECOMMENDED)\n")
                    self._failed_packages.add(package_name)
                    return False
                
                allowed, reason = LazyInstallPolicy.is_package_allowed(self._package_name, package_name)
                if not allowed:
                    logger.error(f"Cannot install {package_name}: {reason}")
                    print(f"\n[SECURITY] Package '{package_name}' blocked: {reason}\n")
                    self._failed_packages.add(package_name)
                    return False
                
                # Show warning about missing library with trigger file
                trigger_file = get_trigger_file()
                module_display = module_name or package_name
                if trigger_file:
                    used_for = module_display if module_display != package_name else package_name
                    print_formatted(
                        "WARN",
                        f"Missing library {package_name} used for ({used_for}) triggered by {trigger_file}",
                        same_line=True
                    )
                else:
                    print_formatted(
                        "WARN",
                        f"Missing library {package_name} used for ({module_display})",
                        same_line=True
                    )
                
                # Proceed with installation
                try:
                    print_formatted("INFO", f"Installing package: {package_name}", same_line=True)
                    policy_args = LazyInstallPolicy.get_pip_args(self._package_name) or []

                    cache_args = list(policy_args)
                    if self._install_from_cached_tree(package_name):
                        print_formatted("ACTION", f"Installing {package_name} via pip...", same_line=True)
                        time.sleep(0.1)
                        self._finalize_install_success(package_name, "cache-tree")
                        return True

                    if self._install_from_cached_wheel(package_name, cache_args):
                        print_formatted("ACTION", f"Installing {package_name} via pip...", same_line=True)
                        wheel_path = self._cached_wheel_name(package_name)
                        self._materialize_cached_tree(package_name, wheel_path)
                        time.sleep(0.1)
                        self._finalize_install_success(package_name, "cache")
                        return True

                    wheel_path = self._ensure_cached_wheel(package_name, cache_args)
                    if wheel_path and self._pip_install_from_path(wheel_path, cache_args):
                        print_formatted("ACTION", f"Installing {package_name} via pip...", same_line=True)
                        self._materialize_cached_tree(package_name, wheel_path)
                        time.sleep(0.1)
                        self._finalize_install_success(package_name, "wheel")
                        return True

                    # Show installation message with animated dots
                    print_formatted("ACTION", f"Installing {package_name} via pip...", same_line=True)
                    
                    # Animate dots while installing
                    stop_animation = threading.Event()
                    
                    def animate_dots():
                        dots = ["", ".", "..", "..."]
                        i = 0
                        while not stop_animation.is_set():
                            msg = f"Installing {package_name} via pip{dots[i % len(dots)]}"
                            print_formatted("ACTION", msg, same_line=True)
                            i += 1
                            time.sleep(0.3)
                    
                    animator = threading.Thread(target=animate_dots, daemon=True)
                    animator.start()
                    
                    try:
                        pip_args = [sys.executable, '-m', 'pip', 'install']
                        if policy_args:
                            pip_args.extend(policy_args)
                            logger.debug(f"Using policy args: {policy_args}")
                        
                        pip_args.append(package_name)
                        
                        result = subprocess.run(
                            pip_args,
                            capture_output=True,
                            text=True,
                            check=True
                        )
                    finally:
                        stop_animation.set()
                        animator.join(timeout=0.5)
                    
                    self._finalize_install_success(package_name, "pip")
                    wheel_path = self._ensure_cached_wheel(package_name, cache_args)
                    if wheel_path:
                        self._materialize_cached_tree(package_name, wheel_path)
                    return True
                    
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install {package_name}: {e.stderr}")
                    print(f"[FAIL] Failed to install {package_name}\n")
                    self._failed_packages.add(package_name)
                    return False
                except Exception as e:
                    logger.error(f"Unexpected error installing {package_name}: {e}")
                    print(f"[ERROR] Unexpected error: {e}\n")
                    self._failed_packages.add(package_name)
                    return False
        finally:
            # CRITICAL: Always clear the installing flag
            _installing.active = False
            # Decrement global recursion depth
            from ...module.importer_engine import _installation_depth, _installation_depth_lock
            with _installation_depth_lock:
                _installation_depth = max(0, _installation_depth - 1)
    
    def _finalize_install_success(self, package_name: str, source: str) -> None:
        """Finalize successful installation by updating caches."""
        # Update in-memory cache
        self._installed_packages.add(package_name)
        
        # ROOT CAUSE FIX: Mark in persistent cache (survives Python restarts)
        version = self._get_installed_version(package_name)
        self._install_cache.mark_installed(package_name, version)
        
        print_formatted("SUCCESS", f"Successfully installed via {source}: {package_name}", same_line=True)
        print()
        
        # CRITICAL: Invalidate import caches so Python can see newly installed modules
        importlib.invalidate_caches()
        sys.path_importer_cache.clear()
        
        if check_pip_audit_available():
            self._run_vulnerability_audit(package_name)
        self._update_lockfile(package_name)
    
    def _get_installed_version(self, package_name: str) -> Optional[str]:
        """Get installed version of a package."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split(':', 1)[1].strip()
        except Exception as e:
            logger.debug(f"Could not get version for {package_name}: {e}")
        return None
    
    def uninstall_package(self, package_name: str, quiet: bool = True) -> bool:
        """Uninstall a package (synchronous wrapper)."""
        if self._async_loop and self._async_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.uninstall_package_async(package_name, quiet=quiet),
                self._async_loop
            )
            return True
        else:
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', package_name],
                    capture_output=quiet,
                    check=False
                )
                if result.returncode == 0:
                    with self._lock:
                        self._installed_packages.discard(package_name)
                    return True
                return False
            except Exception as e:
                logger.debug(f"Failed to uninstall {package_name}: {e}")
                return False
    
    def uninstall_all_packages(self, quiet: bool = True) -> None:
        """Uninstall all packages installed by this installer."""
        with self._lock:
            packages_to_uninstall = list(self._installed_packages)
            for package_name in packages_to_uninstall:
                self.uninstall_package(package_name, quiet=quiet)
    
    def _is_module_importable(self, module_name: str) -> bool:
        """Check if module can be imported without installation."""
        # CRITICAL FIX: Check if import is already in progress to prevent recursion
        from ...module.importer_engine import _is_import_in_progress
        if _is_import_in_progress(module_name):
            # Import is already in progress, don't check again to avoid recursion
            return False
        
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None and spec.loader is not None
        except (ValueError, AttributeError, ImportError, Exception):
            return False
    
    def is_package_installed(self, package_name: str) -> bool:
        """Check if a package is already installed."""
        # Step 1: Check persistent cache FIRST (fastest, no importability check needed)
        if self._install_cache.is_installed(package_name):
            # Also update in-memory cache for performance
            self._installed_packages.add(package_name)
            return True
        
        # Step 2: Check in-memory cache (fast, but lost on restart)
        if package_name in self._installed_packages:
            return True
        
        # Step 3: Check actual importability (slower, but accurate)
        try:
            # Get module name from package name (heuristic)
            module_name = package_name.replace('-', '_')
            if self._is_module_importable(module_name):
                # Cache in both persistent and in-memory cache
                version = self._get_installed_version(package_name)
                self._install_cache.mark_installed(package_name, version)
                self._installed_packages.add(package_name)
                return True
        except (ImportError, AttributeError, ValueError) as e:
            # Expected errors when checking package installation
            _ensure_logging_initialized()
            if logger:
                logger.debug(f"Package check failed for {package_name}: {e}")
            pass
        except Exception as e:
            # Unexpected errors - log but don't fail
            _ensure_logging_initialized()
            if logger:
                logger.debug(f"Unexpected error checking package {package_name}: {e}")
            pass
        
        return False
    
    def install_and_import(self, module_name: str, package_name: str = None) -> tuple[Optional[ModuleType], bool]:
        """
        Install package and import module.
        
        ROOT CAUSE FIX: Check if module is importable FIRST before attempting
        installation. This prevents circular imports and unnecessary installations.
        """
        # CRITICAL: Initialize lazy imports first
        _ensure_logging_initialized()
        
        sys.stderr.write(f"DEBUG: install_and_import called for {module_name}\n")
        # CRITICAL: Prevent recursion - if installation is already in progress, skip
        if getattr(_installing, 'active', False):
            sys.stderr.write(f"DEBUG: Recursion guard hit for {module_name}\n")
            logger.debug(
                f"Installation in progress, skipping install_and_import for {module_name} "
                f"to prevent recursion"
            )
            return None, False
        
        if not self.is_enabled():
            sys.stderr.write(f"DEBUG: Installer disabled for {module_name}\n")
            return None, False
        
        # Get package name early for cache check
        if package_name is None:
            package_name = self._dependency_mapper.get_package_name(module_name)
        
        sys.stderr.write(f"DEBUG: package_name for {module_name} is {package_name}\n")
        
        # ROOT CAUSE FIX: Check persistent cache FIRST (fastest, no importability check)
        if package_name and self._install_cache.is_installed(package_name):
            # Package is in persistent cache - import directly
            # CRITICAL: Remove finders before importing to prevent recursion
            xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
            xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
            for finder in xwlazy_finders:
                try:
                    sys.meta_path.remove(finder)
                except ValueError:
                    pass
            
            try:
                module = importlib.import_module(module_name)
                self._clear_module_missing(module_name)
                # Also remove finders before find_spec to prevent recursion
                spec = importlib.util.find_spec(module_name)
                _spec_cache_put(module_name, spec)
                logger.debug(f"Module {module_name} is in persistent cache, imported directly")
                return module, True
            except ImportError as e:
                _log("install", logger.warning, f"Module {module_name} in cache but import failed: {e}")
                # ROOT CAUSE FIX: Cache is stale - invalidate it so we try to install properly
                if package_name:
                    logger.debug(f"Invalidating stale cache entry for {package_name}")
                    self._install_cache.mark_uninstalled(package_name)
                    with self._lock:
                        self._installed_packages.discard(package_name)
                        # Also clear from failed packages so we can retry installation
                        self._failed_packages.discard(package_name)
                # Fall through to importability check and installation
            finally:
                # Restore finders
                for finder in reversed(xwlazy_finders):
                    if finder not in sys.meta_path:
                        sys.meta_path.insert(0, finder)
        
        # ROOT CAUSE FIX: Check if module is ALREADY importable BEFORE doing anything else
        # But first, remove finders to prevent recursion
        xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
        xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
        for finder in xwlazy_finders:
            try:
                sys.meta_path.remove(finder)
            except ValueError:
                pass

        try:
            is_importable = self._is_module_importable(module_name)
        finally:
            # Restore finders
            for finder in reversed(xwlazy_finders):
                if finder not in sys.meta_path:
                    sys.meta_path.insert(0, finder)

        if is_importable:
            # Module is already importable - import it directly
            if package_name:
                version = self._get_installed_version(package_name)
                self._install_cache.mark_installed(package_name, version)
            try:
                module = importlib.import_module(module_name)
                self._clear_module_missing(module_name)
                _spec_cache_put(module_name, importlib.util.find_spec(module_name))
                logger.debug(f"Module {module_name} is already importable, imported directly")
                return module, True
            except ImportError as e:
                _log("install", logger.warning, f"Module {module_name} appeared importable but import failed: {e}")
                # ROOT CAUSE FIX: If importability check passed but import failed, invalidate cache
                if package_name:
                    logger.debug(f"Invalidating stale cache entry for {package_name} (importability check was wrong)")
                    self._install_cache.mark_uninstalled(package_name)
                    with self._lock:
                        self._installed_packages.discard(package_name)
                        # Also clear from failed packages so we can retry installation
                        self._failed_packages.discard(package_name)
        
        # Package name should already be set from cache check above
        if package_name is None:
            package_name = self._dependency_mapper.get_package_name(module_name)
            if package_name is None:
                logger.debug(f"Module '{module_name}' is a system/built-in module, not installing")
                return None, False
        
        # Module is NOT importable - need to install it
        # ROOT CAUSE FIX: Temporarily remove ALL xwlazy finders from sys.meta_path
        xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
        xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
        for finder in xwlazy_finders:
            try:
                sys.meta_path.remove(finder)
            except ValueError:
                pass
        
        try:
            # Try importing again after removing finders (in case it was a false negative)
            module = importlib.import_module(module_name)
            self._clear_module_missing(module_name)
            _spec_cache_put(module_name, importlib.util.find_spec(module_name))
            return module, True
        except ImportError:
            pass
        finally:
            # Restore finders in reverse order to maintain original position
            for finder in reversed(xwlazy_finders):
                if finder not in sys.meta_path:
                    sys.meta_path.insert(0, finder)
        
        if self._async_enabled:
            handle = self.schedule_async_install(module_name)
            if handle is not None:
                return None, False

        if self.install_package(package_name, module_name):
            for attempt in range(3):
                try:
                    importlib.invalidate_caches()
                    sys.path_importer_cache.clear()
                    
                    # ROOT CAUSE FIX: Remove ALL xwlazy finders before importing
                    xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
                    xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
                    for finder in xwlazy_finders:
                        try:
                            sys.meta_path.remove(finder)
                        except ValueError:
                            pass
                    
                    try:
                        module = importlib.import_module(module_name)
                        self._clear_module_missing(module_name)
                        _spec_cache_put(module_name, importlib.util.find_spec(module_name))
                        # ROOT CAUSE FIX: Mark in both persistent and in-memory cache
                        version = self._get_installed_version(package_name)
                        self._install_cache.mark_installed(package_name, version)
                        self._installed_packages.add(package_name)
                        return module, True
                    finally:
                        # Restore finders in reverse order to maintain original position
                        for finder in reversed(xwlazy_finders):
                            if finder not in sys.meta_path:
                                sys.meta_path.insert(0, finder)
                except ImportError as e:
                    _log("install", logger.warning, f"Import retry {attempt} failed for {module_name}: {e}")
                    if attempt < 2:
                        time.sleep(0.1 * (attempt + 1))
                    else:
                        logger.error(f"Still cannot import {module_name} after installing {package_name}: {e}")
                        return None, False
        
        self._mark_module_missing(module_name)
        return None, False
    
    def _check_security_policy(self, package_name: str) -> tuple[bool, str]:
        """Check security policy for package."""
        return LazyInstallPolicy.is_package_allowed(self._package_name, package_name)
    
    def _run_pip_install(self, package_name: str, args: list[str]) -> bool:
        """Run pip install with arguments."""
        if self._install_from_cached_wheel(package_name):
            return True
        try:
            pip_args = [
                sys.executable,
                '-m',
                'pip',
                'install',
                '--disable-pip-version-check',
                '--no-input',
            ] + args + [package_name]
            _log("install", logger.info, f"Running pip install for {package_name}...")
            result = subprocess.run(
                pip_args,
                capture_output=True,
                text=True,
                check=True,
            )
            if result.returncode == 0:
                self._ensure_cached_wheel(package_name)
                _log("install", logger.info, f"Pip install successful for {package_name}")
                return True
            _log("install", logger.error, f"Pip failed for {package_name}: {result.stderr}")
            print(f"DEBUG: Pip failed for {package_name}: {result.stderr}")
            return False
        except subprocess.CalledProcessError as e:
            _log("install", logger.error, f"Pip error for {package_name}: {e.stderr if hasattr(e, 'stderr') else e}")
            print(f"DEBUG: Pip error for {package_name}: {e.stderr if hasattr(e, 'stderr') else e}")
            return False
    
    def get_installed_packages(self) -> set[str]:
        """Get set of installed package names."""
        with self._lock:
            return self._installed_packages.copy()
    
    def get_failed_packages(self) -> set[str]:
        """Get set of failed package names."""
        with self._lock:
            return self._failed_packages.copy()
    
    def get_async_tasks(self) -> dict[str, Any]:
        """Get dictionary of async installation tasks."""
        with self._lock:
            return {
                module_name: {
                    'done': task.done() if task else False,
                    'cancelled': task.cancelled() if task else False,
                }
                for module_name, task in self._async_tasks.items()
            }
    
    def get_stats(self) -> dict[str, Any]:
        """Get installation statistics (extends base class method)."""
        base_stats = super().get_stats()
        with self._lock:
            base_stats.update({
                'async_enabled': self._async_enabled,
                'async_workers': self._async_workers,
                'async_tasks_count': len(self._async_tasks),
                'known_missing_count': len(self._known_missing),
                'auto_approve_all': self._auto_approve_all,
            })
        return base_stats
    
    # Abstract method implementations from APackageHelper
    def _discover_from_sources(self) -> None:
        """Discover dependencies from all sources."""
        # Lazy import to avoid circular dependency
        from ...package.discovery import get_lazy_discovery
        discovery = get_lazy_discovery()
        if discovery:
            all_deps = discovery.discover_all_dependencies()
            for import_name, package_name in all_deps.items():
                from ...defs import DependencyInfo
                self.discovered_dependencies[import_name] = DependencyInfo(
                    import_name=import_name,
                    package_name=package_name,
                    source='discovery',
                    category='discovered'
                )
    
    def _is_cache_valid(self) -> bool:
        """Check if cached dependencies are still valid."""
        # Use discovery's cache validation
        # Lazy import to avoid circular dependency
        from ...package.discovery import get_lazy_discovery
        discovery = get_lazy_discovery()
        if discovery:
            return discovery._is_cache_valid()
        return False
    
    def _add_common_mappings(self) -> None:
        """Add common import -> package mappings."""
        # Common mappings are handled by discovery
        pass
    
    def _update_file_mtimes(self) -> None:
        """Update file modification times for cache validation."""
        # File mtimes are handled by discovery
        pass
    
    def _check_importability(self, package_name: str) -> bool:
        """Check if package is importable."""
        return self.is_package_installed(package_name)
    
    def _check_persistent_cache(self, package_name: str) -> bool:
        """Check persistent cache for package installation status."""
        return self._install_cache.is_installed(package_name)
    
    def _mark_installed_in_persistent_cache(self, package_name: str) -> None:
        """Mark package as installed in persistent cache."""
        version = self._get_installed_version(package_name)
        self._install_cache.mark_installed(package_name, version)
    
    def _mark_uninstalled_in_persistent_cache(self, package_name: str) -> None:
        """Mark package as uninstalled in persistent cache."""
        self._install_cache.mark_uninstalled(package_name)
    
    def _run_install(self, *package_names: str) -> None:
        """Run pip install for packages."""
        for package_name in package_names:
            self.install_package(package_name)
    
    def _run_uninstall(self, *package_names: str) -> None:
        """Run pip uninstall for packages."""
        for package_name in package_names:
            self.uninstall_package(package_name, quiet=True)
    
    def is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        return self._is_cache_valid()

__all__ = ['LazyInstaller']

