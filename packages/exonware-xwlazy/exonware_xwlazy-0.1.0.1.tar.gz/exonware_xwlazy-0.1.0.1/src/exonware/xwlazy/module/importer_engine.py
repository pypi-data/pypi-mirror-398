"""
#exonware/xwlazy/src/exonware/xwlazy/module/importer_engine.py

Import Engine - Unified engine for all import-related operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

This module provides unified import engine for all import-related functionality.
All import-related functionality is centralized here.

Merged from:
- logging_utils.py (Logging utilities)
- import_tracking.py (Import tracking)
- prefix_trie.py (Prefix trie data structure)
- watched_registry.py (Watched prefix registry)
- deferred_loader.py (Deferred module loader)
- cache_utils.py (Multi-tier cache and bytecode cache)
- parallel_utils.py (Parallel loading utilities)
- module_patching.py (Module patching utilities)
- archive_imports.py (Archive import utilities)
- bootstrap.py (Bootstrap utilities)
- loader.py (Lazy loader)
- registry.py (Lazy module registry)
- importer.py (Lazy importer)
- import_hook.py (Import hook)
- meta_path_finder.py (Meta path finder)

Features:
- Unified import engine for all import operations
- Multi-tier caching (L1/L2/L3)
- Parallel loading support
- Import tracking and circular import prevention
- Watched prefix registry
- Meta path finder for intercepting imports
"""

# =============================================================================
# IMPORTS
# =============================================================================

from __future__ import annotations

import os
import sys
import json
import time
import asyncio
import pickle
import struct
import builtins
import atexit
import logging
import importlib
import importlib.util
import importlib.machinery
import importlib.abc
import threading
import subprocess
import concurrent.futures
from pathlib import Path
from types import ModuleType
from typing import Optional, Any, Iterable, Callable
from collections import OrderedDict, defaultdict, Counter, deque
from queue import Queue
from datetime import datetime
from enum import Enum

from ..defs import LazyLoadMode, LazyInstallMode
from ..common.services.dependency_mapper import DependencyMapper
from ..common.services.spec_cache import _spec_cache_get, _spec_cache_put
from ..package.services import LazyInstallerRegistry, LazyInstaller
from ..package.services.config_manager import LazyInstallConfig
from ..package.services.manifest import _normalize_prefix
from ..errors import DeferredImportError
from .base import AModuleHelper

# Import from common (logger and cache)
from ..common.logger import get_logger, log_event
from ..common.cache import MultiTierCache, BytecodeCache

# Import from runtime folder (moved from module folder)
from ..runtime.adaptive_learner import AdaptiveLearner
from ..runtime.intelligent_selector import IntelligentModeSelector, LoadLevel

# =============================================================================
# LOGGER (from common.logger)
# =============================================================================

logger = get_logger("xwlazy.importer_engine")

# =============================================================================
# IMPORT TRACKING (from import_tracking.py)
# =============================================================================

_thread_local = threading.local()
_importing = threading.local()
_installing = threading.local()

_installation_depth = 0
_installation_depth_lock = threading.Lock()

# Thread-local flag to prevent recursion during installation checks
_checking_installation = threading.local()

def _get_thread_imports() -> set[str]:
    """Get thread-local import set (creates if needed)."""
    if not hasattr(_thread_local, 'imports'):
        _thread_local.imports = set()
    return _thread_local.imports

def _is_checking_installation() -> bool:
    """Check if we're currently checking installation status (to prevent recursion)."""
    return getattr(_checking_installation, 'active', False)

def _set_checking_installation(value: bool) -> None:
    """Set the installation check flag."""
    _checking_installation.active = value

def _is_import_in_progress(module_name: str) -> bool:
    """Check if a module import is currently in progress for this thread."""
    return module_name in _get_thread_imports()

def _mark_import_started(module_name: str) -> None:
    """Mark a module import as started for this thread."""
    _get_thread_imports().add(module_name)

def _mark_import_finished(module_name: str) -> None:
    """Mark a module import as finished for this thread."""
    _get_thread_imports().discard(module_name)

def get_importing_state() -> threading.local:
    """Get thread-local importing state."""
    return _importing

def get_installing_state() -> threading.local:
    """Get thread-local installing state."""
    return _installing

# Thread-local storage for installation state
_installing_state = get_installing_state()
_importing_state = get_importing_state()

# Global recursion depth counter to prevent infinite recursion
_installation_depth = 0
_installation_depth_lock = threading.Lock()

# =============================================================================
# GLOBAL __import__ HOOK (Critical for Module-Level Imports)
# =============================================================================

# Global state for builtins.__import__ hook
_original_builtins_import: Optional[Callable] = None
_global_import_hook_installed: bool = False
_global_import_hook_lock = threading.RLock()

# Fast-path caches for O(1) lookup
_installed_cache: set[str] = set()
_failed_cache: set[str] = set()

# Registry of packages that should auto-install
_lazy_packages: dict[str, Any] = {}

def register_lazy_package(package_name: str, config: Optional[Any] = None) -> None:
    """
    Register a package for lazy loading/installation.
    
    Args:
        package_name: Package name to register
        config: Optional configuration object
    """
    with _global_import_hook_lock:
        _lazy_packages[package_name] = config or {}
        logger.debug(f"Registered lazy package: {package_name}")

def _should_auto_install(module_name: str) -> bool:
    """
    Check if module should be auto-installed.
    
    Checks if:
    1. Module's root package is registered, OR
    2. Module maps to a known package (via DependencyMapper) AND packages are registered
    
    Args:
        module_name: Module name to check
        
    Returns:
        True if should auto-install, False otherwise
    """
    root_package = module_name.split('.')[0]
    
    # Fast path: root package is registered
    if root_package in _lazy_packages:
        return True
    
    # If no packages are registered, don't auto-install
    if not _lazy_packages:
        return False
    
    # Check if module maps to a known package via DependencyMapper
    # This handles cases like:
    # - 'yaml' -> 'PyYAML' (different name)
    # - 'msgpack' -> 'msgpack' (same name, but still a known dependency)
    # - 'bson' -> 'pymongo' (different name)
    try:
        # Use the first registered package to get the mapper context
        # All registered packages should have the same dependency mappings
        registered_package = next(iter(_lazy_packages.keys()), None)
        if registered_package:
            mapper = DependencyMapper(package_name=registered_package)
        else:
            mapper = DependencyMapper()
        
        package_name = mapper.get_package_name(module_name)
        
        # If DependencyMapper found a package name (not None), it's a known dependency
        # Allow installation attempt - the installer will verify if it's actually needed
        if package_name:
            logger.debug(f"[AUTO-INSTALL] Module '{module_name}' maps to package '{package_name}', allowing auto-install")
            return True
        else:
            logger.debug(f"[AUTO-INSTALL] Module '{module_name}' has no package mapping, skipping auto-install")
            
    except Exception as e:
        # If mapper fails, log and be conservative
        logger.debug(f"[AUTO-INSTALL] DependencyMapper failed for '{module_name}': {e}")
        pass
    
    return False

def _try_install_package(module_name: str) -> bool:
    """
    Try to install package for missing module.
    
    Tries all registered packages until one succeeds.
    
    Args:
        module_name: Module name that failed to import
        
    Returns:
        True if installation successful, False otherwise
    """
    # Try root package first
    root_package = module_name.split('.')[0]
    if root_package in _lazy_packages:
        try:
            logger.info(f"[AUTO-INSTALL] Trying root package {root_package} for module {module_name}")
            installer = LazyInstallerRegistry.get_instance(root_package)
            logger.info(f"[AUTO-INSTALL] Installer for {root_package}: {installer is not None}, enabled={installer.is_enabled() if installer else False}")
            
            if installer is None:
                logger.warning(f"[AUTO-INSTALL] Installer for {root_package} is None")
            elif not installer.is_enabled():
                logger.warning(f"[AUTO-INSTALL] Installer for {root_package} is disabled")
            else:
                logger.info(f"Auto-installing missing package for module: {module_name} (via {root_package})")
                logger.info(f"[AUTO-INSTALL] Calling install_and_import('{module_name}')")
                try:
                    module, success = installer.install_and_import(module_name)
                    logger.info(f"[AUTO-INSTALL] install_and_import returned: module={module is not None}, success={success}")
                    if success and module:
                        _installed_cache.add(module_name)
                        logger.info(f"[AUTO-INSTALL] Successfully installed and imported '{module_name}'")
                        return True
                    else:
                        logger.warning(f"[AUTO-INSTALL] install_and_import failed for '{module_name}': success={success}, module={module is not None}")
                except Exception as install_exc:
                    logger.error(f"[AUTO-INSTALL] install_and_import raised exception: {install_exc}", exc_info=True)
                    raise
        except Exception as e:
            logger.error(f"[AUTO-INSTALL] Exception installing via root package {root_package}: {e}", exc_info=True)
    
    # Try all registered packages (for dependencies like 'yaml' when 'xwsystem' is registered)
    for registered_package in _lazy_packages.keys():
        if registered_package == root_package:
            continue  # Already tried
        
        try:
            logger.debug(f"[AUTO-INSTALL] Trying to get installer for {registered_package}")
            installer = LazyInstallerRegistry.get_instance(registered_package)
            logger.debug(f"[AUTO-INSTALL] Installer retrieved: {installer is not None}")
            
            if installer is None:
                logger.warning(f"[AUTO-INSTALL] Installer for {registered_package} is None")
                continue
                
            if not installer.is_enabled():
                logger.warning(f"[AUTO-INSTALL] Installer for {registered_package} is disabled")
                continue
                
            logger.info(f"Auto-installing missing package for module: {module_name} (via {registered_package})")
            logger.info(f"[AUTO-INSTALL] Calling install_and_import('{module_name}')")
            try:
                module, success = installer.install_and_import(module_name)
                logger.info(f"[AUTO-INSTALL] install_and_import returned: module={module is not None}, success={success}")
            except Exception as install_exc:
                logger.error(f"[AUTO-INSTALL] install_and_import raised exception: {install_exc}", exc_info=True)
                raise
            
            if success and module:
                _installed_cache.add(module_name)
                logger.info(f"[AUTO-INSTALL] Successfully installed and imported '{module_name}'")
                return True
            else:
                logger.warning(f"[AUTO-INSTALL] install_and_import failed for '{module_name}': success={success}, module={module is not None}")
        except Exception as e:
            logger.error(f"[AUTO-INSTALL] Exception installing via {registered_package}: {e}", exc_info=True)
            continue
    
    logger.warning(f"[AUTO-INSTALL] Failed to install package for module '{module_name}' via all registered packages")
    return False

