"""
Module Operations Module

This module provides concrete implementations for module operations.
Main facade: XWModuleHelper extends AModuleHelper
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == 'XWModuleHelper':
        from .facade import XWModuleHelper
        return XWModuleHelper
    if name == 'XWModule':  # Backward compatibility alias
        from .facade import XWModuleHelper
        return XWModuleHelper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['XWModuleHelper', 'XWModule']  # XWModule is backward compatibility alias
