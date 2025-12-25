"""
Compatibility module for xwlazy.lazy imports.

This module provides backward compatibility for packages that import
from xwlazy.lazy instead of exonware.xwlazy.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

# Re-export commonly used functions from the main package
from exonware.xwlazy import (
    xwimport,
    config_package_lazy_install_enabled,
    config_module_lazy_load_enabled,
    enable_lazy_mode,
    disable_lazy_mode,
    is_lazy_mode_enabled,
)

__all__ = [
    'xwimport',
    'config_package_lazy_install_enabled',
    'config_module_lazy_load_enabled',
    'enable_lazy_mode',
    'disable_lazy_mode',
    'is_lazy_mode_enabled',
]

