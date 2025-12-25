"""
#exonware/xwlazy/src/exonware/xwlazy/common/cache.py

Cache utilities for xwlazy - shared across package, module, and runtime.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

This module provides unified caching functionality for all xwlazy components.
All cache code is centralized here to avoid duplication.
"""

import os
import sys
import json
import time
import pickle
import struct
import importlib
import importlib.util
import threading
from pathlib import Path
from typing import Optional, Any
from collections import OrderedDict
from queue import Queue

from .logger import get_logger

logger = get_logger("xwlazy.cache")

# =============================================================================
# MULTI-TIER CACHE
# =============================================================================

class MultiTierCache:
    """
    Multi-tier cache with L1 (memory), L2 (disk), L3 (predictive).
    
    Used by package, module, and runtime for caching:
    - Package installation status
    - Module imports
    - Runtime metrics and performance data
    """
    
    def __init__(self, l1_size: int = 1000, l2_dir: Optional[Path] = None, enable_l3: bool = True):
        """
        Initialize multi-tier cache.
        
        Args:
            l1_size: Maximum size of L1 (memory) cache
            l2_dir: Directory for L2 (disk) cache (defaults to ~/.xwlazy_cache)
            enable_l3: Enable L3 (predictive) cache
        """
        self._l1_cache: OrderedDict[str, Any] = OrderedDict()
        self._l1_max_size = l1_size
        self._l2_dir = l2_dir or Path.home() / ".xwlazy_cache"
        self._l2_dir.mkdir(parents=True, exist_ok=True)
        self._enable_l3 = enable_l3
        self._l3_patterns: dict[str, tuple[int, float]] = {}
        self._lock = threading.RLock()
        
        self._l2_write_queue: Queue = Queue()
        self._l2_write_thread: Optional[threading.Thread] = None
        self._l2_write_stop = threading.Event()
        self._start_l2_writer()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (L1 -> L2 -> L3).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Check L1 (memory) cache first
        if key in self._l1_cache:
            with self._lock:
                if key in self._l1_cache:
                    value = self._l1_cache.pop(key)
                    self._l1_cache[key] = value  # Move to end (LRU)
                    self._update_l3_pattern(key)
                    return value
        
        # Check L2 (disk) cache
        l2_path = self._l2_dir / f"{hash(key) % (2**31)}.cache"
        if l2_path.exists():
            try:
                with open(l2_path, 'rb') as f:
                    value = pickle.load(f)
                with self._lock:
                    self._set_l1(key, value)  # Promote to L1
                    self._update_l3_pattern(key)
                return value
            except Exception as e:
                logger.debug(f"Failed to load L2 cache for {key}: {e}")
        
        # L3 (predictive) - just logs, doesn't return
        if self._enable_l3 and key in self._l3_patterns:
            freq, _ = self._l3_patterns[key]
            if freq > 5:
                logger.debug(f"L3 pattern detected for {key} (freq: {freq})")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache (L1 + L2 batched).
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self._lock:
            self._set_l1(key, value)
            self._update_l3_pattern(key)
        
        # Queue for L2 write (batched)
        self._l2_write_queue.put((key, value))
    
    def _set_l1(self, key: str, value: Any) -> None:
        """Set value in L1 cache (internal, called with lock held)."""
        if key in self._l1_cache:
            self._l1_cache.move_to_end(key)
        else:
            self._l1_cache[key] = value
            if len(self._l1_cache) > self._l1_max_size:
                self._l1_cache.popitem(last=False)  # Remove oldest (LRU)
    
    def _set_l2(self, key: str, value: Any) -> None:
        """Set value in L2 cache (internal, called by writer thread)."""
        try:
            l2_path = self._l2_dir / f"{hash(key) % (2**31)}.cache"
            with open(l2_path, 'wb') as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.debug(f"Failed to save L2 cache for {key}: {e}")
    
    def _start_l2_writer(self) -> None:
        """Start background thread for batched L2 writes."""
        def _l2_writer():
            batch = []
            batch_size = 10
            batch_timeout = 0.1
            
            while not self._l2_write_stop.is_set():
                try:
                    try:
                        key, value = self._l2_write_queue.get(timeout=batch_timeout)
                        batch.append((key, value))
                        
                        # Collect batch
                        for _ in range(batch_size - 1):
                            try:
                                key, value = self._l2_write_queue.get_nowait()
                                batch.append((key, value))
                            except:
                                break
                    except:
                        pass
                    
                    # Write batch
                    if batch:
                        for key, value in batch:
                            self._set_l2(key, value)
                        batch.clear()
                except Exception as e:
                    logger.debug(f"L2 writer error: {e}")
        
        self._l2_write_thread = threading.Thread(target=_l2_writer, daemon=True, name="xwlazy-l2-writer")
        self._l2_write_thread.start()
    
    def shutdown(self) -> None:
        """Shutdown L2 writer thread."""
        self._l2_write_stop.set()
        if self._l2_write_thread:
            self._l2_write_thread.join(timeout=1.0)
    
    def _update_l3_pattern(self, key: str) -> None:
        """Update L3 access patterns (called with lock held)."""
        if self._enable_l3:
            freq, _ = self._l3_patterns.get(key, (0, 0.0))
            self._l3_patterns[key] = (freq + 1, time.time())
            
            # Prune old patterns if too many
            if len(self._l3_patterns) > 10000:
                sorted_patterns = sorted(self._l3_patterns.items(), key=lambda x: x[1][1])
                for old_key, _ in sorted_patterns[:1000]:
                    del self._l3_patterns[old_key]
    
    def get_predictive_keys(self, limit: int = 10) -> list[str]:
        """
        Get keys likely to be accessed soon (for preloading).
        
        Args:
            limit: Maximum number of keys to return
            
        Returns:
            List of keys sorted by access likelihood
        """
        with self._lock:
            if not self._enable_l3:
                return []
            
            scored = [
                (key, freq * (1.0 / (time.time() - last + 1.0)))
                for key, (freq, last) in self._l3_patterns.items()
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            return [key for key, _ in scored[:limit]]
    
    def clear(self) -> None:
        """Clear all cache tiers."""
        with self._lock:
            self._l1_cache.clear()
            self._l3_patterns.clear()
        
        # Clear L2 directory
        try:
            for cache_file in self._l2_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logger.debug(f"Failed to clear L2 cache: {e}")

# =============================================================================
# BYTECODE CACHE
# =============================================================================

class BytecodeCache:
    """
    Bytecode caching for faster module loading.
    
    Caches compiled Python bytecode to avoid recompilation on subsequent imports.
    Used by module loading for performance optimization.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize bytecode cache.
        
        Args:
            cache_dir: Directory for bytecode cache (defaults to ~/.xwlazy_bytecode)
        """
        self._cache_dir = cache_dir or Path.home() / ".xwlazy_bytecode"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
    
    def get_bytecode_path(self, module_path: str) -> Path:
        """
        Get bytecode cache path for module.
        
        Args:
            module_path: Module path (e.g., "exonware.xwdata")
            
        Returns:
            Path to bytecode cache file
        """
        cache_name = f"{hash(module_path) % (2**31)}.pyc"
        return self._cache_dir / cache_name
    
    def get_cached_bytecode(self, module_path: str) -> Optional[bytes]:
        """
        Get cached bytecode if available and valid.
        
        Args:
            module_path: Module path
            
        Returns:
            Cached bytecode or None if not available/invalid
        """
        with self._lock:
            cache_path = self.get_bytecode_path(module_path)
            if not cache_path.exists():
                return None
            
            try:
                # Check if source is newer than cache
                source_path = self._find_source_path(module_path)
                if source_path and source_path.exists():
                    source_mtime = source_path.stat().st_mtime
                    cache_mtime = cache_path.stat().st_mtime
                    if source_mtime > cache_mtime:
                        return None  # Source is newer, cache invalid
                
                # Read bytecode (skip 16-byte header)
                with open(cache_path, 'rb') as f:
                    f.seek(16)
                    return f.read()
            except Exception as e:
                logger.debug(f"Failed to load bytecode cache for {module_path}: {e}")
                return None
    
    def cache_bytecode(self, module_path: str, bytecode: bytes) -> None:
        """
        Cache compiled bytecode.
        
        Args:
            module_path: Module path
            bytecode: Compiled bytecode to cache
        """
        with self._lock:
            try:
                cache_path = self.get_bytecode_path(module_path)
                with open(cache_path, 'wb') as f:
                    # Write Python bytecode header
                    f.write(importlib.util.MAGIC_NUMBER)
                    f.write(struct.pack('<I', int(time.time())))  # Timestamp
                    f.write(struct.pack('<I', 0))  # Size (0 = unknown)
                    f.write(bytecode)
            except Exception as e:
                logger.debug(f"Failed to cache bytecode for {module_path}: {e}")
    
    def _find_source_path(self, module_path: str) -> Optional[Path]:
        """
        Find source file path for module.
        
        Args:
            module_path: Module path
            
        Returns:
            Path to source file or None if not found
        """
        try:
            spec = importlib.util.find_spec(module_path)
            if spec and spec.origin:
                return Path(spec.origin)
        except Exception:
            pass
        return None
    
    def clear(self) -> None:
        """Clear bytecode cache."""
        with self._lock:
            try:
                for cache_file in self._cache_dir.glob("*.pyc"):
                    cache_file.unlink()
            except Exception as e:
                logger.debug(f"Failed to clear bytecode cache: {e}")

# =============================================================================
# INSTALLATION CACHE
# =============================================================================

class InstallationCache:
    """
    Persistent file-based cache for tracking installed packages.
    
    Cache format: {package_name: {installed: bool, version: str, timestamp: float}}
    Cache location: ~/.xwlazy/installed_packages.json
    
    Used by package installer to track which packages are installed,
    avoiding expensive importability checks on subsequent runs.
    """
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize installation cache.
        
        Args:
            cache_file: Optional path to cache file. Defaults to ~/.xwlazy/installed_packages.json
        """
        if cache_file is None:
            cache_dir = Path.home() / ".xwlazy"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / "installed_packages.json"
        
        self._cache_file = cache_file
        self._lock = threading.RLock()
        self._cache: dict[str, dict[str, Any]] = {}
        self._dirty = False
        
        # Load cache on init
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cache from disk."""
        if not self._cache_file.exists():
            self._cache = {}
            return
        
        try:
            with self._lock:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Validate format
                    if isinstance(data, dict):
                        self._cache = {k: v for k, v in data.items() 
                                     if isinstance(v, dict) and 'installed' in v}
                    else:
                        self._cache = {}
        except (json.JSONDecodeError, IOError, OSError) as e:
            logger.debug(f"Failed to load installation cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to disk."""
        if not self._dirty:
            return
        
        try:
            with self._lock:
                # Create parent directory if needed
                self._cache_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write atomically using temp file
                temp_file = self._cache_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self._cache, f, indent=2, sort_keys=True)
                
                # Atomic rename
                temp_file.replace(self._cache_file)
                self._dirty = False
        except (IOError, OSError) as e:
            logger.warning(f"Failed to save installation cache: {e}")
    
    def is_installed(self, package_name: str) -> bool:
        """
        Check if package is marked as installed in cache.
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            True if package is in cache and marked as installed, False otherwise
        """
        with self._lock:
            entry = self._cache.get(package_name)
            if entry is None:
                return False
            return entry.get('installed', False)
    
    def mark_installed(self, package_name: str, version: Optional[str] = None) -> None:
        """
        Mark package as installed in cache.
        
        Args:
            package_name: Name of the package
            version: Optional version string
        """
        with self._lock:
            self._cache[package_name] = {
                'installed': True,
                'version': version or 'unknown',
                'timestamp': time.time()
            }
            self._dirty = True
            self._save_cache()
    
    def mark_uninstalled(self, package_name: str) -> None:
        """
        Mark package as uninstalled in cache.
        
        Args:
            package_name: Name of the package
        """
        with self._lock:
            if package_name in self._cache:
                self._cache[package_name]['installed'] = False
                self._cache[package_name]['timestamp'] = time.time()
                self._dirty = True
                self._save_cache()
    
    def get_version(self, package_name: str) -> Optional[str]:
        """
        Get cached version of package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            Version string if available, None otherwise
        """
        with self._lock:
            entry = self._cache.get(package_name)
            if entry and entry.get('installed', False):
                return entry.get('version')
            return None
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._dirty = True
            self._save_cache()
    
    def get_all_installed(self) -> set[str]:
        """
        Get set of all packages marked as installed.
        
        Returns:
            Set of package names that are marked as installed
        """
        with self._lock:
            return {name for name, entry in self._cache.items() 
                   if entry.get('installed', False)}
    
    def __len__(self) -> int:
        """Return number of cached packages."""
        return len(self._cache)

