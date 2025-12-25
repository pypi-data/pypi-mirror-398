"""
Async Execution Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Async execution strategy - async pip install using asyncio.
Uses shared utilities from common/services/install_async_utils.
"""

import sys
import asyncio
import subprocess
from typing import Any
from ...package.base import AInstallExecutionStrategy
from ...package.services.install_result import InstallResult, InstallStatus
from ...common.services.install_async_utils import async_install_package

class AsyncExecution(AInstallExecutionStrategy):
    """
    Async execution strategy - installs packages asynchronously using asyncio.
    
    Uses asyncio subprocess for non-blocking installation.
    Uses shared utilities from common/services/install_async_utils.
    """
    
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """
        Execute installation asynchronously.
        
        Note: This is a synchronous wrapper that runs async code.
        For true async, use the async methods directly.
        
        Args:
            package_name: Package name to install
            policy_args: Policy arguments
            
        Returns:
            InstallResult with success status
        """
        try:
            # Run async install in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(
                    self._async_install(package_name, policy_args),
                    loop
                )
                return future.result(timeout=600)  # 10 min timeout
            else:
                # If no loop running, use asyncio.run
                return asyncio.run(self._async_install(package_name, policy_args))
        except Exception as e:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error=str(e)
            )
    
    async def _async_install(self, package_name: str, policy_args: list[str]) -> InstallResult:
        """
        Async installation implementation.
        
        Args:
            package_name: Package name to install
            policy_args: Policy arguments
            
        Returns:
            InstallResult with success status
        """
        success, error_msg = await async_install_package(package_name, policy_args)
        
        if success:
            return InstallResult(
                package_name=package_name,
                success=True,
                status=InstallStatus.SUCCESS,
                source="pip-async"
            )
        else:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error=error_msg or "Unknown error"
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