def _intercepting_import(name: str, globals=None, locals=None, fromlist=(), level=0):
    """
    Intercept ALL imports including module-level ones.
    
    This is the global builtins.__import__ replacement that catches
    ALL imports, including those at module level during package initialization.
    
    CRITICAL: Skip relative imports (level > 0) - they must use normal import path.
    Relative imports are package/module agnostic and should not be intercepted.
    
    CRITICAL: When fromlist is non-empty (e.g., "from module import Class"),
    Python's import machinery needs direct access to module attributes via getattr().
    We MUST return the actual module object without any wrapping.
    """
    # CRITICAL FIX: Handle relative imports (level > 0)
    # Relative imports like "from .common import" have level=1
    # We must use normal import BUT still enhance the module after import (package/module agnostic)
    if level > 0:
        result = _original_builtins_import(name, globals, locals, fromlist, level)
        # CRITICAL: Enhance modules imported via relative imports (package/module agnostic)
        # This ensures instance methods work on classes for ANY package/module structure
        if result and isinstance(result, ModuleType) and fromlist:
            try:
                for pkg_name in _lazy_packages.keys():
                    if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                        finder = _installed_hooks.get(pkg_name)
                        if finder:
                            finder._enhance_classes_with_class_methods(result)
                            break
            except Exception:
                pass
        return result
    
    # CRITICAL FIX: Handle fromlist imports specially
    # When fromlist is present (e.g., "from module import Class"),
    # Python needs direct access to module attributes via getattr(module, 'Class')
    # We MUST return the actual module without any wrapping or modification
    if fromlist:
        # Import partial module detector (lazy import to avoid circular dependency)
        try:
            from .partial_module_detector import (
                is_partially_initialized as _default_is_partially_initialized,
                mark_module_importing,
                unmark_module_importing,
                DetectionStrategy,
                PartialModuleDetector
            )
            # Allow strategy override via environment variable for testing
            strategy_name = os.environ.get('XWLAZY_PARTIAL_DETECTION_STRATEGY', 'hybrid')
            try:
                strategy = DetectionStrategy(strategy_name)
                detector = PartialModuleDetector(strategy)
                is_partially_initialized = lambda n, m: detector.is_partially_initialized(n, m)
            except (ValueError, AttributeError):
                # Use default detector (HYBRID strategy)
                is_partially_initialized = _default_is_partially_initialized
        except ImportError:
            # Fallback if detector not available
            def is_partially_initialized(name, mod):
                return False
            def mark_module_importing(name):
                pass
            def unmark_module_importing(name):
                pass
        
        # Mark this module as being imported (for tracking)
        mark_module_importing(name)
        
        try:
            # Fast path: already imported and in sys.modules
            # CRITICAL: For fromlist imports, we must be VERY conservative
            # Only return early if we're CERTAIN the module is fully initialized
            # and NOT currently being imported
            if name in sys.modules:
                module = sys.modules[name]
                # Ensure module is fully loaded (not a placeholder or lazy wrapper)
                # Check if it's a real ModuleType (not a proxy/wrapper)
                if isinstance(module, ModuleType):
                    # CRITICAL: Check if module is partially initialized
                    # We must NOT return a partially initialized module
                    # For fromlist imports, be extra conservative - only return if
                    # module is definitely fully loaded AND not currently importing
                    if not is_partially_initialized(name, module):
                        # Additional check: verify module has meaningful content
                        # (not just metadata attributes)
                        module_dict = getattr(module, '__dict__', {})
                        metadata_attrs = {'__name__', '__loader__', '__spec__', '__package__', '__file__', '__path__', '__cached__'}
                        content_attrs = set(module_dict.keys()) - metadata_attrs
                        
                        # Only return if module has actual content (classes, functions, etc.)
                        # OR if it's a namespace package (has __path__)
                        has_content = len(content_attrs) > 0
                        is_namespace = hasattr(module, '__path__')
                        
                        if has_content or is_namespace:
                            # Check if it's a placeholder by looking for common placeholder patterns
                            is_placeholder = (
                                hasattr(module, '__getattr__') and 
                                not hasattr(module, '__file__') and
                                not hasattr(module, '__path__')  # Namespace packages don't have __file__
                            )
                            if not is_placeholder:
                                # Module is fully loaded with content, return it directly
                                # CRITICAL FIX: Enhance classes before returning
                                try:
                                    # Find which package this module belongs to
                                    for pkg_name in _lazy_packages.keys():
                                        # Check if module name starts with package name or "exonware." + package name
                                        if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                                            finder = _installed_hooks.get(pkg_name)
                                            if finder:
                                                finder._enhance_classes_with_class_methods(module)
                                                break
                                except Exception:
                                    pass
                                unmark_module_importing(name)
                                return module
                    # Module is partially initialized or has no content - fall through to normal import
            # If it's a placeholder, partially initialized, or has no content, fall through to normal import
        finally:
            # Always unmark when done (even if exception occurs)
            unmark_module_importing(name)
        
        # For fromlist imports, use normal import path to ensure classes/functions
        # are accessible via getattr() - Python's import machinery handles extraction
        try:
            # Mark as importing before calling original import
            try:
                from .partial_module_detector import mark_module_importing, unmark_module_importing
                mark_module_importing(name)
            except ImportError:
                pass
            
            try:
                result = _original_builtins_import(name, globals, locals, fromlist, level)
                # Cache success but return actual module (no wrapping)
                _installed_cache.add(name)
                # CRITICAL FIX: Enhance classes in the module for class-level method access
                # This makes instance methods callable on classes (e.g., BsonSerializer.encode(data))
                if result and isinstance(result, ModuleType):
                    try:
                        # Find which package this module belongs to
                        for pkg_name in _lazy_packages.keys():
                            # Check if module name starts with package name or "exonware." + package name
                            if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                                finder = _installed_hooks.get(pkg_name)
                                if finder:
                                    finder._enhance_classes_with_class_methods(result)
                                    break
                    except Exception as e:
                        # Enhancement failed - don't break the import, but log for debugging
                        logger.debug(f"Enhancement failed for {name}: {e}", exc_info=True)
                        pass
                return result
            finally:
                # Always unmark when done
                try:
                    from .partial_module_detector import unmark_module_importing
                    unmark_module_importing(name)
                except ImportError:
                    pass
        except ImportError as e:
            # Only try auto-install if needed
            if _should_auto_install(name):
                try:
                    if _try_install_package(name):
                        # Retry import after installation - return actual module
                        result = _original_builtins_import(name, globals, locals, fromlist, level)
                        _installed_cache.add(name)
                        # CRITICAL FIX: Enhance classes in the module for class-level method access
                        if result and isinstance(result, ModuleType):
                            try:
                                # Find which package this module belongs to
                                for pkg_name in _lazy_packages.keys():
                                    # Check if module name starts with package name or "exonware." + package name
                                    if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                                        finder = _installed_hooks.get(pkg_name)
                                        if finder:
                                            finder._enhance_classes_with_class_methods(result)
                                            break
                            except Exception:
                                pass
                        return result
                except Exception:
                    # If installation fails, don't crash - just raise the original ImportError
                    pass
            
            # Installation failed or not applicable - cache failure (but limit cache size)
            if len(_failed_cache) < 1000:  # Prevent unbounded growth
                _failed_cache.add(name)
            raise
    
    # Fast path: cached as installed (but still enhance for fromlist)
    if name in _installed_cache:
        result = _original_builtins_import(name, globals, locals, fromlist, level)
        # CRITICAL: Enhance even cached modules for fromlist imports (package/module agnostic)
        if fromlist and result and isinstance(result, ModuleType):
            try:
                for pkg_name in _lazy_packages.keys():
                    if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                        finder = _installed_hooks.get(pkg_name)
                        if finder:
                            finder._enhance_classes_with_class_methods(result)
                            break
            except Exception:
                pass
        return result
    
    # Fast path: already imported (for non-fromlist imports)
    # CRITICAL: For fromlist imports, enhance even if module is cached
    if name in sys.modules:
        result = _original_builtins_import(name, globals, locals, fromlist, level)
        if fromlist:
            module = sys.modules.get(name)
            if module and isinstance(module, ModuleType):
                try:
                    for pkg_name in _lazy_packages.keys():
                        if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                            finder = _installed_hooks.get(pkg_name)
                            if finder:
                                finder._enhance_classes_with_class_methods(module)
                                break
                except Exception:
                    pass
        return result
    
    # Fast path: known failure
    if name in _failed_cache:
        raise ImportError(f"No module named '{name}'")
    
    # Fast path: skip stdlib/builtin modules (performance optimization)
    if name in sys.builtin_module_names:
        return _original_builtins_import(name, globals, locals, fromlist, level)
    
    # Skip private/internal modules (performance optimization)
    # But allow if it's a submodule of a registered package
    if name.startswith('_'):
        # Check if it's a submodule of a registered package
        root_package = name.split('.')[0]
        if root_package not in _lazy_packages:
            return _original_builtins_import(name, globals, locals, fromlist, level)
    
    # Skip test-related modules to avoid interfering with pytest
    if name.startswith(('pytest', '_pytest', 'pluggy', '_pluggy')):
        return _original_builtins_import(name, globals, locals, fromlist, level)
    
    # Skip debugging/profiling modules
    if name in ('tracemalloc', 'pdb', 'ipdb', 'debugpy', 'pydevd'):
        return _original_builtins_import(name, globals, locals, fromlist, level)
    
    try:
        # Try normal import first
        result = _original_builtins_import(name, globals, locals, fromlist, level)
        # Success - cache it
        _installed_cache.add(name)
        # CRITICAL FIX: Enhance classes for fromlist imports (package/module agnostic)
        # This ensures instance methods work on classes for ANY package/module structure
        if result and isinstance(result, ModuleType) and fromlist:
            try:
                for pkg_name in _lazy_packages.keys():
                    if name.startswith(pkg_name) or name.startswith(f"exonware.{pkg_name}"):
                        finder = _installed_hooks.get(pkg_name)
                        if finder:
                            finder._enhance_classes_with_class_methods(result)
                            break
            except Exception:
                pass
        return result
    except ImportError as e:
        # Check if this package should be auto-installed
        # ROOT CAUSE DEBUG: Log the exact import name and traceback to find where typos originate
        if any(typo in name for typo in ['contrrib', 'msgpackk', 'msgppack', 'mmsgpack']):
            import traceback
            logger.warning(
                f"[ROOT CAUSE] Typo detected in module name '{name}'. "
                f"ImportError: {e}. "
                f"Traceback:\n{''.join(traceback.format_stack()[-5:-1])}"
            )
        logger.debug(f"[AUTO-INSTALL] ImportError for '{name}': {e}")
        should_install = _should_auto_install(name)
        logger.debug(f"[AUTO-INSTALL] Should auto-install '{name}': {should_install}")
        
        if should_install:
            try:
                logger.info(f"[AUTO-INSTALL] Attempting to install package for '{name}'")
                if _try_install_package(name):
                    logger.info(f"[AUTO-INSTALL] Successfully installed package for '{name}', retrying import")
                    # Retry import after installation
                    try:
                        result = _original_builtins_import(name, globals, locals, fromlist, level)
                        _installed_cache.add(name)
                        logger.info(f"[AUTO-INSTALL] Successfully imported '{name}' after installation")
                        return result
                    except ImportError as retry_error:
                        logger.warning(f"[AUTO-INSTALL] Import still failed for '{name}' after installation: {retry_error}")
                        pass
                else:
                    logger.warning(f"[AUTO-INSTALL] Installation attempt returned False for '{name}'")
            except Exception as install_error:
                # If installation fails, log it but don't crash - just raise the original ImportError
                logger.error(f"[AUTO-INSTALL] Installation failed for '{name}': {install_error}", exc_info=True)
                pass
        else:
            logger.debug(f"[AUTO-INSTALL] Not auto-installing '{name}' (not eligible)")
        
        # Installation failed or not applicable - cache failure (but limit cache size)
        if len(_failed_cache) < 1000:  # Prevent unbounded growth
            _failed_cache.add(name)
        raise
    except Exception:
        # For any other exception, don't interfere - let it propagate
        # This prevents the hook from breaking system functionality
        raise

def install_global_import_hook() -> None:
    """
    Install global builtins.__import__ hook for auto-install.
    
    This hook intercepts ALL imports including module-level ones,
    enabling auto-installation for registered packages.
    """
    global _original_builtins_import, _global_import_hook_installed
    
    with _global_import_hook_lock:
        if _global_import_hook_installed:
            logger.debug("Global import hook already installed")
            return
        
        if _original_builtins_import is None:
            _original_builtins_import = builtins.__import__
        
        builtins.__import__ = _intercepting_import
        _global_import_hook_installed = True
        logger.info("✅ Global builtins.__import__ hook installed for auto-install")

def uninstall_global_import_hook() -> None:
    """
    Uninstall global builtins.__import__ hook.
    
    Restores original builtins.__import__.
    """
    global _original_builtins_import, _global_import_hook_installed
    
    with _global_import_hook_lock:
        if not _global_import_hook_installed:
            return
        
        if _original_builtins_import is not None:
            builtins.__import__ = _original_builtins_import
            _original_builtins_import = None
        
        _global_import_hook_installed = False
        logger.info("Global builtins.__import__ hook uninstalled")

def is_global_import_hook_installed() -> bool:
    """Check if global import hook is installed."""
    return _global_import_hook_installed

def clear_global_import_caches() -> None:
    """
    Clear global import hook caches (useful for testing).
    
    Clears both installed and failed caches.
    """
    global _installed_cache, _failed_cache
    with _global_import_hook_lock:
        _installed_cache.clear()
        _failed_cache.clear()
        logger.debug("Cleared global import hook caches")

def get_global_import_cache_stats() -> dict[str, Any]:
    """
    Get statistics about global import hook caches.
    
    Returns:
        Dict with cache sizes and hit/miss information
    """
    with _global_import_hook_lock:
        return {
            'installed_cache_size': len(_installed_cache),
            'failed_cache_size': len(_failed_cache),
            'registered_packages': list(_lazy_packages.keys()),
            'hook_installed': _global_import_hook_installed,
        }

# =============================================================================
# PREFIX TRIE (from prefix_trie.py)
# =============================================================================

class _PrefixTrie:
    """Trie data structure for prefix matching."""
    
    __slots__ = ("_root",)

    def __init__(self) -> None:
        self._root: dict[str, dict[str, Any]] = {}

    def add(self, prefix: str) -> None:
        """Add a prefix to the trie."""
        node = self._root
        for char in prefix:
            node = node.setdefault(char, {})
        node["_end"] = prefix

    def iter_matches(self, value: str) -> tuple[str, ...]:
        """Find all matching prefixes for a given value."""
        node = self._root
        matches: list[str] = []
        for char in value:
            end_value = node.get("_end")
            if end_value:
                matches.append(end_value)
            node = node.get(char)
            if node is None:
                break
        else:
            end_value = node.get("_end")
            if end_value:
                matches.append(end_value)
        return tuple(matches)

# =============================================================================
# WATCHED REGISTRY (from watched_registry.py)
# =============================================================================

