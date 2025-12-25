"""
Wheel Execution Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Wheel execution strategy - install from wheel files.
Uses shared utilities from common/services/install_cache_utils.
"""

import sys
import subprocess
from pathlib import Path
from typing import Any, Optional
from ...package.base import AInstallExecutionStrategy
from ...package.services.install_result import InstallResult, InstallStatus
from ...common.services.install_cache_utils import (
    get_wheel_path,
    ensure_cached_wheel,
    pip_install_from_path,
)

class WheelExecution(AInstallExecutionStrategy):
    """
    Wheel execution strategy - installs packages from wheel files.
    
    Downloads wheel first, then installs from local wheel file.
    Uses shared utilities from common/services/install_cache_utils.
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize wheel execution strategy.
        
        Args:
            cache_dir: Optional cache directory for wheels
        """
        self._cache_dir = cache_dir
    
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """
        Execute installation from wheel file.
        
        Args:
            package_name: Package name to install
            policy_args: Policy arguments
            
        Returns:
            InstallResult with success status
        """
        # Check if wheel already exists
        wheel_path = get_wheel_path(package_name, self._cache_dir)
        
        if not wheel_path.exists():
            # Download wheel first
            wheel_path = ensure_cached_wheel(package_name, policy_args, self._cache_dir)
            if wheel_path is None:
                return InstallResult(
                    package_name=package_name,
                    success=False,
                    status=InstallStatus.FAILED,
                    error="Failed to download wheel"
                )
        
        # Install from wheel
        success = pip_install_from_path(wheel_path, policy_args)
        
        if success:
            return InstallResult(
                package_name=package_name,
                success=True,
                status=InstallStatus.SUCCESS,
                source="wheel"
            )
        else:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error="Failed to install from wheel"
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

