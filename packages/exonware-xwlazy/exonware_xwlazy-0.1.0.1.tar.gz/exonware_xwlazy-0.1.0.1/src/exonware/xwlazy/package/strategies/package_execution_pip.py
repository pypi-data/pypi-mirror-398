"""
Pip Execution Strategy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Pip execution strategy - direct pip install.
"""

import sys
import subprocess
from typing import Any
from ...package.base import AInstallExecutionStrategy
from ...package.services.install_result import InstallResult, InstallStatus

class PipExecution(AInstallExecutionStrategy):
    """
    Pip execution strategy - installs packages directly using pip.
    
    This is the default execution strategy that uses pip install.
    """
    
    def execute_install(self, package_name: str, policy_args: list[str]) -> Any:
        """
        Execute installation using pip.
        
        Args:
            package_name: Package name to install
            policy_args: Policy arguments (index URLs, trusted hosts, etc.)
            
        Returns:
            InstallResult with success status
        """
        try:
            pip_args = [sys.executable, '-m', 'pip', 'install']
            if policy_args:
                pip_args.extend(policy_args)
            pip_args.append(package_name)
            
            result = subprocess.run(
                pip_args,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                return InstallResult(
                    package_name=package_name,
                    success=True,
                    status=InstallStatus.SUCCESS,
                    source="pip"
                )
            else:
                return InstallResult(
                    package_name=package_name,
                    success=False,
                    status=InstallStatus.FAILED,
                    error=result.stderr or "Unknown error"
                )
        except subprocess.CalledProcessError as e:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error=e.stderr or str(e)
            )
        except Exception as e:
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error=str(e)
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

