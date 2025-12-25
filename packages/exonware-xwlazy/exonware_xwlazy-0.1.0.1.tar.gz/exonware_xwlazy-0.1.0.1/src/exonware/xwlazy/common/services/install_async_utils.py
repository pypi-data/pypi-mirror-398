"""
Installation Async Utilities

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Shared utilities for async installation operations.
Used by both execution strategies and LazyInstaller.
"""

import os
import sys
import json
import asyncio
import subprocess
from typing import Optional

# Lazy imports
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ..logger import get_logger
    return get_logger("xwlazy.install_async_utils")

logger = None

def _ensure_logging_initialized():
    """Ensure logging utilities are initialized."""
    global logger
    if logger is None:
        logger = _get_logger()
        # Fallback if get_logger returns None (should not happen but safety first)
        if logger is None:
            import logging
            logger = logging.getLogger("xwlazy.install_async_utils.fallback")
            logger.addHandler(logging.NullHandler())

async def get_package_size_mb(package_name: str) -> Optional[float]:
    """
    Get package size in MB by checking pip show or download size.
    
    Args:
        package_name: Package name to check
        
    Returns:
        Size in MB or None if cannot determine
    """
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, '-m', 'pip', 'show', package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        
        if process.returncode == 0:
            output = stdout.decode()
            for line in output.split('\n'):
                if line.startswith('Location:'):
                    location = line.split(':', 1)[1].strip()
                    try:
                        total_size = 0
                        for dirpath, dirnames, filenames in os.walk(location):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                if os.path.exists(filepath):
                                    total_size += os.path.getsize(filepath)
                        return total_size / (1024 * 1024)
                    except Exception:
                        pass
    except Exception:
        pass
    
    # Fallback: Try to get download size from PyPI
    try:
        import urllib.request
        url = f"https://pypi.org/pypi/{package_name}/json"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            if 'urls' in data and data['urls']:
                latest = data['urls'][0]
                if 'size' in latest:
                    return latest['size'] / (1024 * 1024)
    except Exception:
        pass
    
    return None

async def async_install_package(
    package_name: str,
    policy_args: Optional[list] = None
) -> tuple[bool, Optional[str]]:
    """
    Install a package asynchronously using asyncio subprocess.
    
    Args:
        package_name: Package name to install
        policy_args: Optional policy arguments (index URLs, trusted hosts, etc.)
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    _ensure_logging_initialized()
    try:
        pip_args = [sys.executable, '-m', 'pip', 'install']
        if policy_args:
            pip_args.extend(policy_args)
        pip_args.append(package_name)
        
        process = await asyncio.create_subprocess_exec(
            *pip_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return True, None
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Failed to install {package_name}: {error_msg}")
            return False, error_msg
    except Exception as e:
        logger.error(f"Error in async install of {package_name}: {e}")
        return False, str(e)

async def async_uninstall_package(
    package_name: str,
    quiet: bool = True
) -> bool:
    """
    Uninstall a package asynchronously.
    
    Args:
        package_name: Package name to uninstall
        quiet: If True, suppress output
        
    Returns:
        True if successful, False otherwise
    """
    _ensure_logging_initialized()
    try:
        pip_args = [sys.executable, '-m', 'pip', 'uninstall', '-y', package_name]
        
        process = await asyncio.create_subprocess_exec(
            *pip_args,
            stdout=asyncio.subprocess.PIPE if quiet else None,
            stderr=asyncio.subprocess.PIPE if quiet else None
        )
        
        await process.communicate()
        
        if process.returncode == 0:
            if not quiet:
                logger.info(f"Uninstalled {package_name}")
            return True
        return False
    except Exception as e:
        logger.debug(f"Failed to uninstall {package_name}: {e}")
        return False

__all__ = [
    'get_package_size_mb',
    'async_install_package',
    'async_uninstall_package',
]

