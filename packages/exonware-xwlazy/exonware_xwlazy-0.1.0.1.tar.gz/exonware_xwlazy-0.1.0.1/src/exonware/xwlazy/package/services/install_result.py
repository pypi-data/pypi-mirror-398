"""
Install Result and Status

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Re-export installation result types from defs.py for backward compatibility.
"""

# Re-export from defs.py
from ...defs import InstallStatus, InstallResult

__all__ = ['InstallStatus', 'InstallResult']

