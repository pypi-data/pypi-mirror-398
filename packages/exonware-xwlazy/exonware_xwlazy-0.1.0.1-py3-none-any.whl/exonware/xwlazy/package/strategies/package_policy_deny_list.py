"""
Deny List Policy Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Deny list policy - blocks packages in the deny list.
"""

from typing import
from ...package.base import APolicyStrategy

class DenyListPolicy(APolicyStrategy):
    """
    Deny list policy strategy - blocks packages in the deny list.
    
    Packages in the deny list cannot be installed.
    """
    
    def __init__(self, denied_packages: set[str]):
        """
        Initialize deny list policy.
        
        Args:
            denied_packages: Set of denied package names
        """
        self._denied = {pkg.lower() for pkg in denied_packages}
    
    def is_allowed(self, package_name: str) -> tuple[bool, str]:
        """
        Check if package is allowed to be installed.
        
        Args:
            package_name: Package name to check
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        if package_name.lower() in self._denied:
            return (False, f"Package '{package_name}' is in deny list")
        return (True, f"Package '{package_name}' is not in deny list")
    
    def get_pip_args(self, package_name: str) -> list[str]:
        """
        Get pip arguments based on policy.
        
        Args:
            package_name: Package name
            
        Returns:
            List of pip arguments (empty for deny list policy)
        """
        return []

