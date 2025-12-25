"""
Full Timing Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Full timing - install all dependencies upfront.
"""

from typing import Any
from ...package.base import AInstallTimingStrategy

class FullTiming(AInstallTimingStrategy):
    """
    Full timing strategy - installs all packages upfront (LazyInstallMode.FULL).
    
    Batch installs all dependencies in parallel on initialization.
    """
    
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be installed now.
        
        Full mode: Install all upfront.
        
        Args:
            package_name: Package name to check
            context: Context information (ignored in full mode)
            
        Returns:
            True (always install upfront)
        """
        return True
    
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be uninstalled after use.
        
        Full mode: Keep installed after use.
        
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
        
        Full mode: Install all in parallel (no specific order).
        
        Args:
            packages: List of package names
            
        Returns:
            Priority-ordered list (original order)
        """
        return packages

