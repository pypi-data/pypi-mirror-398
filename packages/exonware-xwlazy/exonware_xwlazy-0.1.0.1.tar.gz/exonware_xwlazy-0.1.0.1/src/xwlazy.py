"""
Convenience module for importing xwlazy.

This allows users to import the library in two ways:
1. import exonware.xwlazy
2. import xwlazy  # This convenience import

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Generation Date: 10-Oct-2025

DESIGN RATIONALE FOR WILDCARD IMPORT:
This file intentionally uses a wildcard import (from exonware.xwlazy import *) as an 
alias import technique. This is an EXCEPTION to the explicit imports rule because:

1. This is a convenience alias module, not core functionality
2. The wildcard import is the standard Python pattern for creating import aliases
3. It provides the same functionality as the main module without code duplication
4. All actual functionality is defined in the main exonware.xwlazy module
5. This approach is commonly used in Python libraries for backward compatibility

The wildcard import here is intentional and follows Python best practices for alias modules.
"""

# Import everything from the main package
from exonware.xwlazy import *  # noqa: F401, F403

# Import version info
from exonware.xwlazy.version import (
    __version__,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
    VERSION_BUILD,
    VERSION_SUFFIX,
    VERSION_STRING,
    get_version,
    get_version_info,
    get_version_dict,
    is_dev_version,
    is_release_version,
)
