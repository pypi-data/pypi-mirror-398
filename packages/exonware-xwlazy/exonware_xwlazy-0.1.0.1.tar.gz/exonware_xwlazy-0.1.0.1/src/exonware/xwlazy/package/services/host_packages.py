"""Lightweight helpers for registering host packages with xwlazy."""

from __future__ import annotations

import os
import sys
import functools
from typing import Iterable, Sequence

# Lazy imports to avoid circular dependency
def _get_config_package_lazy_install_enabled():
    """Get config_package_lazy_install_enabled (lazy import to avoid circular dependency)."""
    from ...facade import config_package_lazy_install_enabled
    return config_package_lazy_install_enabled

def _get_install_import_hook():
    """Get install_import_hook (lazy import to avoid circular dependency)."""
    from ...facade import install_import_hook
    return install_import_hook

def _get_is_lazy_install_enabled():
    """Get is_lazy_install_enabled (lazy import to avoid circular dependency)."""
    from ...facade import is_lazy_install_enabled
    return is_lazy_install_enabled

def _get_register_lazy_module_methods():
    """Get register_lazy_module_methods (lazy import to avoid circular dependency)."""
    from ...facade import register_lazy_module_methods
    return register_lazy_module_methods

def _get_register_lazy_module_prefix():
    """Get register_lazy_module_prefix (lazy import to avoid circular dependency)."""
    from ...facade import register_lazy_module_prefix
    return register_lazy_module_prefix

# Note: LazyMetaPathFinder is implemented in module/meta_path_finder.py
# For now, create a placeholder
class LazyMetaPathFinder:
    """Placeholder for LazyMetaPathFinder - to be implemented in hooks domain."""
    def __init__(self, package_name: str):
        self.package_name = package_name
    
    def _enhance_classes_with_class_methods(self, module):
        """Enhance classes with lazy-aware static/class method behavior."""
        
        for name, cls in vars(module).items():
            if not isinstance(cls, type):
                continue
            
            # Skip if not a serializer (heuristic)
            if not name.endswith('Serializer'):
                continue

            # Methods to patch
            for method_name in ['encode', 'decode']:
                if not hasattr(cls, method_name):
                    continue

                original_method = getattr(cls, method_name)
                if not callable(original_method):
                    continue
                
                # Check if already patched to avoid recursion/duplication
                if getattr(original_method, '_is_lazy_wrapper', False):
                    continue

                @functools.wraps(original_method)
                def wrapper(first_arg, *args, **kwargs):
                    # Check if first_arg is 'self' (instance of cls)
                    if isinstance(first_arg, cls):
                        return original_method(first_arg, *args, **kwargs)
                    
                    # Called as class method or static usage: Class.encode(data)
                    # first_arg is actually the data
                    # Instantiate to trigger lazy loading (__init__)
                    instance = cls()
                    return original_method(instance, first_arg, *args, **kwargs)
                
                wrapper._is_lazy_wrapper = True
                setattr(cls, method_name, wrapper)

_TRUTHY = {"1", "true", "yes", "on"}
_REGISTERED: dict[str, dict[str, tuple[str, ...]]] = {}

def _normalized(items: Iterable[str]) -> tuple[str, ...]:
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return tuple(seen)

def register_host_package(
    package_name: str,
    module_prefixes: Iterable[str] = (),
    method_prefixes: Iterable[str] = (),
    method_names: Sequence[str] = ("encode", "decode"),
    auto_config: bool = True,
    env_var: str | None = None,
) -> None:
    """
    Register a host package (e.g., xwsystem) with xwlazy.

    Args:
        package_name: Host package name.
        module_prefixes: Prefixes that should be lazily wrapped.
        method_prefixes: Prefixes whose classes expose class-level helpers.
        method_names: Methods to expose at class level (default encode/decode).
        auto_config: If True, record lazy config but do not install hook yet.
        env_var: Optional environment variable to force enable (defaults to
                 ``{PACKAGE}_LAZY_INSTALL``).
    """
    package_name = package_name.lower()

    module_prefixes = _normalized(module_prefixes)
    method_prefixes = _normalized(method_prefixes)
    _REGISTERED[package_name] = {
        "module_prefixes": module_prefixes,
        "method_prefixes": method_prefixes,
    }

    for prefix in module_prefixes:
        _get_register_lazy_module_prefix()(prefix)

    for prefix in method_prefixes:
        _get_register_lazy_module_methods()(prefix, tuple(method_names))

    if auto_config:
        # Detect if lazy should be enabled (checks keyword, marker package, etc.)
        _get_config_package_lazy_install_enabled()(package_name, enabled=None, install_hook=False)
        
        # If detection found that lazy should be enabled, install the hook automatically
        if _get_is_lazy_install_enabled()(package_name):
            try:
                _get_install_import_hook()(package_name)
            except Exception:
                # Best-effort: package import must continue even if hook installation fails
                pass

    _apply_wrappers_for_loaded_modules(package_name, module_prefixes, method_prefixes)

    env_key = env_var or f"{package_name.upper()}_LAZY_INSTALL"
    flag = os.environ.get(env_key, "")
    if flag.strip().lower() in _TRUTHY:
        _get_config_package_lazy_install_enabled()(package_name, enabled=True)
        try:
            _get_install_import_hook()(package_name)
        except Exception:
            # Best-effort: package import must continue even if hook installation fails
            pass

def refresh_host_package(package_name: str) -> None:
    """Re-apply wrappers for a registered package."""
    data = _REGISTERED.get(package_name.lower())
    if not data:
        return
    _apply_wrappers_for_loaded_modules(
        package_name,
        data["module_prefixes"],
        data["method_prefixes"],
    )

def _apply_wrappers_for_loaded_modules(
    package_name: str,
    module_prefixes: Iterable[str],
    method_prefixes: Iterable[str],
) -> None:
    """Enhance already-imported modules so encode/decode helpers work immediately."""
    prefixes = _normalized((*module_prefixes, *method_prefixes))
    if not prefixes:
        return

    finder = LazyMetaPathFinder(package_name)
    for module_name, module in list(sys.modules.items()):
        if not isinstance(module_name, str) or module is None:
            continue
        if any(module_name.startswith(prefix) for prefix in prefixes):
            try:
                finder._enhance_classes_with_class_methods(module)  # type: ignore[attr-defined]
            except Exception:
                continue
