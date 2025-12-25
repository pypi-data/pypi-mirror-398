"""
Async Install Handle

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Lightweight handle for background installation jobs.
"""

import asyncio
from typing import Optional, Any

class AsyncInstallHandle:
    """Lightweight handle for background installation jobs."""
    
    __slots__ = ("_task_or_future", "module_name", "package_name", "installer_package")
    
    def __init__(
        self,
        task_or_future: Any,  # Can be Future or asyncio.Task
        module_name: str,
        package_name: str,
        installer_package: str,
    ) -> None:
        self._task_or_future = task_or_future
        self.module_name = module_name
        self.package_name = package_name
        self.installer_package = installer_package
    
    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for installation to complete.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            True if installation succeeded, False otherwise
        """
        try:
            # Handle concurrent.futures.Future (from asyncio.run_coroutine_threadsafe)
            if hasattr(self._task_or_future, 'result'):
                result = self._task_or_future.result(timeout=timeout)
                return bool(result)
            # Handle asyncio.Task
            elif hasattr(self._task_or_future, 'done'):
                if timeout is None:
                    # Use asyncio.wait_for if we have a loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Can't wait in running loop, return False
                            return False
                    except RuntimeError:
                        pass
                    # Create new event loop to wait
                    return asyncio.run(self._wait_task())
                else:
                    return asyncio.run(asyncio.wait_for(self._wait_task(), timeout=timeout))
            return False
        except Exception:
            return False
    
    async def _wait_task(self) -> bool:
        """Async helper to wait for task."""
        if hasattr(self._task_or_future, 'done'):
            await self._task_or_future
            return bool(self._task_or_future.result() if hasattr(self._task_or_future, 'result') else True)
        return False
    
    @property
    def done(self) -> bool:
        """
        Check if installation is complete.
        
        Returns:
            True if installation is complete
        """
        if hasattr(self._task_or_future, 'done'):
            return self._task_or_future.done()
        return False

__all__ = ['AsyncInstallHandle']

