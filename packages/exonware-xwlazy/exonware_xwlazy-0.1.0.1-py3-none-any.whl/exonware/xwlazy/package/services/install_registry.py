"""
Installer Registry

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Registry to manage separate lazy installer instances per package.
"""

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .lazy_installer import LazyInstaller

class LazyInstallerRegistry:
    """Registry to manage separate lazy installer instances per package."""
    _instances: dict[str, 'LazyInstaller'] = {}
    _lock = threading.RLock()
    
    @classmethod
    def get_instance(cls, package_name: str = 'default') -> 'LazyInstaller':
        """
        Get or create a lazy installer instance for a package.
        
        Args:
            package_name: Package name for isolation
            
        Returns:
            LazyInstaller instance for the package
        """
        with cls._lock:
            if package_name not in cls._instances:
                # Lazy import to avoid circular dependency
                from .lazy_installer import LazyInstaller
                cls._instances[package_name] = LazyInstaller(package_name)
            return cls._instances[package_name]
    
    @classmethod
    def get_all_instances(cls) -> dict[str, 'LazyInstaller']:
        """
        Get all lazy installer instances.
        
        Returns:
            Dict mapping package_name -> LazyInstaller
        """
        with cls._lock:
            return cls._instances.copy()

__all__ = ['LazyInstallerRegistry']

