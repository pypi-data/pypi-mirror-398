"""
Installer Engine

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Unified async execution engine for install operations.
"""

import os
import sys
import asyncio
import threading
import importlib.metadata
from typing import Optional, Callable

from .install_result import InstallResult, InstallStatus
from .install_policy import LazyInstallPolicy
from ...common.cache import InstallationCache
from .config_manager import LazyInstallConfig
from ...defs import LazyInstallMode

# Lazy import to avoid circular dependency
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.installer_engine")

logger = None  # Will be initialized on first use

class InstallerEngine:
    """
    Unified async execution engine for install operations.
    
    Features:
    - Parallel async execution for installs (waits for all to complete)
    - Integration with InstallCache and InstallPolicy
    - Support for all install modes (SMART, FULL, CLEAN, TEMPORARY, SIZE_AWARE, etc.)
    - Progress tracking and error handling
    - Retry logic with exponential backoff
    """
    
    def __init__(self, package_name: str = 'default'):
        """
        Initialize installer engine.
        
        Args:
            package_name: Package name for isolation
        """
        self._package_name = package_name
        self._install_cache = InstallationCache()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._active_installs: set[str] = set()  # Track active installs to prevent duplicates
        
        # Get install mode from config
        self._mode = LazyInstallConfig.get_install_mode(package_name) or LazyInstallMode.SMART
        
        # Initialize logger
        global logger
        if logger is None:
            logger = _get_logger()
    
    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure async event loop is running in background thread."""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name=f"InstallerEngine-{self._package_name}"
            )
            self._loop_thread.start()
        return self._loop
    
    def _run_loop(self):
        """Run event loop in background thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    def _get_installed_version(self, package_name: str) -> Optional[str]:
        """Get installed version of a package."""
        try:
            dist = importlib.metadata.distribution(package_name)
            return dist.version
        except importlib.metadata.PackageNotFoundError:
            return None
    
    async def _install_single(
        self,
        package_name: str,
        module_name: Optional[str] = None,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ) -> InstallResult:
        """
        Install a single package asynchronously.
        
        Args:
            package_name: Package name to install
            module_name: Optional module name (for context)
            max_retries: Maximum retry attempts
            initial_delay: Initial delay before retry (exponential backoff)
            
        Returns:
            InstallResult with success status and details
        """
        # Prevent duplicate installs
        with self._lock:
            if package_name in self._active_installs:
                logger.debug(f"Install already in progress for {package_name}, skipping")
                return InstallResult(
                    package_name=package_name,
                    success=False,
                    status=InstallStatus.SKIPPED,
                    error="Install already in progress"
                )
            self._active_installs.add(package_name)
        
        try:
            # Check cache first
            if self._install_cache.is_installed(package_name):
                version = self._install_cache.get_version(package_name)
                logger.debug(f"Package {package_name} already installed (cached)")
                return InstallResult(
                    package_name=package_name,
                    success=True,
                    status=InstallStatus.SUCCESS,
                    version=version,
                    source="cache"
                )
            
            # Security check
            allowed, reason = LazyInstallPolicy.is_package_allowed(
                self._package_name, package_name
            )
            if not allowed:
                return InstallResult(
                    package_name=package_name,
                    success=False,
                    status=InstallStatus.FAILED,
                    error=f"Security policy violation: {reason}"
                )
            
            # Check externally managed environment (PEP 668)
            from .install_utils import is_externally_managed
            if is_externally_managed():
                return InstallResult(
                    package_name=package_name,
                    success=False,
                    status=InstallStatus.FAILED,
                    error="Environment is externally managed (PEP 668)"
                )
            
            # SIZE_AWARE mode: Check package size
            if self._mode == LazyInstallMode.SIZE_AWARE:
                mode_config = LazyInstallConfig.get_mode_config(self._package_name)
                threshold_mb = mode_config.large_package_threshold_mb if mode_config else 50.0
                
                size_mb = await self._get_package_size_mb(package_name)
                if size_mb is not None and size_mb >= threshold_mb:
                    logger.warning(
                        f"Package '{package_name}' is {size_mb:.1f}MB "
                        f"(>= {threshold_mb}MB threshold), skipping in SIZE_AWARE mode"
                    )
                    return InstallResult(
                        package_name=package_name,
                        success=False,
                        status=InstallStatus.SKIPPED,
                        error=f"Package too large ({size_mb:.1f}MB >= {threshold_mb}MB)"
                    )
            
            # Retry logic with exponential backoff
            delay = initial_delay
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    # Get pip args from policy
                    policy_args = LazyInstallPolicy.get_pip_args(self._package_name) or []
                    pip_args = [
                        sys.executable, '-m', 'pip', 'install', package_name
                    ] + policy_args
                    
                    # Run pip install
                    process = await asyncio.create_subprocess_exec(
                        *pip_args,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0:
                        # Success - mark in cache
                        version = self._get_installed_version(package_name)
                        self._install_cache.mark_installed(package_name, version)
                        
                        logger.info(f"Successfully installed {package_name} (version: {version})")
                        
                        return InstallResult(
                            package_name=package_name,
                            success=True,
                            status=InstallStatus.SUCCESS,
                            version=version,
                            source="pip"
                        )
                    else:
                        error_msg = stderr.decode() if stderr else "Unknown error"
                        last_error = f"pip install failed: {error_msg}"
                        
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"Install attempt {attempt + 1} failed for {package_name}, "
                                f"retrying in {delay}s..."
                            )
                            await asyncio.sleep(delay)
                            delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"Failed to install {package_name} after {max_retries} attempts")
                            
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Install attempt {attempt + 1} failed for {package_name}: {e}, "
                            f"retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                    else:
                        logger.error(f"Error installing {package_name}: {e}")
            
            return InstallResult(
                package_name=package_name,
                success=False,
                status=InstallStatus.FAILED,
                error=last_error or "Unknown error"
            )
            
        finally:
            # Remove from active installs
            with self._lock:
                self._active_installs.discard(package_name)
    
    async def _get_package_size_mb(self, package_name: str) -> Optional[float]:
        """Get package size in MB (for SIZE_AWARE mode)."""
        try:
            cmd = [
                sys.executable, '-m', 'pip', 'show', package_name
            ]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                # Parse output to find size
                # This is a simplified version - actual implementation may vary
                output = stdout.decode()
                # Look for Size: field or estimate from download size
                # For now, return None (would need more sophisticated parsing)
                return None
        except Exception:
            pass
        return None
    
    def install_many(
        self,
        *package_names: str,
        callback: Optional[Callable[[str, InstallResult], None]] = None
    ) -> dict[str, InstallResult]:
        """
        Install multiple packages in parallel (async), but wait for all to complete.
        
        This is a SYNCHRONOUS method that internally uses async execution.
        It waits for all installations to complete before returning.
        
        Args:
            *package_names: Package names to install
            callback: Optional callback called as (package_name, result) for each completion
            
        Returns:
            Dict mapping package_name -> InstallResult
        """
        if not package_names:
            return {}
        
        # Filter out already installed packages
        to_install = []
        results = {}
        
        for name in package_names:
            if self._install_cache.is_installed(name):
                version = self._install_cache.get_version(name)
                result = InstallResult(
                    package_name=name,
                    success=True,
                    status=InstallStatus.SUCCESS,
                    version=version,
                    source="cache"
                )
                results[name] = result
                if callback:
                    callback(name, result)
            else:
                to_install.append(name)
        
        if not to_install:
            return results
        
        # Create async tasks for all packages
        loop = self._ensure_loop()
        
        async def _install_all():
            """Install all packages in parallel."""
            tasks = [
                self._install_single(name)
                for name in to_install
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        
        # Wait for all to complete (synchronous wait)
        try:
            future = asyncio.run_coroutine_threadsafe(_install_all(), loop)
            install_results = future.result(timeout=600)  # 10 min timeout
            
            # Process results
            for name, result in zip(to_install, install_results):
                if isinstance(result, Exception):
                    install_result = InstallResult(
                        package_name=name,
                        success=False,
                        status=InstallStatus.FAILED,
                        error=str(result)
                    )
                else:
                    install_result = result
                
                results[name] = install_result
                
                # Update cache for successful installs
                if install_result.success:
                    self._install_cache.mark_installed(
                        name,
                        install_result.version
                    )
                
                # Call callback if provided
                if callback:
                    callback(name, install_result)
                    
        except Exception as e:
            logger.error(f"Error in install_many: {e}")
            # Mark remaining as failed
            for name in to_install:
                if name not in results:
                    results[name] = InstallResult(
                        package_name=name,
                        success=False,
                        status=InstallStatus.FAILED,
                        error=str(e)
                    )
        
        return results
    
    def install_one(
        self,
        package_name: str,
        module_name: Optional[str] = None
    ) -> InstallResult:
        """
        Install a single package (synchronous interface).
        
        Args:
            package_name: Package name to install
            module_name: Optional module name (for context)
            
        Returns:
            InstallResult with success status
        """
        results = self.install_many(package_name)
        return results.get(package_name, InstallResult(
            package_name=package_name,
            success=False,
            status=InstallStatus.FAILED,
            error="Installation not executed"
        ))
    
    def set_mode(self, mode: LazyInstallMode) -> None:
        """Set installation mode."""
        with self._lock:
            self._mode = mode
    
    def get_mode(self) -> LazyInstallMode:
        """Get current installation mode."""
        return self._mode

__all__ = ['InstallerEngine']

