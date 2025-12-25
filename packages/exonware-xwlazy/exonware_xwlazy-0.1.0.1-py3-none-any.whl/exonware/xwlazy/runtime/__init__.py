"""
Runtime Services Module

This module provides concrete implementations for runtime services.
Main facade: XWRuntimeHelper extends ARuntimeHelper
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == 'XWRuntimeHelper':
        from .facade import XWRuntimeHelper
        return XWRuntimeHelper
    if name == 'XWRuntime':  # Backward compatibility alias
        from .facade import XWRuntimeHelper
        return XWRuntimeHelper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['XWRuntimeHelper', 'XWRuntime']  # XWRuntime is backward compatibility alias