class WatchedPrefixRegistry:
    """Maintain watched prefixes and provide fast trie-based membership checks."""

    __slots__ = (
        "_lock",
        "_prefix_refcounts",
        "_owner_map",
        "_prefixes",
        "_trie",
        "_dirty",
        "_root_refcounts",
        "_root_snapshot",
        "_root_snapshot_dirty",
    )

    def __init__(self, initial: Optional[list[str]] = None) -> None:
        self._lock = threading.RLock()
        self._prefix_refcounts: Counter[str] = Counter()
        self._owner_map: dict[str, set[str]] = {}
        self._prefixes: set[str] = set()
        self._trie = _PrefixTrie()
        self._dirty = False
        self._root_refcounts: Counter[str] = Counter()
        self._root_snapshot: set[str] = set()
        self._root_snapshot_dirty = False
        if initial:
            for prefix in initial:
                self._register_manual(prefix)

    def _register_manual(self, prefix: str) -> None:
        normalized = _normalize_prefix(prefix)
        if not normalized:
            return
        owner = "__manual__"
        owners = self._owner_map.setdefault(owner, set())
        if normalized in owners:
            return
        owners.add(normalized)
        self._add_prefix(normalized)

    def _add_prefix(self, prefix: str) -> None:
        if not prefix:
            return
        self._prefix_refcounts[prefix] += 1
        if self._prefix_refcounts[prefix] == 1:
            self._prefixes.add(prefix)
            self._dirty = True
            root = prefix.split('.', 1)[0]
            self._root_refcounts[root] += 1
            self._root_snapshot_dirty = True

    def _remove_prefix(self, prefix: str) -> None:
        if prefix not in self._prefix_refcounts:
            return
        self._prefix_refcounts[prefix] -= 1
        if self._prefix_refcounts[prefix] <= 0:
            self._prefix_refcounts.pop(prefix, None)
            self._prefixes.discard(prefix)
            self._dirty = True
            root = prefix.split('.', 1)[0]
            self._root_refcounts[root] -= 1
            if self._root_refcounts[root] <= 0:
                self._root_refcounts.pop(root, None)
            self._root_snapshot_dirty = True

    def _ensure_trie(self) -> None:
        if not self._dirty:
            return
        self._trie = _PrefixTrie()
        for prefix in self._prefixes:
            self._trie.add(prefix)
        self._dirty = False

    def add(self, prefix: str) -> None:
        normalized = _normalize_prefix(prefix)
        if not normalized:
            return
        with self._lock:
            self._register_manual(normalized)
    
    def is_empty(self) -> bool:
        with self._lock:
            return not self._prefixes

    def register_package(self, package_name: str, prefixes: Iterable[str]) -> None:
        owner_key = f"pkg::{package_name.lower()}"
        normalized = {_normalize_prefix(p) for p in prefixes if _normalize_prefix(p)}
        with self._lock:
            current = self._owner_map.get(owner_key, set())
            to_remove = current - normalized
            to_add = normalized - current

            for prefix in to_remove:
                self._remove_prefix(prefix)
            for prefix in to_add:
                self._add_prefix(prefix)

            if normalized:
                self._owner_map[owner_key] = normalized
            elif owner_key in self._owner_map:
                self._owner_map.pop(owner_key, None)

    def is_prefix_owned_by(self, package_name: str, prefix: str) -> bool:
        normalized = _normalize_prefix(prefix)
        owner_key = f"pkg::{package_name.lower()}"
        with self._lock:
            if normalized in self._owner_map.get("__manual__", set()):
                return True
            return normalized in self._owner_map.get(owner_key, set())

    def get_matching_prefixes(self, module_name: str) -> tuple[str, ...]:
        with self._lock:
            if not self._prefixes:
                return ()
            self._ensure_trie()
            return self._trie.iter_matches(module_name)

    def has_root(self, root_name: str) -> bool:
        snapshot = self._root_snapshot
        if not self._root_snapshot_dirty:
            return root_name in snapshot
        with self._lock:
            if self._root_snapshot_dirty:
                self._root_snapshot = set(self._root_refcounts.keys())
                self._root_snapshot_dirty = False
            return root_name in self._root_snapshot

# Global registry instance
_DEFAULT_WATCHED_PREFIXES = tuple(
    filter(
        None,
        os.environ.get(
            "XWLAZY_LAZY_PREFIXES",
            "",
        ).split(";"),
    )
)
_watched_registry = WatchedPrefixRegistry(list(_DEFAULT_WATCHED_PREFIXES))

def get_watched_registry() -> WatchedPrefixRegistry:
    """Get the global watched prefix registry."""
    return _watched_registry

# =============================================================================
# DEFERRED LOADER (from deferred_loader.py)
# =============================================================================

class _DeferredModuleLoader(importlib.abc.Loader):
    """Loader that simply returns a preconstructed module placeholder."""

    def __init__(self, module: ModuleType) -> None:
        self._module = module

    def create_module(self, spec):  # noqa: D401 - standard loader hook
        return self._module

    def exec_module(self, module):  # noqa: D401 - nothing to execute
        return None

# =============================================================================
# CACHE (from common.cache)
# =============================================================================

# MultiTierCache and BytecodeCache are now imported from ..common.cache

# =============================================================================
# PARALLEL UTILITIES (from parallel_utils.py)
# =============================================================================

