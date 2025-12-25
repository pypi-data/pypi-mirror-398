"""
Permissive Policy Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Permissive policy - allows all packages (default).
"""

from typing import
from ...package.base import APolicyStrategy

class PermissivePolicy(APolicyStrategy):
    """
    Permissive policy strategy - allows all packages.
    
    This is the default policy that doesn't restrict any packages.
    """
    
    def is_allowed(self, package_name: str) -> tuple[bool, str]:
        """
        Check if package is allowed to be installed.
        
        Args:
            package_name: Package name to check
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        return (True, "Permissive policy allows all packages")
    
    def get_pip_args(self, package_name: str) -> list[str]:
        """
        Get pip arguments based on policy.
        
        Args:
            package_name: Package name
            
        Returns:
            List of pip arguments (empty for permissive policy)
        """
        return []

