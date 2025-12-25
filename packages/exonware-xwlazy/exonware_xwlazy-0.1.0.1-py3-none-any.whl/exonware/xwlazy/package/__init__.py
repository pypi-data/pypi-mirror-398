"""
Package Operations Module

This module provides concrete implementations for package operations.
Main facade: XWPackageHelper extends APackageHelper
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name: str):
    if name == 'XWPackageHelper':
        from .facade import XWPackageHelper
        return XWPackageHelper
    if name == 'XWPackage':  # Backward compatibility alias
        from .facade import XWPackageHelper
        return XWPackageHelper
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ['XWPackageHelper', 'XWPackage']  # XWPackage is backward compatibility alias
