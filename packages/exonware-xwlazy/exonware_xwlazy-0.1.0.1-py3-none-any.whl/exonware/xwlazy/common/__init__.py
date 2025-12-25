"""
#exonware/xwlazy/src/exonware/xwlazy/common/__init__.py

Common utilities shared across package, module, and runtime.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025
"""

from .logger import (
    get_logger,
    log_event,
    print_formatted,
    format_message,
    is_log_category_enabled,
    set_log_category,
    set_log_categories,
    get_log_categories,
    XWLazyFormatter,
)

from .cache import (
    MultiTierCache,
    BytecodeCache,
    InstallationCache,
)

from .utils import (
    find_project_root,
    find_config_file,
)

__all__ = [
    # Logger
    'get_logger',
    'log_event',
    'print_formatted',
    'format_message',
    'is_log_category_enabled',
    'set_log_category',
    'set_log_categories',
    'get_log_categories',
    'XWLazyFormatter',
    # Cache
    'MultiTierCache',
    'BytecodeCache',
    'InstallationCache',
    # Utils
    'find_project_root',
    'find_config_file',
]

