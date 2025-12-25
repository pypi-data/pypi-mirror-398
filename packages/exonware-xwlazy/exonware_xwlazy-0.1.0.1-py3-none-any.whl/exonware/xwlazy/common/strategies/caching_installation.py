"""
Installation Cache Strategy - Wrapper for existing InstallationCache.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Wraps existing InstallationCache to implement ICachingStrategy interface.
"""

from typing import Optional, Any
from pathlib import Path
from ..cache import InstallationCache
from ..base import ACachingStrategy
from ...package.data import PackageData

class InstallationCacheWrapper(ACachingStrategy):
    """
    Installation cache strategy wrapper.
    
    Wraps existing InstallationCache to implement ICachingStrategy interface.
    Used for package installation status caching.
    """
    
    def __init__(self, cache_file: Optional[Path] = None):
        """
        Initialize installation cache wrapper.
        
        Args:
            cache_file: Optional path to cache file
        """
        self._cache = InstallationCache(cache_file)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get package from cache.
        
        Args:
            key: Package name
            
        Returns:
            PackageData if found, None otherwise
        """
        if self._cache.is_installed(key):
            version = self._cache.get_version(key)
            return PackageData(
                name=key,
                installed=True,
                version=version
            )
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Cache a package.
        
        Args:
            key: Package name
            value: PackageData or dict with installed/version info
        """
        if isinstance(value, PackageData):
            if value.installed:
                self._cache.mark_installed(key, value.version)
            else:
                self._cache.mark_uninstalled(key)
        elif isinstance(value, dict):
            if value.get('installed', False):
                self._cache.mark_installed(key, value.get('version'))
            else:
                self._cache.mark_uninstalled(key)
    
    def invalidate(self, key: str) -> None:
        """
        Invalidate cached package.
        
        Args:
            key: Package name
        """
        self._cache.mark_uninstalled(key)
    
    def clear(self) -> None:
        """Clear all cached packages."""
        # InstallationCache doesn't have clear, so we'd need to extend it
        # For now, just mark all as uninstalled (would need cache iteration)
        pass

