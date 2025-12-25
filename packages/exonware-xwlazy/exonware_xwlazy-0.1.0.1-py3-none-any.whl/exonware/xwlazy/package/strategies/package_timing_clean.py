"""
Clean Timing Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Clean timing - install on usage + uninstall after completion.
"""

from typing import Any
from ...package.base import AInstallTimingStrategy

class CleanTiming(AInstallTimingStrategy):
    """
    Clean timing strategy - installs on usage + uninstalls after completion (LazyInstallMode.CLEAN).
    
    Installs package when needed, then uninstalls after use to keep environment clean.
    """
    
    def should_install_now(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be installed now.
        
        Clean mode: Install when first needed.
        
        Args:
            package_name: Package name to check
            context: Context information (e.g., import error)
            
        Returns:
            True if should install now
        """
        # In clean mode, install when first needed
        return context is not None
    
    def should_uninstall_after(self, package_name: str, context: Any) -> bool:
        """
        Determine if package should be uninstalled after use.
        
        Clean mode: Uninstall after use.
        
        Args:
            package_name: Package name to check
            context: Context information
            
        Returns:
            True (uninstall after use)
        """
        return True
    
    def get_install_priority(self, packages: list[str]) -> list[str]:
        """
        Get priority order for installing packages.
        
        Clean mode: Install in order requested.
        
        Args:
            packages: List of package names
            
        Returns:
            Priority-ordered list
        """
        return packages

