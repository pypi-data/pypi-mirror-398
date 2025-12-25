"""
Cached Execution Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Cached execution strategy - install from cached tree.
Uses shared utilities from common/services/install_cache_utils.
"""

import sys
import subprocess
from pathlib import Path
from typing import Any, Optional
from ...package.base import AInstallExecutionStrategy
from ...package.services.install_result import InstallResult, InstallStatus
from ...common.services.install_cache_utils import (
    get_cache_dir,
    install_from_cached_tree,
)

class CachedExecution(AInstallExecutionStrategy):
    """
    Cached execution strategy - installs packages from cached installation tree.
    
    Fastest installation method - copies from pre-extracted cache.
    Uses shared utilities from common/services/install_cache_utils.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize cached execution strategy.
        
        Args:
            cache_dir: Optional cache directory for installation trees
        """
        self._cache_dir = cache_dir
    
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """
        Execute installation from cached tree.
        
        Args:
            package_name: Package name to install
            policy_args: Policy arguments (ignored for cached install)
            
        Returns:
            InstallResult with success status
        """
        success = install_from_cached_tree(package_name, self._cache_dir)
        
        if success:
            return InstallResult(
                package_name=package_name,
                success=True,
                status=InstallStatus.SUCCESS,
                source="cache-tree"
            )
        else:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error="Cached installation tree not found"
            )
    
    def execute_uninstall(self, package_name: str) -> bool:
        """
        Execute uninstallation using pip.
        
        Args:
            package_name: Package name to uninstall
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', package_name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.returncode == 0
        except Exception:
            return False

