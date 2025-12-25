"""
Smart Timing Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Smart timing - install on first usage (on-demand).
"""

from typing import Any
from ...package.base import AInstallTimingStrategy
from ...defs import LazyInstallMode

class SmartTiming(AInstallTimingStrategy):
    """
    Smart timing strategy - installs packages on-demand (LazyInstallMode.SMART).
    
    Installs package when first needed, then caches the result.
    """
    
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be installed now.
        
        Smart mode: Install when first needed.
        
        Args:
            package_name: Package name to check
            context: Context information (e.g., import error)
            
        Returns:
            True if should install now
        """
        # In smart mode, install when first needed (context indicates need)
        return context is not None
    
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be uninstalled after use.
        
        Smart mode: Keep installed after use.
        
        Args:
            package_name: Package name to check
            context: Context information
            
        Returns:
            False (keep installed)
        """
        return False
    
    def get_install_priority(self, packages: list[str]) -> list[str]:
        """
        Get priority order for installing packages.
        
        Smart mode: Install in order requested.
        
        Args:
            packages: List of package names
            
        Returns:
            Priority-ordered list
        """
        return packages

