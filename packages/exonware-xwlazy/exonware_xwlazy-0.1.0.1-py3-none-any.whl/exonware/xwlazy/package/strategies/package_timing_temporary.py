"""
Temporary Timing Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Temporary timing - always uninstall after use (more aggressive than CLEAN).
"""

from typing import Any
from ...package.base import AInstallTimingStrategy

class TemporaryTiming(AInstallTimingStrategy):
    """
    Temporary timing strategy - always uninstalls after use (LazyInstallMode.TEMPORARY).
    
    More aggressive than CLEAN - always uninstalls packages after use.
    """
    
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be installed now.
        
        Temporary mode: Install when first needed.
        
        Args:
            package_name: Package name to check
            context: Context information (e.g., import error)
            
        Returns:
            True if should install now
        """
        return context is not None
    
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be uninstalled after use.
        
        Temporary mode: Always uninstall after use.
        
        Args:
            package_name: Package name to check
            context: Context information (ignored)
            
        Returns:
            True (always uninstall)
        """
        return True
    
    def get_install_priority(self, packages: list[str]) -> list[str]:
        """
        Get priority order for installing packages.
        
        Temporary mode: Install in order requested.
        
        Args:
            packages: List of package names
            
        Returns:
            Priority-ordered list
        """
        return packages

