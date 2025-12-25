"""
#exonware/xwlazy/src/exonware/xwlazy/discovery/spec_cache.py

Spec cache utilities for module specification caching.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 10-Oct-2025

This module provides multi-level caching (L1: memory, L2: disk) for module specs
to optimize import performance.
"""

import os
import sys
import time
import threading
import importlib
import importlib.machinery
import importlib.util
from pathlib import Path
from typing import Optional
from collections import OrderedDict
from functools import lru_cache

# Environment variables
_SPEC_CACHE_MAX = int(os.environ.get("XWLAZY_SPEC_CACHE_MAX", "512") or 512)
_SPEC_CACHE_TTL = float(os.environ.get("XWLAZY_SPEC_CACHE_TTL", "60") or 60.0)

# Cache storage
_spec_cache_lock = threading.RLock()
_spec_cache: OrderedDict[str, tuple[importlib.machinery.ModuleSpec, float]] = OrderedDict()

# Multi-level cache: L1 (in-memory) + L2 (disk)
_CACHE_L2_DIR = Path(
    os.environ.get(
        "XWLAZY_CACHE_DIR",
        os.path.join(os.path.expanduser("~"), ".xwlazy", "cache"),
    )
)
_CACHE_L2_DIR.mkdir(parents=True, exist_ok=True)

# Stdlib module set
try:
    _STDLIB_MODULE_SET: set[str] = set(sys.stdlib_module_names)  # type: ignore[attr-defined]
except AttributeError:
    _STDLIB_MODULE_SET = set()
_STDLIB_MODULE_SET.update(sys.builtin_module_names)

@lru_cache(maxsize=1024)
def _cached_stdlib_check(module_name: str) -> bool:
    """Check if module is part of stdlib or built-in modules."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        if spec.origin in ("built-in", None):
            return True
        origin = spec.origin or ""
        return (
            "python" in origin.lower()
            and "site-packages" not in origin.lower()
            and "dist-packages" not in origin.lower()
        )
    except Exception:
        return False

def _spec_cache_prune_locked(now: Optional[float] = None) -> None:
    """Prune expired entries from spec cache (must be called with lock held)."""
    if not _spec_cache:
        return
    current = now or time.monotonic()
    while _spec_cache:
        fullname, (_, ts) = next(iter(_spec_cache.items()))
        if current - ts <= _SPEC_CACHE_TTL and len(_spec_cache) <= _SPEC_CACHE_MAX:
            break
        _spec_cache.popitem(last=False)

def _spec_cache_get(fullname: str) -> Optional[importlib.machinery.ModuleSpec]:
    """Get spec from multi-level cache (L1: memory, L2: disk)."""
    with _spec_cache_lock:
        _spec_cache_prune_locked()
        entry = _spec_cache.get(fullname)
        if entry is not None:
            spec, _ = entry
            _spec_cache.move_to_end(fullname)
            return spec
        
        # L2 cache: Check disk cache
        try:
            cache_file = _CACHE_L2_DIR / f"{fullname.replace('.', '_')}.spec"
            if cache_file.exists():
                mtime = cache_file.stat().st_mtime
                age = time.time() - mtime
                if age < _SPEC_CACHE_TTL:
                    try:
                        import pickle
                        with open(cache_file, 'rb') as f:
                            spec = pickle.load(f)
                        # Promote to L1 cache
                        _spec_cache[fullname] = (spec, time.monotonic())
                        _spec_cache.move_to_end(fullname)
                        return spec
                    except Exception:
                        pass
        except Exception:
            pass
        
        return None

def _spec_cache_put(fullname: str, spec: Optional[importlib.machinery.ModuleSpec]) -> None:
    """Put spec in multi-level cache (L1: memory, L2: disk)."""
    if spec is None:
        return
    with _spec_cache_lock:
        # L1 cache: In-memory
        _spec_cache[fullname] = (spec, time.monotonic())
        _spec_cache.move_to_end(fullname)
        _spec_cache_prune_locked()
        
        # L2 cache: Disk (async, non-blocking)
        try:
            cache_file = _CACHE_L2_DIR / f"{fullname.replace('.', '_')}.spec"
            import pickle
            # Use protocol 5 for better performance
            with open(cache_file, 'wb') as f:
                pickle.dump(spec, f, protocol=5)
        except Exception:
            pass  # Fail silently for disk cache

def _spec_cache_clear(fullname: Optional[str] = None) -> None:
    """Clear spec cache entries."""
    with _spec_cache_lock:
        if fullname is None:
            _spec_cache.clear()
        else:
            _spec_cache.pop(fullname, None)

def _cache_spec_if_missing(fullname: str) -> None:
    """Ensure a ModuleSpec is cached for a known-good module."""
    if _spec_cache_get(fullname):
        return
    try:
        spec = importlib.util.find_spec(fullname)
    except Exception:
        spec = None
    if spec is not None:
        _spec_cache_put(fullname, spec)

def get_stdlib_module_set() -> set[str]:
    """Get the set of stdlib module names."""
    return _STDLIB_MODULE_SET.copy()

__all__ = [
    '_cached_stdlib_check',
    '_spec_cache_get',
    '_spec_cache_put',
    '_spec_cache_clear',
    '_spec_cache_prune_locked',
    '_cache_spec_if_missing',
    'get_stdlib_module_set',
]

