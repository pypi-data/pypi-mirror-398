"""
Common utility functions for xwlazy.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

This module provides shared utility functions used across xwlazy,
including path operations and project root detection.
"""

import sys
from pathlib import Path
from typing import Optional


def find_project_root(start_path: Optional[Path] = None) -> Path:
    """
    Find the project root directory by looking for markers.
    
    Package-agnostic: Finds root from running script location, not xwlazy's location.
    This function is designed to work with any project that uses xwlazy.
    
    Args:
        start_path: Optional starting path. If None, attempts to find from:
            1. __main__ module location
            2. sys.path[0] (script directory)
            3. Current working directory
    
    Returns:
        Path to the project root directory
        
    Examples:
        >>> root = find_project_root()
        >>> # Finds pyproject.toml or setup.py from running script
        
        >>> root = find_project_root(Path(__file__).parent)
        >>> # Finds from specific starting path
    """
    start_paths = []
    
    # If explicit start path provided, use it first
    if start_path:
        try:
            start_paths.append(start_path.resolve())
        except (ValueError, OSError):
            pass
    
    # Option 1: Use __main__ module location if available
    if '__main__' in sys.modules:
        main_module = sys.modules['__main__']
        if hasattr(main_module, '__file__') and main_module.__file__:
            try:
                main_path = Path(main_module.__file__).resolve().parent
                start_paths.append(main_path)
            except (ValueError, OSError):
                pass
    
    # Option 2: Use sys.path[0] (script directory)
    if sys.path and sys.path[0]:
        try:
            script_path = Path(sys.path[0]).resolve()
            if script_path.exists():
                start_paths.append(script_path)
        except (ValueError, OSError):
            pass
    
    # Option 3: Use current working directory
    try:
        cwd = Path.cwd().resolve()
        if cwd.exists():
            start_paths.append(cwd)
    except (OSError, ValueError):
        pass
    
    # Option 4: Fallback to xwlazy location (for backwards compatibility)
    try:
        xwlazy_path = Path(__file__).parent.parent.parent.parent
        if xwlazy_path.exists():
            start_paths.append(xwlazy_path)
    except (ValueError, OSError):
        pass
    
    # Try each starting path
    for start_path_item in start_paths:
        current = start_path_item
        max_levels = 20  # Prevent infinite loops
        levels = 0
        
        while current != current.parent and levels < max_levels:
            # Check for project markers
            markers = ['pyproject.toml', 'setup.py', 'requirements.txt', '.git']
            if any((current / marker).exists() for marker in markers):
                return current
            current = current.parent
            levels += 1
    
    # Final fallback: current working directory
    try:
        return Path.cwd().resolve()
    except (OSError, ValueError):
        # Ultimate fallback: return the xwlazy package directory
        return Path(__file__).parent.parent.parent.parent


def find_config_file(filename: str, start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Find a configuration file by walking up from the start path.
    
    Args:
        filename: Name of the config file to find (e.g., 'pyproject.toml', 'requirements.txt')
        start_path: Optional starting path. If None, uses find_project_root()
    
    Returns:
        Path to the config file if found, None otherwise
        
    Examples:
        >>> pyproject = find_config_file('pyproject.toml')
        >>> requirements = find_config_file('requirements.txt')
    """
    if start_path is None:
        root = find_project_root()
    else:
        root = start_path
    
    # Check in root and walk up
    current = root
    max_levels = 10
    levels = 0
    
    while current != current.parent and levels < max_levels:
        config_path = current / filename
        if config_path.exists():
            return config_path
        current = current.parent
        levels += 1
    
    return None


__all__ = ['find_project_root', 'find_config_file']