class ParallelLoader:
    """Parallel module loader with smart dependency management."""
    
    def __init__(self, max_workers: Optional[int] = None):
        if max_workers is None:
            max_workers = min(os.cpu_count() or 4, 8)
        
        self._max_workers = max_workers
        self._executor: Optional[concurrent.futures.ThreadPoolExecutor] = None
        self._lock = threading.RLock()
        
    def _get_executor(self) -> concurrent.futures.ThreadPoolExecutor:
        """Get or create thread pool executor."""
        with self._lock:
            if self._executor is None:
                self._executor = concurrent.futures.ThreadPoolExecutor(
                    max_workers=self._max_workers,
                    thread_name_prefix="xwlazy-parallel"
                )
            return self._executor
    
    def load_modules_parallel(self, module_paths: list[str]) -> dict[str, Any]:
        """Load multiple modules in parallel."""
        executor = self._get_executor()
        results: dict[str, Any] = {}
        
        def _load_module(module_path: str) -> tuple[str, Any, Optional[Exception]]:
            try:
                module = importlib.import_module(module_path)
                return (module_path, module, None)
            except Exception as e:
                logger.debug(f"Failed to load {module_path} in parallel: {e}")
                return (module_path, None, e)
        
        futures = {executor.submit(_load_module, path): path for path in module_paths}
        
        for future in concurrent.futures.as_completed(futures):
            module_path, module, error = future.result()
            results[module_path] = (module, error)
        
        return results
    
    def load_modules_with_priority(
        self,
        module_paths: list[tuple[str, int]]
    ) -> dict[str, Any]:
        """Load modules in parallel with priority ordering."""
        sorted_modules = sorted(module_paths, key=lambda x: x[1], reverse=True)
        module_list = [path for path, _ in sorted_modules]
        return self.load_modules_parallel(module_list)
    
    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the executor."""
        with self._lock:
            if self._executor:
                self._executor.shutdown(wait=wait)
                self._executor = None

class DependencyGraph:
    """Manages module dependencies for optimal parallel loading."""
    
    def __init__(self):
        self._dependencies: dict[str, list[str]] = {}
        self._reverse_deps: dict[str, list[str]] = {}
        self._lock = threading.RLock()
    
    def add_dependency(self, module: str, depends_on: list[str]) -> None:
        """Add dependencies for a module."""
        with self._lock:
            self._dependencies[module] = depends_on
            for dep in depends_on:
                if dep not in self._reverse_deps:
                    self._reverse_deps[dep] = []
                if module not in self._reverse_deps[dep]:
                    self._reverse_deps[dep].append(module)
    
    def get_load_order(self, modules: list[str]) -> list[list[str]]:
        """Get optimal load order for parallel loading (topological sort levels)."""
        with self._lock:
            in_degree: dict[str, int] = {m: 0 for m in modules}
            for module, deps in self._dependencies.items():
                if module in modules:
                    for dep in deps:
                        if dep in modules:
                            in_degree[module] += 1
            
            levels: list[list[str]] = []
            remaining = set(modules)
            
            while remaining:
                current_level = [
                    m for m in remaining
                    if in_degree[m] == 0
                ]
                
                if not current_level:
                    current_level = list(remaining)
                
                levels.append(current_level)
                remaining -= set(current_level)
                
                for module in current_level:
                    for dependent in self._reverse_deps.get(module, []):
                        if dependent in remaining:
                            in_degree[dependent] = max(0, in_degree[dependent] - 1)
            
            return levels

# =============================================================================
# MODULE PATCHING (from module_patching.py)
# =============================================================================

_original_import_module = importlib.import_module

def _lazy_aware_import_module(name: str, package: Optional[str] = None) -> ModuleType:
    """Lazy-aware version of importlib.import_module."""
    if _is_import_in_progress(name):
        return _original_import_module(name, package)
    
    _mark_import_started(name)
    try:
        return _original_import_module(name, package)
    finally:
        _mark_import_finished(name)

def _patch_import_module() -> None:
    """
    Patch importlib.import_module to be lazy-aware.
    
    WARNING: This performs global monkey-patching that affects ALL code in the Python process.
    This can cause conflicts with other libraries. Use sys.meta_path hooks instead.
    
    This function is kept for backward compatibility but should be avoided in new code.
    """
    # DISABLED: Dangerous monkey-patching disabled by default
    logger.warning(
        "_patch_import_module called - Dangerous monkey-patching is DISABLED. "
        "Use sys.meta_path hooks (install_import_hook) instead."
    )
    return
    # Original code (disabled):
    # importlib.import_module = _lazy_aware_import_module
    # logger.debug("Patched importlib.import_module to be lazy-aware")

def _unpatch_import_module() -> None:
    """Restore original importlib.import_module."""
    importlib.import_module = _original_import_module
    logger.debug("Restored original importlib.import_module")

# =============================================================================
# ARCHIVE IMPORTS (from archive_imports.py)
# =============================================================================

_archive_path = None
_archive_added = False

def get_archive_path() -> Path:
    """Get the path to the _archive folder."""
    global _archive_path
    if _archive_path is None:
        current_file = Path(__file__)
        _archive_path = current_file.parent.parent.parent.parent.parent.parent / "_archive"
    return _archive_path

def ensure_archive_in_path() -> None:
    """Ensure the archive folder is in sys.path for imports."""
    global _archive_added
    if not _archive_added:
        archive_path = get_archive_path()
        archive_str = str(archive_path)
        if archive_str not in sys.path:
            sys.path.insert(0, archive_str)
        _archive_added = True

def import_from_archive(module_name: str):
    """Import a module from the archived lazy code."""
    ensure_archive_in_path()
    return __import__(module_name, fromlist=[''])

# =============================================================================
# BOOTSTRAP (from bootstrap.py)
# =============================================================================

def _env_enabled(env_value: Optional[str]) -> Optional[bool]:
    if not env_value:
        return None
    normalized = env_value.strip().lower()
    if normalized in ('true', '1', 'yes', 'on'):
        return True
    if normalized in ('false', '0', 'no', 'off'):
        return False
    return None

def bootstrap_lazy_mode(package_name: str) -> None:
    """Detect whether lazy mode should be enabled for ``package_name`` and bootstrap hooks."""
    package_name = package_name.lower()
    env_value = os.environ.get(f"{package_name.upper()}_LAZY_INSTALL")
    env_enabled = _env_enabled(env_value)
    enabled = env_enabled

    if enabled is None:
        from ..common.services.keyword_detection import _detect_lazy_installation
        enabled = _detect_lazy_installation(package_name)

    if not enabled:
        return

    from ..facade import config_package_lazy_install_enabled

    config_package_lazy_install_enabled(
        package_name,
        enabled=True,
        install_hook=True,
    )

def bootstrap_lazy_mode_deferred(package_name: str) -> None:
    """
    Schedule lazy mode bootstrap to run AFTER the calling package finishes importing.
    
    WARNING: This function performs dangerous global monkey-patching of __builtins__.__import__.
    This can cause conflicts with other libraries (gevent, greenlet, debuggers, etc.).
    Consider using sys.meta_path hooks instead (install_import_hook) which is safer.
    
    This function is kept for backward compatibility but should be avoided in new code.
    """
    # DISABLED: Dangerous monkey-patching disabled by default
    # Uncomment only if absolutely necessary and you understand the risks
    logger.warning(
        f"bootstrap_lazy_mode_deferred called for {package_name} - "
        "Dangerous monkey-patching is DISABLED. Use install_import_hook() instead."
    )
    return
    
    # Original code (disabled):
    # package_name_lower = package_name.lower()
    # package_module_name = f"exonware.{package_name_lower}"
    # original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__
    # ... (rest of dangerous code)

# =============================================================================
# LAZY LOADER (from loader.py)
# =============================================================================

class LazyLoader(AModuleHelper):
    """Thread-safe lazy loader for modules with caching."""
    
    def load_module(self, module_path: str = None) -> ModuleType:
        """Thread-safe module loading with caching."""
        if module_path is None:
            module_path = self._module_path
        
        if self._cached_module is not None:
            return self._cached_module
        
        with self._lock:
            if self._cached_module is not None:
                return self._cached_module
            
            if self._loading:
                raise ImportError(f"Circular import detected for {module_path}")
            
            try:
                self._loading = True
                logger.debug(f"Lazy loading module: {module_path}")
                
                self._cached_module = importlib.import_module(module_path)
                
                logger.debug(f"Successfully loaded: {module_path}")
                return self._cached_module
                
            except Exception as e:
                logger.error(f"Failed to load module {module_path}: {e}")
                raise ImportError(f"Failed to load {module_path}: {e}") from e
            finally:
                self._loading = False
    
    def unload_module(self, module_path: str) -> None:
        """Unload a module from cache."""
        with self._lock:
            if module_path == self._module_path:
                self._cached_module = None
    
    def is_loaded(self) -> bool:
        """Check if module is currently loaded."""
        return self._cached_module is not None
    
    def __getattr__(self, name: str) -> Any:
        """Get attribute from lazily loaded module."""
        module = self.load_module()
        try:
            return getattr(module, name)
        except AttributeError:
            raise AttributeError(
                f"module '{self._module_path}' has no attribute '{name}'"
            )
    
    def __dir__(self) -> list:
        """Return available attributes from loaded module."""
        module = self.load_module()
        return dir(module)

# =============================================================================
# LAZY MODULE REGISTRY (from registry.py)
# =============================================================================

class LazyModuleRegistry:
    """Registry for managing lazy-loaded modules with performance tracking."""
    
    __slots__ = ('_modules', '_load_times', '_lock', '_access_counts')
    
    def __init__(self):
        self._modules: dict[str, LazyLoader] = {}
        self._load_times: dict[str, float] = {}
        self._access_counts: dict[str, int] = {}
        self._lock = threading.RLock()
    
    def register_module(self, name: str, module_path: str) -> None:
        """Register a module for lazy loading."""
        with self._lock:
            if name in self._modules:
                logger.warning(f"Module '{name}' already registered, overwriting")
            
            self._modules[name] = LazyLoader(module_path)
            self._access_counts[name] = 0
            logger.debug(f"Registered lazy module: {name} -> {module_path}")
    
    def get_module(self, name: str) -> LazyLoader:
        """Get a lazy-loaded module."""
        with self._lock:
            if name not in self._modules:
                raise KeyError(f"Module '{name}' not registered")
            
            self._access_counts[name] += 1
            return self._modules[name]
    
    def preload_frequently_used(self, threshold: int = 5) -> None:
        """Preload modules that are accessed frequently."""
        with self._lock:
            for name, count in self._access_counts.items():
                if count >= threshold:
                    try:
                        start_time = time.time()
                        _ = self._modules[name].load_module()
                        self._load_times[name] = time.time() - start_time
                        log_event("hook", logger.info, f"Preloaded frequently used module: {name}")
                    except Exception as e:
                        logger.warning(f"Failed to preload {name}: {e}")
    
    def get_stats(self) -> dict[str, Any]:
        """Get loading statistics."""
        with self._lock:
            loaded_count = sum(
                1 for loader in self._modules.values() 
                if loader.is_loaded()
            )
            
            return {
                'total_registered': len(self._modules),
                'loaded_count': loaded_count,
                'unloaded_count': len(self._modules) - loaded_count,
                'access_counts': self._access_counts.copy(),
                'load_times': self._load_times.copy(),
            }
    
    def clear_cache(self) -> None:
        """Clear all cached modules."""
        with self._lock:
            for name, loader in self._modules.items():
                loader.unload_module(loader._module_path)
            log_event("config", logger.info, "Cleared all cached modules")

# =============================================================================
# LAZY IMPORTER (from importer.py)
# =============================================================================

class LazyImporter:
    """
    Lazy importer that defers heavy module imports until first access.
    
    Supports multiple load modes: NONE, AUTO, PRELOAD, BACKGROUND, CACHED,
    TURBO, ADAPTIVE, HYPERPARALLEL, STREAMING, ULTRA, INTELLIGENT.
    
    ARCHITECTURAL NOTE: This class implements many modes for what should be a simple
    lazy loading mechanism. Modes like TURBO, ULTRA, and HYPERPARALLEL add significant
    complexity and may introduce concurrency issues with Python's import lock.
    Consider simplifying to just Lazy/Eager modes in future refactoring.
    """
    
    __slots__ = (
        '_enabled', '_load_mode', '_lazy_modules', '_loaded_modules', '_lock',
        '_access_counts', '_background_tasks', '_async_loop',
        '_multi_tier_cache', '_bytecode_cache', '_adaptive_learner',
        '_parallel_loader', '_dependency_graph', '_load_times',
        '_intelligent_selector', '_effective_mode', '_effective_install_mode'
    )
    
    def __init__(self):
        """Initialize lazy importer."""
        self._enabled = False
        self._load_mode = LazyLoadMode.NONE
        self._lazy_modules: dict[str, str] = {}
        self._loaded_modules: dict[str, ModuleType] = {}
        self._access_counts: dict[str, int] = {}
        self._load_times: dict[str, float] = {}
        self._background_tasks: dict[str, asyncio.Task] = {}
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Superior mode components
        self._multi_tier_cache: Optional[MultiTierCache] = None
        self._bytecode_cache: Optional[BytecodeCache] = None
        self._adaptive_learner: Optional[AdaptiveLearner] = None
        self._parallel_loader: Optional[ParallelLoader] = None
        self._dependency_graph: Optional[DependencyGraph] = None
        self._intelligent_selector: Optional[IntelligentModeSelector] = None
        
        # Effective modes (for INTELLIGENT mode)
        self._effective_mode: Optional[LazyLoadMode] = None
        self._effective_install_mode = None
        
        self._lock = threading.RLock()
    
    def _ensure_async_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure async event loop is running for background loading."""
        if self._async_loop is not None and self._async_loop.is_running():
            return self._async_loop
        
        with self._lock:
            if self._async_loop is None or not self._async_loop.is_running():
                loop_ready = threading.Event()
                
                def _run_loop():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    self._async_loop = loop
                    loop_ready.set()
                    loop.run_forever()
                
                thread = threading.Thread(target=_run_loop, daemon=True, name="xwlazy-loader-async")
                thread.start()
                
                if not loop_ready.wait(timeout=5.0):
                    raise RuntimeError("Failed to start async loop for lazy loader")
        
        return self._async_loop
    
    def enable(self, load_mode: LazyLoadMode = LazyLoadMode.AUTO) -> None:
        """Enable lazy imports with specified load mode."""
        with self._lock:
            self._enabled = True
            self._load_mode = load_mode
            
            # Initialize superior mode components
            if load_mode in (LazyLoadMode.TURBO, LazyLoadMode.ULTRA):
                self._multi_tier_cache = MultiTierCache(l1_size=1000, enable_l3=True)
                self._bytecode_cache = BytecodeCache()
            
            if load_mode == LazyLoadMode.ADAPTIVE:
                self._adaptive_learner = AdaptiveLearner()
                self._multi_tier_cache = MultiTierCache(l1_size=1000, enable_l3=True)
            
            if load_mode == LazyLoadMode.HYPERPARALLEL:
                max_workers = min(os.cpu_count() or 4, 8)
                self._parallel_loader = ParallelLoader(max_workers=max_workers)
                self._dependency_graph = DependencyGraph()
            
            if load_mode == LazyLoadMode.STREAMING:
                self._ensure_async_loop()
            
            if load_mode == LazyLoadMode.ULTRA:
                # ULTRA combines all optimizations
                if self._multi_tier_cache is None:
                    self._multi_tier_cache = MultiTierCache(l1_size=2000, enable_l3=True)
                if self._bytecode_cache is None:
                    self._bytecode_cache = BytecodeCache()
                if self._adaptive_learner is None:
                    self._adaptive_learner = AdaptiveLearner()
                if self._parallel_loader is None:
                    self._parallel_loader = ParallelLoader(max_workers=min(os.cpu_count() or 4, 8))
                if self._dependency_graph is None:
                    self._dependency_graph = DependencyGraph()
                self._ensure_async_loop()
            
            # INTELLIGENT mode: Initialize selector and determine initial mode
            if load_mode == LazyLoadMode.INTELLIGENT:
                self._intelligent_selector = IntelligentModeSelector()
                # Detect initial load level and get optimal mode
                initial_level = self._intelligent_selector.detect_load_level()
                self._effective_mode, self._effective_install_mode = self._intelligent_selector.get_optimal_mode(initial_level)
                logger.info(f"INTELLIGENT mode initialized: {initial_level.value} -> {self._effective_mode.value} + {self._effective_install_mode.value}")
                # Enable the effective mode recursively
                self.enable(self._effective_mode)
                return  # Early return, effective mode is already enabled
            
            # For PRELOAD/TURBO/ULTRA modes, preload modules
            if load_mode in (LazyLoadMode.PRELOAD, LazyLoadMode.TURBO, LazyLoadMode.ULTRA):
                self._preload_all_modules()
            # For BACKGROUND/STREAMING modes, ensure async loop is ready
            elif load_mode in (LazyLoadMode.BACKGROUND, LazyLoadMode.STREAMING):
                self._ensure_async_loop()
            
            log_event("config", logger.info, f"Lazy imports enabled (mode: {load_mode.value})")
    
    def disable(self) -> None:
        """Disable lazy imports."""
        with self._lock:
            self._enabled = False
            
            # Cleanup cache resources
            if self._multi_tier_cache:
                self._multi_tier_cache.shutdown()
            
            log_event("config", logger.info, "Lazy imports disabled")
    
    def is_enabled(self) -> bool:
        """Check if lazy imports are enabled."""
        return self._enabled
    
    def register_lazy_module(self, module_name: str, module_path: str = None) -> None:
        """Register a module for lazy loading."""
        with self._lock:
            if module_path is None:
                module_path = module_name
            
            self._lazy_modules[module_name] = module_path
            self._access_counts[module_name] = 0
            logger.debug(f"Registered lazy module: {module_name} -> {module_path}")
    
    async def _background_load_module(self, module_name: str, module_path: str) -> ModuleType:
        """Load module in background thread."""
        try:
            actual_module = importlib.import_module(module_path)
            with self._lock:
                self._loaded_modules[module_name] = actual_module
                self._access_counts[module_name] += 1
            logger.debug(f"Background loaded module: {module_name}")
            return actual_module
        except ImportError as e:
            logger.error(f"Failed to background load {module_name}: {e}")
            raise
    
    def _preload_all_modules(self) -> None:
        """Preload all registered modules using appropriate strategy based on mode."""
        if not self._lazy_modules:
            return
        
        with self._lock:
            modules_to_load = [
                (name, path) for name, path in self._lazy_modules.items()
                if name not in self._loaded_modules
            ]
        
        if not modules_to_load:
            return
        
        # HYPERPARALLEL/ULTRA: Use thread pool executor
        if self._load_mode in (LazyLoadMode.HYPERPARALLEL, LazyLoadMode.ULTRA) and self._parallel_loader:
            module_paths = [path for _, path in modules_to_load]
            results = self._parallel_loader.load_modules_parallel(module_paths)
            
            with self._lock:
                for (name, path), (module, error) in zip(modules_to_load, results.items()):
                    if module is not None:
                        self._loaded_modules[name] = module
                        self._access_counts[name] = 0
                        if self._adaptive_learner:
                            self._adaptive_learner.record_import(name, 0.0)
            
            log_event("hook", logger.info, f"Parallel preloaded {len([r for r in results.values() if r[0] is not None])} modules")
            return
        
        # TURBO/ULTRA: Preload with predictive caching
        if self._load_mode in (LazyLoadMode.TURBO, LazyLoadMode.ULTRA) and self._multi_tier_cache:
            # Get predictive modules to prioritize
            predictive_keys = self._multi_tier_cache.get_predictive_keys(limit=10)
            priority_modules = [(name, path) for name, path in modules_to_load if name in predictive_keys]
            normal_modules = [(name, path) for name, path in modules_to_load if name not in predictive_keys]
            modules_to_load = priority_modules + normal_modules
        
        # ADAPTIVE: Preload based on learned patterns
        if self._load_mode == LazyLoadMode.ADAPTIVE and self._adaptive_learner:
            priority_modules = self._adaptive_learner.get_priority_modules(limit=10)
            priority_list = [(name, path) for name, path in modules_to_load if name in priority_modules]
            normal_list = [(name, path) for name, path in modules_to_load if name not in priority_modules]
            modules_to_load = priority_list + normal_list
        
        # Default: Use asyncio for parallel loading
        loop = self._ensure_async_loop()
        
        async def _preload_all():
            tasks = [
                self._background_load_module(name, path)
                for name, path in modules_to_load
            ]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                log_event("hook", logger.info, f"Preloaded {len(tasks)} modules")
        
        asyncio.run_coroutine_threadsafe(_preload_all(), loop)
    
    def import_module(self, module_name: str, package_name: str = None) -> Any:
        """Import a module with lazy loading."""
        start_time = time.time()
        
        # Fast path: Check if already in sys.modules (lock-free read)
        if module_name in sys.modules:
            # Lock-free check first
            if module_name not in self._loaded_modules:
                with self._lock:
                    # Double-check after acquiring lock
                    if module_name not in self._loaded_modules:
                        self._loaded_modules[module_name] = sys.modules[module_name]
            # Update access count (requires lock)
            with self._lock:
                self._access_counts[module_name] = self._access_counts.get(module_name, 0) + 1
                load_time = time.time() - start_time
                if self._adaptive_learner:
                    self._adaptive_learner.record_import(module_name, load_time)
                if self._load_mode == LazyLoadMode.INTELLIGENT:
                    self._total_import_time = getattr(self, '_total_import_time', 0.0) + load_time
            return sys.modules[module_name]
        
        # Fast path: Check if already loaded (lock-free read)
        if module_name in self._loaded_modules:
            with self._lock:
                # Double-check and update
                if module_name in self._loaded_modules:
                    self._access_counts[module_name] = self._access_counts.get(module_name, 0) + 1
                    if self._adaptive_learner:
                        self._adaptive_learner.record_import(module_name, 0.0)
                    return self._loaded_modules[module_name]
        
        # Check enabled state and get module path (requires lock)
        with self._lock:
            if not self._enabled or self._load_mode == LazyLoadMode.NONE:
                return importlib.import_module(module_name)
            
            if module_name in self._lazy_modules:
                module_path = self._lazy_modules[module_name]
            else:
                return importlib.import_module(module_name)
            
            # Update total import time for intelligent mode (initialization)
            if self._load_mode == LazyLoadMode.INTELLIGENT:
                if not hasattr(self, '_total_import_time'):
                    self._total_import_time = 0.0
        
        # INTELLIGENT mode: Check if mode switch is needed and determine effective mode
        effective_load_mode = self._load_mode
        if self._load_mode == LazyLoadMode.INTELLIGENT and self._intelligent_selector:
            # Throttle load level detection (cache for 0.1s to avoid excessive checks)
            current_time = time.time()
            last_check = getattr(self, '_last_load_level_check', 0.0)
            check_interval = 0.1  # 100ms throttle
            
            if current_time - last_check >= check_interval:
                # Fast path: lock-free reads for stats
                module_count = len(self._loaded_modules)  # Dict read is thread-safe
                total_import_time = getattr(self, '_total_import_time', 0.0)
                import_count = sum(self._access_counts.values())  # Dict read is thread-safe
                
                # Cache psutil import and memory check (only check every 0.5s)
                last_memory_check = getattr(self, '_last_memory_check', 0.0)
                memory_mb = getattr(self, '_cached_memory_mb', 0.0)
                
                if current_time - last_memory_check >= 0.5:
                    try:
                        import psutil
                        process = psutil.Process()
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        self._cached_memory_mb = memory_mb
                        self._last_memory_check = current_time
                    except Exception:
                        memory_mb = 0.0
                
                # Detect current load level (lock-free)
                detected_level = self._intelligent_selector.detect_load_level(
                    module_count=module_count,
                    total_import_time=total_import_time,
                    import_count=import_count,
                    memory_usage_mb=memory_mb
                )
                
                # Check if mode switch is needed (requires lock for write)
                current_mode_tuple = (self._effective_mode or self._load_mode, self._effective_install_mode)
                if self._intelligent_selector.should_switch_mode(current_mode_tuple, detected_level):
                    optimal_load, optimal_install = self._intelligent_selector.get_optimal_mode(detected_level)
                    if optimal_load != self._effective_mode or optimal_install != self._effective_install_mode:
                        with self._lock:  # Only lock for mode switch
                            if optimal_load != self._effective_mode or optimal_install != self._effective_install_mode:
                                logger.info(f"INTELLIGENT mode switching: {detected_level.value} -> {optimal_load.value} + {optimal_install.value}")
                                self._effective_mode = optimal_load
                                self._effective_install_mode = optimal_install
                                # Switch to optimal mode (re-enable with new mode)
                                self.enable(optimal_load)
                
                self._last_load_level_check = current_time
            
            # Use effective mode for processing
            effective_load_mode = self._effective_mode or self._load_mode
        
        # Use effective mode for all checks
        check_mode = effective_load_mode
        
        # TURBO/ULTRA: Check multi-tier cache first
        if check_mode in (LazyLoadMode.TURBO, LazyLoadMode.ULTRA) and self._multi_tier_cache:
            cached_module = self._multi_tier_cache.get(module_name)
            if cached_module is not None:
                with self._lock:
                    self._loaded_modules[module_name] = cached_module
                    self._access_counts[module_name] += 1
                    self._load_times[module_name] = time.time() - start_time
                    if self._adaptive_learner:
                        self._adaptive_learner.record_import(module_name, self._load_times[module_name])
                return cached_module
        
        # ADAPTIVE: Check cache and predict next imports
        if check_mode == LazyLoadMode.ADAPTIVE:
            if self._multi_tier_cache:
                cached_module = self._multi_tier_cache.get(module_name)
                if cached_module is not None:
                    with self._lock:
                        self._loaded_modules[module_name] = cached_module
                        self._access_counts[module_name] += 1
                        load_time = time.time() - start_time
                        self._load_times[module_name] = load_time
                        if self._adaptive_learner:
                            self._adaptive_learner.record_import(module_name, load_time)
                    
                    # Predict and preload next likely imports
                    if self._adaptive_learner:
                        next_imports = self._adaptive_learner.predict_next_imports(module_name, limit=3)
                        self._preload_predictive_modules(next_imports)
                    
                    return cached_module
            
            # Record import for learning
            with self._lock:
                if self._adaptive_learner:
                    # Will be updated after load
                    pass
        
        # HYPERPARALLEL: Use parallel loading
        if check_mode == LazyLoadMode.HYPERPARALLEL and self._parallel_loader:
            results = self._parallel_loader.load_modules_parallel([module_path])
            module, error = results.get(module_path, (None, None))
            if module is not None:
                with self._lock:
                    self._loaded_modules[module_name] = module
                    self._access_counts[module_name] += 1
                    self._load_times[module_name] = time.time() - start_time
                return module
            elif error:
                raise error
        
        # STREAMING: Load asynchronously in background
        if check_mode == LazyLoadMode.STREAMING:
            return self._streaming_load(module_name, module_path)
        
        # BACKGROUND mode: Load in background, return placeholder
        if check_mode == LazyLoadMode.BACKGROUND:
            return self._background_placeholder_load(module_name, module_path)
        
        # TURBO/ULTRA: Load with bytecode cache
        actual_module = None
        if check_mode in (LazyLoadMode.TURBO, LazyLoadMode.ULTRA) and self._bytecode_cache:
            # Try to load from bytecode cache first
            bytecode = self._bytecode_cache.get_cached_bytecode(module_path)
            if bytecode is not None:
                try:
                    # Load from bytecode
                    code = compile(bytecode, f"<cached {module_path}>", "exec")
                    actual_module = importlib.import_module(module_path)
                except Exception as e:
                    logger.debug(f"Failed to load from bytecode cache: {e}")
        
        # Load module (standard or cached)
        if actual_module is None:
            try:
                actual_module = importlib.import_module(module_path)
                
                # Cache bytecode for TURBO/ULTRA
                if check_mode in (LazyLoadMode.TURBO, LazyLoadMode.ULTRA) and self._bytecode_cache:
                    try:
                        # Get compiled bytecode from module
                        if hasattr(actual_module, '__file__') and actual_module.__file__:
                            pyc_path = actual_module.__file__.replace('.py', '.pyc')
                            if os.path.exists(pyc_path):
                                with open(pyc_path, 'rb') as f:
                                    f.seek(16)  # Skip header
                                    bytecode = f.read()
                                    self._bytecode_cache.cache_bytecode(module_path, bytecode)
                    except Exception as e:
                        logger.debug(f"Failed to cache bytecode: {e}")
            except ImportError as e:
                logger.error(f"Failed to lazy load {module_name}: {e}")
                raise
        
        load_time = time.time() - start_time
        
        with self._lock:
            self._loaded_modules[module_name] = actual_module
            self._access_counts[module_name] += 1
            self._load_times[module_name] = load_time
            
            # Update total import time for intelligent mode
            if self._load_mode == LazyLoadMode.INTELLIGENT:
                self._total_import_time = getattr(self, '_total_import_time', 0.0) + load_time
            
            # Cache in multi-tier cache for TURBO/ULTRA/ADAPTIVE
            if self._multi_tier_cache:
                self._multi_tier_cache.set(module_name, actual_module)
            
            # Record for adaptive learning
            if self._adaptive_learner:
                self._adaptive_learner.record_import(module_name, load_time)
            
            logger.debug(f"Lazy loaded module: {module_name} ({load_time*1000:.2f}ms)")
        
        return actual_module
    
    def _streaming_load(self, module_name: str, module_path: str) -> ModuleType:
        """Load module asynchronously with streaming."""
        if module_name not in self._background_tasks or self._background_tasks[module_name].done():
            loop = self._ensure_async_loop()
            task = asyncio.run_coroutine_threadsafe(
                self._background_load_module(module_name, module_path),
                loop
            )
            self._background_tasks[module_name] = task
        
        # Return placeholder that streams
        placeholder = ModuleType(module_name)
        placeholder.__path__ = []
        placeholder.__package__ = module_name
        
        def _streaming_getattr(name):
            task = self._background_tasks.get(module_name)
            if task and not task.done():
                # Non-blocking check with short timeout
                try:
                    task.result(timeout=0.01)  # Very short timeout for streaming
                except Exception:
                    pass  # Still loading, continue
            
            # Check if loaded now
            with self._lock:
                if module_name in self._loaded_modules:
                    return getattr(self._loaded_modules[module_name], name)
            
            # Still loading, wait for completion
            if task and not task.done():
                task.result(timeout=10.0)
            
            with self._lock:
                if module_name in self._loaded_modules:
                    return getattr(self._loaded_modules[module_name], name)
            raise AttributeError(f"module '{module_name}' has no attribute '{name}'")
        
        placeholder.__getattr__ = _streaming_getattr  # type: ignore[attr-defined]
        return placeholder
    
    def _background_placeholder_load(self, module_name: str, module_path: str) -> ModuleType:
        """Load module in background, return placeholder."""
        if module_name not in self._background_tasks or self._background_tasks[module_name].done():
            loop = self._ensure_async_loop()
            task = asyncio.run_coroutine_threadsafe(
                self._background_load_module(module_name, module_path),
                loop
            )
            self._background_tasks[module_name] = task
        
        # Return placeholder module that will be replaced when loaded
        placeholder = ModuleType(module_name)
        placeholder.__path__ = []
        placeholder.__package__ = module_name
        
        def _getattr(name):
            # Wait for background load to complete
            task = self._background_tasks.get(module_name)
            if task and not task.done():
                task.result(timeout=10.0)  # Wait up to 10 seconds
            with self._lock:
                if module_name in self._loaded_modules:
                    return getattr(self._loaded_modules[module_name], name)
            raise AttributeError(f"module '{module_name}' has no attribute '{name}'")
        
        placeholder.__getattr__ = _getattr  # type: ignore[attr-defined]
        return placeholder
    
    def _preload_predictive_modules(self, module_names: list) -> None:
        """Preload modules predicted to be needed soon."""
        if not module_names:
            return
        
        with self._lock:
            modules_to_preload = [
                (name, self._lazy_modules[name])
                for name in module_names
                if name in self._lazy_modules and name not in self._loaded_modules
            ]
        
        if not modules_to_preload:
            return
        
        # Preload in background
        loop = self._ensure_async_loop()
        
        async def _preload_predictive():
            tasks = [
                self._background_load_module(name, path)
                for name, path in modules_to_preload
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
        
        asyncio.run_coroutine_threadsafe(_preload_predictive(), loop)
    
    def preload_module(self, module_name: str) -> bool:
        """Preload a registered lazy module."""
        with self._lock:
            if module_name not in self._lazy_modules:
                logger.warning(f"Module {module_name} not registered for lazy loading")
                return False
            
            try:
                self.import_module(module_name)
                log_event("hook", logger.info, f"Preloaded module: {module_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to preload {module_name}: {e}")
                return False
    
    def get_stats(self) -> dict[str, Any]:
        """Get lazy import statistics."""
        with self._lock:
            return {
                'enabled': self._enabled,
                'registered_modules': list(self._lazy_modules.keys()),
                'loaded_modules': list(self._loaded_modules.keys()),
                'access_counts': self._access_counts.copy(),
                'total_registered': len(self._lazy_modules),
                'total_loaded': len(self._loaded_modules)
            }

# =============================================================================
# IMPORT HOOK (from import_hook.py)
# =============================================================================

class LazyImportHook(AModuleHelper):
    """
    Import hook that intercepts ImportError and auto-installs packages.
    Performance optimized with zero overhead for successful imports.
    """
    
    __slots__ = AModuleHelper.__slots__
    
    def handle_import_error(self, module_name: str) -> Optional[Any]:
        """Handle ImportError by attempting to install and re-import."""
        if not self._enabled:
            return None
        
        try:
            # Deferred import to avoid circular dependency
            from ..facade import lazy_import_with_install
            module, success = lazy_import_with_install(
                module_name, 
                installer_package=self._package_name
            )
            return module if success else None
        except Exception:
            return None
    
    def install_hook(self) -> None:
        """Install the import hook into sys.meta_path."""
        install_import_hook(self._package_name)
    
    def uninstall_hook(self) -> None:
        """Uninstall the import hook from sys.meta_path."""
        uninstall_import_hook(self._package_name)
    
    def is_installed(self) -> bool:
        """Check if hook is installed."""
        return is_import_hook_installed(self._package_name)

# =============================================================================
# META PATH FINDER (from meta_path_finder.py)
# =============================================================================

# Wrapped class cache
_WRAPPED_CLASS_CACHE: dict[str, set[str]] = defaultdict(set)
_wrapped_cache_lock = threading.RLock()

# Default lazy methods
_DEFAULT_LAZY_METHODS = tuple(
    filter(
        None,
        os.environ.get("XWLAZY_LAZY_METHODS", "").split(","),
    )
)

# Lazy prefix method registry
_lazy_prefix_method_registry: dict[str, tuple[str, ...]] = {}

# Package class hints
_package_class_hints: dict[str, tuple[str, ...]] = {}
_class_hint_lock = threading.RLock()

def _set_package_class_hints(package_name: str, hints: Iterable[str]) -> None:
    """Set class hints for a package."""
    normalized: tuple[str, ...] = tuple(
        OrderedDict((hint.lower(), None) for hint in hints if hint).keys()  # type: ignore[arg-type]
    )
    with _class_hint_lock:
        if normalized:
            _package_class_hints[package_name] = normalized
        else:
            _package_class_hints.pop(package_name, None)

def _get_package_class_hints(package_name: str) -> tuple[str, ...]:
    """Get class hints for a package."""
    with _class_hint_lock:
        return _package_class_hints.get(package_name, ())

def _clear_all_package_class_hints() -> None:
    """Clear all package class hints."""
    with _class_hint_lock:
        _package_class_hints.clear()

def register_lazy_module_methods(prefix: str, methods: tuple[str, ...]) -> None:
    """Register method names to enhance for all classes under a module prefix."""
    prefix = prefix.strip()
    if not prefix:
        return
    
    if not prefix.endswith("."):
        prefix += "."
    
    _lazy_prefix_method_registry[prefix] = methods
    log_event("config", logger.info, f"Registered lazy module methods for prefix {prefix}: {methods}")

def _spec_for_existing_module(
    fullname: str,
    module: ModuleType,
    original_spec: Optional[importlib.machinery.ModuleSpec] = None,
) -> importlib.machinery.ModuleSpec:
    """Build a ModuleSpec whose loader simply returns an already-initialized module."""
    loader = _DeferredModuleLoader(module)
    spec = importlib.machinery.ModuleSpec(fullname, loader)
    if original_spec and original_spec.submodule_search_locations is not None:
        locations = list(original_spec.submodule_search_locations)
        spec.submodule_search_locations = locations
        if hasattr(module, "__path__"):
            module.__path__ = locations
    module.__loader__ = loader
    module.__spec__ = spec
    return spec

class LazyMetaPathFinder:
    """
    Custom meta path finder that intercepts failed imports.
    Performance optimized - only triggers when import would fail anyway.
    """
    
    __slots__ = ('_package_name', '_enabled')
    
    def __init__(self, package_name: str = 'default'):
        """Initialize meta path finder."""
        self._package_name = package_name
        self._enabled = True

    def _build_async_placeholder(
        self,
        fullname: str,
        installer: LazyInstaller,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        """Create and register a deferred module placeholder for async installs."""
        handle = installer.ensure_async_install(fullname)
        if handle is None:
            return None

        missing = ModuleNotFoundError(f"No module named '{fullname}'")
        deferred = DeferredImportError(fullname, missing, self._package_name, async_handle=handle)

        module = ModuleType(fullname)
        loader = _DeferredModuleLoader(module)

        def _resolve_real_module():
            real_module = deferred._try_install_and_import()
            sys.modules[fullname] = real_module
            module.__dict__.clear()
            module.__dict__.update(real_module.__dict__)
            module.__loader__ = getattr(real_module, "__loader__", loader)
            module.__spec__ = getattr(real_module, "__spec__", None)
            module.__path__ = getattr(real_module, "__path__", getattr(module, "__path__", []))
            module.__class__ = real_module.__class__
            try:
                spec_obj = getattr(real_module, "__spec__", None) or importlib.util.find_spec(fullname)
                if spec_obj is not None:
                    _spec_cache_put(fullname, spec_obj)
            except (ValueError, AttributeError, ImportError):
                pass
            return real_module

        def _module_getattr(name):
            real = _resolve_real_module()
            if name in module.__dict__:
                return module.__dict__[name]
            return getattr(real, name)

        def _module_dir():
            try:
                real = _resolve_real_module()
                return dir(real)
            except Exception:
                return []

        module.__getattr__ = _module_getattr  # type: ignore[attr-defined]
        module.__dir__ = _module_dir  # type: ignore[attr-defined]
        module.__loader__ = loader
        module.__package__ = fullname
        module.__path__ = []

        spec = importlib.machinery.ModuleSpec(fullname, loader)
        spec.submodule_search_locations = []
        module.__spec__ = spec

        sys.modules[fullname] = module
        log_event("hook", logger.info, f"⏳ [HOOK] Deferred import placeholder created for '{fullname}'")
        return spec
    
    def find_module(self, fullname: str, path: Optional[str] = None):
        """Find module - returns None to let standard import continue."""
        return None
    
    def find_spec(self, fullname: str, path: Optional[str] = None, target=None):
        """
        Find module spec - intercepts imports to enable two-stage lazy loading.
        
        PERFORMANCE: Optimized for zero overhead on successful imports.
        """
        # CRITICAL: Check installing state FIRST to prevent recursion during installation
        if getattr(_installing_state, 'active', False):
            logger.debug(f"[HOOK] Installation in progress, skipping {fullname} to prevent recursion")
            return None
        
        # CRITICAL: Check if we're checking installation status to prevent infinite recursion
        if _is_checking_installation():
            logger.debug(f"[HOOK] Checking installation status, bypassing lazy finder for {fullname} to prevent recursion")
            return None
        
        # Fast path 1: Hook disabled
        if not self._enabled:
            return None
        
        # Fast path 2: Module already loaded - wrap it if needed
        if fullname in sys.modules:
            module = sys.modules[fullname]
            # Wrap classes in already-loaded modules to ensure auto-instantiation works
            if isinstance(module, ModuleType) and not getattr(module, '_xwlazy_wrapped', False):
                try:
                    self._wrap_classes_for_auto_instantiation(module)
                    module._xwlazy_wrapped = True  # Mark as wrapped to avoid re-wrapping
                except Exception:
                    pass
            return None
        
        # Fast path 3: Skip C extension modules and internal modules
        # Also skip submodules that start with underscore (e.g., yaml._yaml)
        if fullname.startswith('_') or ('.' in fullname and fullname.split('.')[-1].startswith('_')):
            logger.debug(f"[HOOK] Skipping C extension/internal module {fullname}")
            return None
        
        # Fast path 4: Check if parent package is partially initialized
        # CRITICAL: Skip ALL submodules of packages that are in sys.modules
        # This prevents circular import issues when a package imports its own submodules
        if '.' in fullname:
            parent_package = fullname.split('.', 1)[0]
            if parent_package in sys.modules:
                logger.debug(f"[HOOK] Skipping {fullname} - parent {parent_package} is in sys.modules (prevent circular import)")
                return None
            if _is_import_in_progress(parent_package):
                logger.debug(f"[HOOK] Skipping {fullname} - parent {parent_package} import in progress")
                return None
        
        # ROOT CAUSE FIX: Check lazy install status FIRST
        root_name = fullname.split('.', 1)[0]
        _watched_registry = get_watched_registry()
        
        # Check if lazy install is enabled
        lazy_install_enabled = LazyInstallConfig.is_enabled(self._package_name)
        install_mode = LazyInstallConfig.get_install_mode(self._package_name)
        
        # If lazy install is disabled, only intercept watched modules
        if not lazy_install_enabled or install_mode == LazyInstallMode.NONE:
            if not _watched_registry.has_root(root_name):
                logger.debug(f"[HOOK] Module {fullname} not in watched registry and lazy install disabled, skipping interception")
                return None
        
        # Check persistent installation cache FIRST
        try:
            installer = LazyInstallerRegistry.get_instance(self._package_name)
            package_name = installer._dependency_mapper.get_package_name(root_name)
            
            # ROOT CAUSE FIX: If this is the package we are managing, DO NOT skip interception!
            # We need to wrap it even if it is installed, so we can intercept its imports.
            should_skip = False
            if package_name == self._package_name or root_name == self._package_name:
                should_skip = False
            elif package_name:
                # Set flag to prevent recursion during installation check
                _set_checking_installation(True)
                try:
                    if installer.is_package_installed(package_name):
                        should_skip = True
                finally:
                    _set_checking_installation(False)
            
            if should_skip:
                logger.debug(f"[HOOK] Package {package_name} is installed (cache check), skipping interception of {fullname}")
                return None
        except Exception:
            pass
        
        # Fast path 4: Cached spec
        cached_spec = _spec_cache_get(fullname)
        if cached_spec is not None:
            return cached_spec
        
        # Fast path 5: Stdlib/builtin check
        if fullname.startswith('importlib') or fullname.startswith('_frozen_importlib'):
            return None
        
        if '.' not in fullname:
            if DependencyMapper._is_stdlib_or_builtin(fullname):
                return None
            if fullname in DependencyMapper.DENY_LIST:
                return None
        
        # Fast path 6: Import in progress
        # NOTE: We allow lazy install to proceed even if import is in progress,
        # because we need to install missing packages during import
        if _is_import_in_progress(fullname):
            # Only skip if lazy install is disabled (for watched modules, we still need to wrap)
            if not lazy_install_enabled and not _watched_registry.has_root(root_name):
                return None
        
        # Only skip global importing state if lazy install is disabled
        # (lazy install needs to run even during imports to install missing packages)
        if getattr(_importing_state, 'active', False):
            if not lazy_install_enabled and not _watched_registry.has_root(root_name):
                return None
        
        # Install mode check already done above
        matching_prefixes: tuple[str, ...] = ()
        if _watched_registry.has_root(root_name):
            matching_prefixes = _watched_registry.get_matching_prefixes(fullname)
        
        installer = LazyInstallerRegistry.get_instance(self._package_name)
        
        # Two-stage lazy loading for serialization and archive modules
        if matching_prefixes:
            for prefix in matching_prefixes:
                if not _watched_registry.is_prefix_owned_by(self._package_name, prefix):
                    continue
                if fullname.startswith(prefix):
                    module_suffix = fullname[len(prefix):]
                    
                    if module_suffix:
                        log_event("hook", logger.info, f"[HOOK] Candidate for wrapping: {fullname}")
                        
                        _mark_import_started(fullname)
                        try:
                            if getattr(_importing_state, 'active', False):
                                logger.debug(f"[HOOK] Recursion guard active, skipping {fullname}")
                                return None
                            
                            try:
                                logger.debug(f"[HOOK] Looking for spec: {fullname}")
                                spec = _spec_cache_get(fullname)
                                if spec is None:
                                    try:
                                        spec = importlib.util.find_spec(fullname)
                                    except (ValueError, AttributeError, ImportError):
                                        pass
                                    if spec is not None:
                                        _spec_cache_put(fullname, spec)
                                if spec is not None:
                                    logger.debug(f"[HOOK] Spec found, trying normal import: {fullname}")
                                    _importing_state.active = True
                                    try:
                                        __import__(fullname)
                                        
                                        module = sys.modules.get(fullname)
                                        if module:
                                            try:
                                                self._enhance_classes_with_class_methods(module)
                                                # Enable auto-instantiation for classes in this module
                                                self._wrap_classes_for_auto_instantiation(module)
                                            except Exception as enhance_exc:
                                                logger.debug(f"[HOOK] Could not enhance classes in {fullname}: {enhance_exc}")
                                            spec = _spec_for_existing_module(fullname, module, spec)
                                        log_event("hook", logger.info, f"✓ [HOOK] Module {fullname} imported successfully, no wrapping needed")
                                        if spec is not None:
                                            _spec_cache_put(fullname, spec)
                                            return spec
                                        return None
                                    finally:
                                        _importing_state.active = False
                            except ImportError as e:
                                if '.' not in module_suffix:
                                    log_event("hook", logger.info, f"⚠ [HOOK] Module {fullname} has missing dependencies, wrapping: {e}")
                                    wrapped_spec = self._wrap_serialization_module(fullname)
                                    if wrapped_spec is not None:
                                        log_event("hook", logger.info, f"✓ [HOOK] Successfully wrapped: {fullname}")
                                        return wrapped_spec
                                    logger.warning(f"✗ [HOOK] Failed to wrap: {fullname}")
                                else:
                                    logger.debug(f"[HOOK] Import failed for nested module {fullname}: {e}")
                            except (ModuleNotFoundError,) as e:
                                logger.debug(f"[HOOK] Module {fullname} not found, skipping wrap: {e}")
                                pass
                            except Exception as e:
                                logger.warning(f"[HOOK] Error checking module {fullname}: {e}")
                        finally:
                            _mark_import_finished(fullname)
                    
                    return None
            
            # If we had matching prefixes but didn't match any, continue to lazy install logic
            if matching_prefixes:
                logger.debug(f"[HOOK] {fullname} had matching prefixes but didn't match any, continuing to lazy install")
        
        # For lazy installation, handle submodules by checking if parent package is installed
        if '.' in fullname:
            parent_package = fullname.split('.', 1)[0]
            if lazy_install_enabled:
                try:
                    installer = LazyInstallerRegistry.get_instance(self._package_name)
                    package_name = installer._dependency_mapper.get_package_name(parent_package)
                    if package_name:
                        # Set flag to prevent recursion during installation check
                        _set_checking_installation(True)
                        try:
                            if not installer.is_package_installed(package_name):
                                logger.debug(f"[HOOK] Parent package {parent_package} not installed, intercepting parent")
                                return self.find_spec(parent_package, path, target)
                        finally:
                            _set_checking_installation(False)
                except Exception:
                    pass
            return None
        if DependencyMapper._is_stdlib_or_builtin(fullname):
            return None
        if fullname in DependencyMapper.DENY_LIST:
            return None
        
        # ROOT CAUSE FIX: For lazy installation, intercept missing imports and install them
        logger.debug(f"[HOOK] Checking lazy install for {fullname}: enabled={lazy_install_enabled}, install_mode={install_mode}")
        if lazy_install_enabled:
            # Prevent infinite loops: Skip if already attempting import
            if _is_import_in_progress(fullname):
                logger.debug(f"[HOOK] Import {fullname} already in progress, skipping to prevent recursion")
                return None
            
            # Prevent infinite loops: Check if we've already tried to install this package
            installer = LazyInstallerRegistry.get_instance(self._package_name)
            package_name = installer._dependency_mapper.get_package_name(root_name)
            
            # ROOT CAUSE FIX: Check if module is ALREADY importable BEFORE checking package installation
            # This handles cases where package name != module name (e.g., PyYAML -> yaml)
            try:
                # Try direct import first (most reliable check)
                if fullname in sys.modules:
                    logger.debug(f"[HOOK] Module {fullname} already in sys.modules, skipping installation")
                    return None
                
                # Temporarily remove finders to check actual importability
                xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
                xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
                for finder in xwlazy_finders:
                    try:
                        sys.meta_path.remove(finder)
                    except ValueError:
                        pass
                
                try:
                    # Check spec without importing (avoids triggering module code execution)
                    # This prevents circular import issues when checking importability
                    spec = importlib.util.find_spec(fullname)
                    if spec is not None and spec.loader is not None:
                        logger.debug(f"[HOOK] Module {fullname} has valid spec, skipping installation")
                        return None
                finally:
                    # Restore finders
                    for finder in reversed(xwlazy_finders):
                        if finder not in sys.meta_path:
                            sys.meta_path.insert(0, finder)
            except Exception as e:
                logger.debug(f"[HOOK] Importability check failed for {fullname}: {e}")
                # If check fails, proceed with installation attempt
            
            if package_name:
                if package_name in installer.get_failed_packages():
                    logger.debug(f"[HOOK] Package {package_name} previously failed installation, skipping {fullname}")
                    return None
                
                # Also check package installation status (for cache efficiency)
                # Set flag to prevent recursion during installation check
                _set_checking_installation(True)
                try:
                    if installer.is_package_installed(package_name):
                        logger.debug(f"[HOOK] Package {package_name} is already installed, skipping installation attempt for {fullname}")
                        return None
                finally:
                    _set_checking_installation(False)
            
            _mark_import_started(fullname)
            try:
                # Guard against recursion when importing facade
                if 'exonware.xwlazy.facade' in sys.modules or 'xwlazy.facade' in sys.modules:
                    from ..facade import lazy_import_with_install
                else:
                    if _is_import_in_progress('exonware.xwlazy.facade') or _is_import_in_progress('xwlazy.facade'):
                        logger.debug(f"[HOOK] Facade import in progress, skipping {fullname} to prevent recursion")
                        return None
                    from ..facade import lazy_import_with_install
                
                # Log installation attempt (DEBUG level to reduce noise)
                if package_name:
                    logger.debug(f"⏳ [HOOK] Attempting to install package '{package_name}' for module '{fullname}'")
                else:
                    logger.debug(f"⏳ [HOOK] Attempting to install module '{fullname}' (no package mapping found)")
                
                _importing_state.active = True
                try:
                    module, success = lazy_import_with_install(
                        fullname,
                        installer_package=self._package_name
                    )
                finally:
                    _importing_state.active = False
                
                if success and module:
                    # Module was successfully installed and imported
                    logger.debug(f"✅ [HOOK] Successfully installed and imported '{fullname}'")
                    xwlazy_finder_names = {'LazyMetaPathFinder', 'LazyPathFinder', 'LazyLoader'}
                    xwlazy_finders = [f for f in sys.meta_path if type(f).__name__ in xwlazy_finder_names]
                    for finder in xwlazy_finders:
                        try:
                            sys.meta_path.remove(finder)
                        except ValueError:
                            pass
                    
                    try:
                        if fullname in sys.modules:
                            del sys.modules[fullname]
                        importlib.invalidate_caches()
                        sys.path_importer_cache.clear()
                        real_module = importlib.import_module(fullname)
                        sys.modules[fullname] = real_module
                        logger.debug(f"[HOOK] Successfully installed {fullname}, replaced module in sys.modules with real module")
                    finally:
                        for finder in reversed(xwlazy_finders):
                            if finder not in sys.meta_path:
                                sys.meta_path.insert(0, finder)
                    return None
                else:
                    # Only log warning if it's not a known missing package (reduce noise)
                    if package_name and package_name not in installer.get_failed_packages():
                        logger.debug(f"❌ [HOOK] Failed to install/import {fullname}")
                    else:
                        logger.debug(f"❌ [HOOK] Failed to install/import {fullname} (already marked as failed)")
                    # Mark as failed to prevent infinite retry loops
                    if package_name:
                        installer._failed_packages.add(package_name)
                    try:
                        installer = LazyInstallerRegistry.get_instance(self._package_name)
                        # Force disable async install usage in engine
                        use_async = False # installer.is_async_enabled()
                        if use_async:
                            placeholder = self._build_async_placeholder(fullname, installer)
                            if placeholder is not None:
                                return placeholder
                    except Exception:
                        pass
                    # Return None to let Python handle the ImportError naturally
                    return None
            except Exception as e:
                logger.error(f"❌ [HOOK] Lazy import hook failed for {fullname}: {e}", exc_info=True)
                # Mark as failed to prevent infinite retry loops
                if package_name:
                    try:
                        installer = LazyInstallerRegistry.get_instance(self._package_name)
                        installer._failed_packages.add(package_name)
                    except Exception:
                        pass
                return None
            finally:
                _mark_import_finished(fullname)
    
    def _wrap_serialization_module(self, fullname: str):
        """Wrap serialization module loading to defer missing dependencies."""
        log_event("hook", logger.info, f"[STAGE 1] Starting wrap of module: {fullname}")
        
        try:
            logger.debug(f"[STAGE 1] Getting spec for: {fullname}")
            try:
                sys.meta_path.remove(self)
            except ValueError:
                pass
            try:
                spec = importlib.util.find_spec(fullname)
            finally:
                if self not in sys.meta_path:
                    sys.meta_path.insert(0, self)
            if not spec or not spec.loader:
                logger.warning(f"[STAGE 1] No spec or loader for: {fullname}")
                return None
            
            logger.debug(f"[STAGE 1] Creating module from spec: {fullname}")
            module = importlib.util.module_from_spec(spec)
            
            deferred_imports = {}
            
            logger.debug(f"[STAGE 1] Setting up import wrapper for: {fullname}")
            original_import = builtins.__import__
            
            def capture_import_errors(name, *args, **kwargs):
                """Intercept imports and defer ONLY external missing packages."""
                logger.debug(f"[STAGE 1] capture_import_errors: Trying to import '{name}' in {fullname}")
                
                if _is_import_in_progress(name):
                    logger.debug(f"[STAGE 1] Import '{name}' already in progress, using original_import")
                    return original_import(name, *args, **kwargs)
                
                _mark_import_started(name)
                try:
                    result = original_import(name, *args, **kwargs)
                    logger.debug(f"[STAGE 1] ✓ Successfully imported '{name}'")
                    return result
                except ImportError as e:
                    logger.debug(f"[STAGE 1] ✗ Import failed for '{name}': {e}")
                    
                    host_alias = self._package_name or ""
                    if name.startswith('exonware.') or (host_alias and name.startswith(f"{host_alias}.")):
                        log_event("hook", logger.info, f"[STAGE 1] Letting internal import '{name}' fail normally (internal package)")
                        raise
                    
                    if '.' in name:
                        log_event("hook", logger.info, f"[STAGE 1] Letting submodule '{name}' fail normally (has dots)")
                        raise
                    
                    log_event("hook", logger.info, f"⏳ [STAGE 1] DEFERRING missing external package '{name}' in {fullname}")
                    async_handle = None
                    try:
                        installer = LazyInstallerRegistry.get_instance(self._package_name)
                        async_handle = installer.schedule_async_install(name)
                    except Exception as schedule_exc:
                        logger.debug(f"[STAGE 1] Async install scheduling failed for '{name}': {schedule_exc}")
                    deferred = DeferredImportError(name, e, self._package_name, async_handle=async_handle)
                    deferred_imports[name] = deferred
                    
                    # ROOT CAUSE FIX: Register deferred object in sys.modules to prevent infinite import loops
                    # If we don't do this, subsequent imports of the same missing module will trigger find_spec again
                    sys.modules[name] = deferred
                    
                    return deferred
                finally:
                    _mark_import_finished(name)
            
            logger.debug(f"[STAGE 1] Executing module with import wrapper: {fullname}")
            builtins.__import__ = capture_import_errors
            try:
                spec.loader.exec_module(module)
                logger.debug(f"[STAGE 1] Module execution completed: {fullname}")
                
                if deferred_imports:
                    log_event("hook", logger.info, f"✓ [STAGE 1] Module {fullname} loaded with {len(deferred_imports)} deferred imports: {list(deferred_imports.keys())}")
                    self._replace_none_with_deferred(module, deferred_imports)
                    self._wrap_module_classes(module, deferred_imports)
                else:
                    log_event("hook", logger.info, f"✓ [STAGE 1] Module {fullname} loaded with NO deferred imports (all dependencies available)")
                
                self._enhance_classes_with_class_methods(module)
                
                # Enable auto-instantiation for classes in this module
                self._wrap_classes_for_auto_instantiation(module)
                
            finally:
                logger.debug(f"[STAGE 1] Restoring original __import__")
                builtins.__import__ = original_import
            
            logger.debug(f"[STAGE 1] Registering module in sys.modules: {fullname}")
            sys.modules[fullname] = module
            final_spec = _spec_for_existing_module(fullname, module, spec)
            _spec_cache_put(fullname, final_spec)
            log_event("hook", logger.info, f"✓ [STAGE 1] Successfully wrapped and registered: {fullname}")
            return final_spec
            
        except Exception as e:
            logger.debug(f"Could not wrap {fullname}: {e}")
            return None
    
    def _replace_none_with_deferred(self, module, deferred_imports: Dict):
        """Replace None values in module namespace with deferred import proxies."""
        logger.debug(f"[STAGE 1] Replacing None with deferred imports in {module.__name__}")
        replaced_count = 0
        
        for dep_name, deferred_import in deferred_imports.items():
            if hasattr(module, dep_name):
                current_value = getattr(module, dep_name)
                if current_value is None:
                    log_event("hook", logger.info, f"[STAGE 1] Replacing {dep_name}=None with deferred import proxy in {module.__name__}")
                    setattr(module, dep_name, deferred_import)
                    replaced_count += 1
        
        if replaced_count > 0:
            log_event("hook", logger.info, f"✓ [STAGE 1] Replaced {replaced_count} None values with deferred imports in {module.__name__}")
    
    def _wrap_module_classes(self, module, deferred_imports: Dict):
        """Wrap classes in a module that depend on deferred imports."""
        module_name = getattr(module, '__name__', '<unknown>')
        logger.debug(f"[STAGE 1] Wrapping classes in {module_name} (deferred: {list(deferred_imports.keys())})")
        module_file = (getattr(module, '__file__', '') or '').lower()
        lower_map = {dep_name.lower(): dep_name for dep_name in deferred_imports.keys()}
        class_hints = _get_package_class_hints(self._package_name)
        with _wrapped_cache_lock:
            already_wrapped = _WRAPPED_CLASS_CACHE.setdefault(module_name, set()).copy()
        pending_lower = {lower for lower in lower_map.keys() if lower_map[lower] not in already_wrapped}
        if not pending_lower:
            logger.debug(f"[STAGE 1] All deferred imports already wrapped for {module_name}")
            return
        dep_entries = [(lower, deferred_imports[lower_map[lower]]) for lower in pending_lower]
        wrapped_count = 0
        newly_wrapped: set[str] = set()
        
        for name, obj in list(module.__dict__.items()):
            if not pending_lower:
                break
            if not isinstance(obj, type):
                continue
            lower_name = name.lower()
            if class_hints and not any(hint in lower_name for hint in class_hints):
                continue
            target_lower = None
            target_deferred = None
            for dep_lower, deferred in dep_entries:
                if dep_lower not in pending_lower:
                    continue
                if dep_lower in lower_name or dep_lower in module_file:
                    target_lower = dep_lower
                    target_deferred = deferred
                    break
            if target_deferred is None or target_lower is None:
                continue
            
            logger.debug(f"[STAGE 1] Class '{name}' depends on deferred import, wrapping...")
            wrapped = self._create_lazy_class_wrapper(obj, target_deferred)
            module.__dict__[name] = wrapped
            wrapped_count += 1
            origin_name = lower_map.get(target_lower, target_lower)
            newly_wrapped.add(origin_name)
            pending_lower.discard(target_lower)
            log_event("hook", logger.info, f"✓ [STAGE 1] Wrapped class '{name}' in {module_name}")
        
        if newly_wrapped:
            with _wrapped_cache_lock:
                cache = _WRAPPED_CLASS_CACHE.setdefault(module_name, set())
                cache.update(newly_wrapped)
        
        log_event("hook", logger.info, f"[STAGE 1] Wrapped {wrapped_count} classes in {module_name}")
    
    def _wrap_classes_for_auto_instantiation(self, module: ModuleType) -> None:
        """
        Wrap classes in modules with AutoInstantiateProxy for auto-instantiation.
        
        This enables: from module import Class as instance
        Then: instance.method() works automatically without manual instantiation.
        
        We wrap classes directly in module.__dict__ AND add a __getattr__ fallback
        to catch any classes that might be accessed before wrapping completes.
        
        We wrap ALL classes in the module's namespace, whether defined in this
        module or imported from submodules (like BsonSerializer imported in __init__.py).
        """
        import inspect
        import types
        
        # Store original __getattr__ if it exists
        original_getattr = getattr(module, '__getattr__', None)
        
        wrapped_count = 0
        wrapped_classes = {}  # Track wrapped classes for __getattr__
        
        for name, obj in list(module.__dict__.items()):
            # Wrap classes that are in this module's namespace
            # This includes classes defined here AND classes imported from submodules
            if (inspect.isclass(obj) and 
                not inspect.isbuiltin(obj) and
                hasattr(obj, '__module__')):
                # Skip if it's already a proxy
                if isinstance(obj, AutoInstantiateProxy):
                    continue
                # Skip if it's a wrapper class
                if obj.__name__.startswith('Lazy'):
                    continue
                # Skip if it's a type from typing or other special modules
                module_name = obj.__module__
                if module_name in ('typing', 'builtins', '__builtin__'):
                    continue
                
                logger.debug(f"[AUTO-INST] Wrapping class '{name}' ({module_name}) in {module.__name__} for auto-instantiation")
                proxy = AutoInstantiateProxy(obj)
                module.__dict__[name] = proxy
                wrapped_classes[name] = proxy
                wrapped_count += 1
        
        # Add __getattr__ fallback to wrap classes on access (for classes added after initial load)
        if wrapped_count > 0 or True:  # Always add __getattr__ for consistency
            def auto_instantiate_getattr(name: str):
                """Module-level __getattr__ that wraps classes for auto-instantiation."""
                # First try original __getattr__
                if original_getattr:
                    try:
                        attr = original_getattr(name)
                        # If it's a class, wrap it
                        if inspect.isclass(attr) and not inspect.isbuiltin(attr):
                            if not isinstance(attr, AutoInstantiateProxy):
                                logger.debug(f"[AUTO-INST] Wrapping class '{name}' on access in {module.__name__}")
                                proxy = AutoInstantiateProxy(attr)
                                module.__dict__[name] = proxy  # Cache it
                                return proxy
                        return attr
                    except AttributeError:
                        pass
                
                # Get from __dict__ (might be unwrapped)
                if name in module.__dict__:
                    attr = module.__dict__[name]
                    # If it's an unwrapped class, wrap it now
                    if (inspect.isclass(attr) and 
                        not inspect.isbuiltin(attr) and
                        not isinstance(attr, AutoInstantiateProxy) and
                        hasattr(attr, '__module__')):
                        module_name = attr.__module__
                        if module_name not in ('typing', 'builtins', '__builtin__'):
                            logger.debug(f"[AUTO-INST] Wrapping class '{name}' on access in {module.__name__}")
                            proxy = AutoInstantiateProxy(attr)
                            module.__dict__[name] = proxy  # Cache it
                            return proxy
                    return attr
                
                raise AttributeError(f"module '{module.__name__}' has no attribute '{name}'")
            
            # Only set __getattr__ if module doesn't already have a custom one
            if not hasattr(module, '__getattr__') or isinstance(getattr(module, '__getattr__', None), types.MethodType):
                module.__getattr__ = auto_instantiate_getattr  # type: ignore[attr-defined]
        
        if wrapped_count > 0:
            logger.debug(f"[AUTO-INST] Wrapped {wrapped_count} classes in {module.__name__} for auto-instantiation")
    
    def _create_lazy_class_wrapper(self, original_class, deferred_import: DeferredImportError):
        """Create a wrapper class that installs dependencies when instantiated."""
        class LazyClassWrapper:
            """Lazy wrapper that installs dependencies on first instantiation."""
            
            def __init__(self, *args, **kwargs):
                """Install dependency and create real instance."""
                deferred_import._try_install_and_import()
                
                real_module = importlib.reload(sys.modules[original_class.__module__])
                real_class = getattr(real_module, original_class.__name__)
                
                real_instance = real_class(*args, **kwargs)
                self.__class__ = real_class
                self.__dict__ = real_instance.__dict__
            
            def __repr__(self):
                return f"<Lazy{original_class.__name__}: will install dependencies on init>"
        
        LazyClassWrapper.__name__ = f"Lazy{original_class.__name__}"
        LazyClassWrapper.__qualname__ = f"Lazy{original_class.__qualname__}"
        LazyClassWrapper.__module__ = original_class.__module__
        LazyClassWrapper.__doc__ = original_class.__doc__
        
        return LazyClassWrapper
    
    def _enhance_classes_with_class_methods(self, module):
        """Enhance classes with lazy class methods - automatically detects ALL instance methods."""
        if module is None:
            return
        # Debug: Check if module has classes
        module_classes = [name for name, obj in module.__dict__.items() if isinstance(obj, type)]
        if not module_classes:
            return  # No classes to enhance
        
        # Get methods from registry (if any) for specific prefixes
        methods_to_apply: tuple[str, ...] = ()
        for prefix, methods in _lazy_prefix_method_registry.items():
            if module.__name__.startswith(prefix.rstrip('.')):
                methods_to_apply = methods
                break
        
        # If no prefix match, use default methods from env var
        if not methods_to_apply:
            methods_to_apply = _DEFAULT_LAZY_METHODS
        
        # CRITICAL FIX: If no specific methods registered, enhance ALL instance methods
        # This makes xwlazy handle ALL scenarios (classes, functions, instance methods)
        auto_detect_all = not methods_to_apply
        
        enhanced = 0
        for name, obj in list(module.__dict__.items()):
            if not isinstance(obj, type):
                continue
            
            # Get methods to enhance for this class
            if auto_detect_all:
                # Auto-detect instance methods defined DIRECTLY in this class (not inherited)
                # This prevents wrapping wrong methods from parent classes
                methods_to_wrap = []
                # Only check methods in this class's __dict__ to avoid inherited methods
                for attr_name, attr_value in obj.__dict__.items():
                    if attr_name.startswith('_') and attr_name not in ('__init__', '__new__'):
                        continue  # Skip private methods except __init__ and __new__
                    if not callable(attr_value):
                        continue
                    if isinstance(attr_value, (classmethod, staticmethod)):
                        continue
                    if getattr(attr_value, "__lazy_wrapped__", False):
                        continue
                    # Check if it's an instance method (has 'self' as first param)
                    import inspect
                    try:
                        if inspect.isfunction(attr_value):
                            sig = inspect.signature(attr_value)
                            params = list(sig.parameters.keys())
                            if params and params[0] == 'self':
                                methods_to_wrap.append(attr_name)
                    except (ValueError, TypeError):
                        # Can't inspect signature, skip
                        pass
            else:
                # Use specific methods from registry
                methods_to_wrap = list(methods_to_apply)
            
            # Enhance each method
            for method_name in methods_to_wrap:
                try:
                    # CRITICAL FIX: Only get from class __dict__ to ensure we get the RIGHT method
                    original_func = obj.__dict__.get(method_name)
                    if original_func is None:
                        continue  # Method not in class dict
                    if not inspect.isfunction(original_func):
                        continue
                    if getattr(original_func, "__lazy_wrapped__", False):
                        continue
                    if isinstance(original_func, (classmethod, staticmethod)):
                        continue
                    if original_func.__name__ != method_name:
                        continue
                    # Verify it's an instance method
                    try:
                        params = list(inspect.signature(original_func).parameters.keys())
                        if not params or params[0] != 'self':
                            continue
                    except Exception:
                        continue
                    # Create wrapper with proper closure
                    class_obj, func_to_call = obj, original_func
                    import functools
                    def make_wrapper(fn, cls):
                        @functools.wraps(fn)
                        def wrapper(first_arg, *args, **kwargs):
                            if isinstance(first_arg, cls):
                                return fn(first_arg, *args, **kwargs)
                            instance = cls()
                            return fn(instance, first_arg, *args, **kwargs)
                        return wrapper
                    smart_wrapper = make_wrapper(func_to_call, class_obj)
                    smart_wrapper.__lazy_wrapped__ = True
                    setattr(obj, method_name, smart_wrapper)
                    enhanced += 1
                except Exception as exc:
                    # Silent skip - one line as requested (package/module agnostic)
                    pass
        
        if enhanced:
            log_event("enhance", logger.info, "✓ [LAZY ENHANCE] Enhanced %s methods in %s", enhanced, module.__name__)


class AutoInstantiateProxy:
    """
    Proxy that auto-instantiates a class on first method call.
    
    Enables: from module import Class as instance
    Then: instance.method() automatically creates Class() and calls method
    
    This allows users to import classes with 'as' and use them directly
    without needing to manually instantiate.
    """
    
    def __init__(self, original_class):
        """Initialize proxy with the class to wrap."""
        self._class = original_class
        self._instance = None
        self._is_instantiated = False
    
    def _ensure_instantiated(self):
        """Ensure the class is instantiated."""
        if not self._is_instantiated:
            self._instance = self._class()
            self._is_instantiated = True
    
    def __getattr__(self, name: str):
        """Get attribute from instance, instantiating if needed."""
        self._ensure_instantiated()
        return getattr(self._instance, name)
    
    def __call__(self, *args, **kwargs):
        """Allow calling the proxy directly (creates new instance)."""
        return self._class(*args, **kwargs)
    
    def __repr__(self):
        if self._is_instantiated:
            return f"<AutoInstantiateProxy({self._class.__name__}): instantiated>"
        return f"<AutoInstantiateProxy({self._class.__name__}): will instantiate on first use>"
    
    @property
    def __class__(self):
        """Return the wrapped class for isinstance checks."""
        return self._class

# Registry of installed hooks per package
_installed_hooks: dict[str, LazyMetaPathFinder] = {}
_hook_lock = threading.RLock()

def install_import_hook(package_name: str = 'default') -> None:
    """Install performant import hook for automatic lazy installation."""
    global _installed_hooks
    
    log_event("hook", logger.info, f"[HOOK INSTALL] Installing import hook for package: {package_name}")
    
    with _hook_lock:
        if package_name in _installed_hooks:
            log_event("hook", logger.info, f"[HOOK INSTALL] Import hook already installed for {package_name}")
            return
        
        logger.debug(f"[HOOK INSTALL] Creating LazyMetaPathFinder for {package_name}")
        hook = LazyMetaPathFinder(package_name)
        
        logger.debug(f"[HOOK INSTALL] Current sys.meta_path has {len(sys.meta_path)} entries")
        sys.meta_path.insert(0, hook)
        _installed_hooks[package_name] = hook
        
        log_event("hook", logger.info, f"✅ [HOOK INSTALL] Lazy import hook installed for {package_name} (now {len(sys.meta_path)} meta_path entries)")

def uninstall_import_hook(package_name: str = 'default') -> None:
    """Uninstall import hook for a package."""
    global _installed_hooks
    
    with _hook_lock:
        if package_name in _installed_hooks:
            hook = _installed_hooks[package_name]
            try:
                sys.meta_path.remove(hook)
            except ValueError:
                pass
            del _installed_hooks[package_name]
            log_event("hook", logger.info, f"Lazy import hook uninstalled for {package_name}")

def is_import_hook_installed(package_name: str = 'default') -> bool:
    """Check if import hook is installed for a package."""
    return package_name in _installed_hooks

def register_lazy_module_prefix(prefix: str) -> None:
    """Register an import prefix for lazy wrapping."""
    _watched_registry = get_watched_registry()
    _watched_registry.add(prefix)
    normalized = _normalize_prefix(prefix)
    if normalized:
        log_event("config", logger.info, "Registered lazy module prefix: %s", normalized)

# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Logging utilities
    'get_logger',
    'log_event',
    'print_formatted',
    'format_message',
    'is_log_category_enabled',
    'set_log_category',
    'set_log_categories',
    'get_log_categories',
    'XWLazyFormatter',
    # Import tracking
    '_is_import_in_progress',
    '_mark_import_started',
    '_mark_import_finished',
    'get_importing_state',
    'get_installing_state',
    '_installation_depth',
    '_installation_depth_lock',
    # Prefix trie
    '_PrefixTrie',
    # Watched registry
    'WatchedPrefixRegistry',
    'get_watched_registry',
    # Deferred loader
    '_DeferredModuleLoader',
    # Cache utilities
    # Parallel utilities
    'ParallelLoader',
    'DependencyGraph',
    # Module patching
    '_lazy_aware_import_module',
    '_patch_import_module',
    '_unpatch_import_module',
    # Archive imports
    'get_archive_path',
    'ensure_archive_in_path',
    'import_from_archive',
    # Bootstrap
    'bootstrap_lazy_mode',
    'bootstrap_lazy_mode_deferred',
    # Lazy loader
    'LazyLoader',
    # Lazy module registry
    'LazyModuleRegistry',
    # Lazy importer
    'LazyImporter',
    # Import hook
    'LazyImportHook',
    # Meta path finder
    'LazyMetaPathFinder',
    'install_import_hook',
    'uninstall_import_hook',
    'is_import_hook_installed',
    'register_lazy_module_prefix',
    'register_lazy_module_methods',
    '_set_package_class_hints',
    '_get_package_class_hints',
    '_clear_all_package_class_hints',
    '_spec_for_existing_module',
    # Global __import__ hook (for module-level imports)
    'register_lazy_package',
    'install_global_import_hook',
    'uninstall_global_import_hook',
    'is_global_import_hook_installed',
    'clear_global_import_caches',
    'get_global_import_cache_stats',
]

