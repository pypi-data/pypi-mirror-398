"""
Host-facing configuration module for xwlazy.

This module provides the get_conf_module function that host packages
like xwsystem use to enable lazy mode via exonware.conf.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
"""

# Re-export from the actual implementation location
from ..package.conf import get_conf_module

__all__ = ['get_conf_module']

