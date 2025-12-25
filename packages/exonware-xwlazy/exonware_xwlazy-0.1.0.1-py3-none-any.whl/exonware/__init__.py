"""
exonware package - Enterprise-grade Python framework ecosystem

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Generation Date: 2025-01-03

This is a namespace package allowing multiple exonware subpackages
to coexist (xwsystem, xwnode, xwdata, xwlazy, etc.)
"""

# Make this a namespace package FIRST
# This allows both exonware.xwsystem and exonware.xwlazy to coexist
__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Import version from xwlazy - required, no fallback
from exonware.xwlazy.version import __version__

__author__ = 'Eng. Muhammad AlShehri'
__email__ = 'connect@exonware.com'
__company__ = 'eXonware.com'

# NOW enable lazy mode (after namespace package is set up)
import sys
import importlib
try:
    # Use importlib to import after namespace is ready
    if 'exonware.xwlazy' not in sys.modules:
        xwlazy_module = importlib.import_module('exonware.xwlazy')
        auto_enable_lazy = getattr(xwlazy_module, 'auto_enable_lazy', None)
        if auto_enable_lazy:
            auto_enable_lazy("xwsystem", mode="smart")
            print("✅ Lazy mode enabled for xwsystem")
    else:
        # Module already loaded, use it directly
        from exonware.xwlazy import auto_enable_lazy
        auto_enable_lazy("xwsystem", mode="smart")
        print("✅ Lazy mode enabled for xwsystem")
except (ImportError, AttributeError):
    print("❌ Lazy mode not enabled for xwsystem (xwlazy not installed)")
    pass  # xwlazy not installed - silently continue