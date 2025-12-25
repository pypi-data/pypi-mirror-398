"""
Installation Utilities

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Utility functions for installation operations.
"""

import os
import sys
import inspect
import subprocess
from pathlib import Path
from typing import Optional

def get_trigger_file() -> Optional[str]:
    """
    Get the file that triggered the import (from call stack).
    
    Returns:
        Filename that triggered the import, or None
    """
    try:
        # Walk up the call stack to find the first non-xwlazy file
        # Look for files in xwsystem, xwnode, xwdata, or user code
        for frame_info in inspect.stack():
            filename = frame_info.filename
            # Skip xwlazy internal files and importlib
            if ('xwlazy' not in filename and 
                'importlib' not in filename and 
                '<frozen' not in filename and
                filename.endswith('.py')):
                # Return just the filename, not full path
                basename = os.path.basename(filename)
                # If it's a serialization file, use that
                if 'serialization' in filename or 'formats' in filename:
                    # Extract the format name (e.g., bson.py -> BsonSerializer)
                    if basename.endswith('.py'):
                        basename = basename[:-3]  # Remove .py
                    return f"{basename.capitalize()}Serializer" if basename else None
                return basename
    except Exception:
        pass
    return None

def is_externally_managed() -> bool:
    """
    Check if Python environment is externally managed (PEP 668).
    
    Returns:
        True if environment is externally managed
    """
    marker_file = Path(sys.prefix) / "EXTERNALLY-MANAGED"
    return marker_file.exists()

def check_pip_audit_available() -> bool:
    """
    Check if pip-audit is available for vulnerability scanning.
    
    Returns:
        True if pip-audit is available
    """
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'pip-audit' in result.stdout
    except Exception:
        return False

__all__ = ['get_trigger_file', 'is_externally_managed', 'check_pip_audit_available']

