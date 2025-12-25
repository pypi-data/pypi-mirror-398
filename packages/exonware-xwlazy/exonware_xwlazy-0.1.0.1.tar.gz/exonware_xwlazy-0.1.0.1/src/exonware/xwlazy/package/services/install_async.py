"""
Async Installation Mixin

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Mixin for async installation operations.
"""

import os
import asyncio
import threading
import importlib
from typing import Optional, Any

from .async_install_handle import AsyncInstallHandle
from .manifest import PackageManifest
from .config_manager import LazyInstallConfig
from .install_policy import LazyInstallPolicy
from ...defs import LazyInstallMode

# Lazy imports
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ...common.logger import get_logger
    return get_logger("xwlazy.lazy_installer")

def _get_log_event():
    """Get log_event function (lazy import to avoid circular dependency)."""
    from ...common.logger import log_event
    return log_event

logger = None
_log = None

# Environment variables
_ENV_ASYNC_INSTALL = os.environ.get("XWLAZY_ASYNC_INSTALL", "").strip().lower() in {"1", "true", "yes", "on"}
_ENV_ASYNC_WORKERS = int(os.environ.get("XWLAZY_ASYNC_WORKERS", "0") or 0)

def _ensure_logging_initialized():
    """Ensure logging utilities are initialized."""
    global logger, _log
    if logger is None:
        logger = _get_logger()
        if logger is None:
            import logging
            logger = logging.getLogger("xwlazy.lazy_installer.fallback")
            logger.addHandler(logging.NullHandler())
    if _log is None:
        _log = _get_log_event()
        if _log is None:
            # Simple fallback
            def _fallback_log(event, *args, **kwargs):
                pass
            _log = _fallback_log

class AsyncInstallMixin:
    """Mixin for async installation operations."""
    
    def _ensure_async_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure async event loop is running in background thread."""
        if self._async_loop is not None and self._async_loop.is_running():  # type: ignore[attr-defined]
            return self._async_loop  # type: ignore[attr-defined]
        
        with self._lock:  # type: ignore[attr-defined]
            if self._async_loop is None or not self._async_loop.is_running():  # type: ignore[attr-defined]
                loop_ready = threading.Event()
                loop_ref = [None]
                
                def _run_loop():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop_ref[0] = loop
                    self._async_loop = loop  # type: ignore[attr-defined]
                    loop_ready.set()
                    loop.run_forever()
                
                self._loop_thread = threading.Thread(  # type: ignore[attr-defined]
                    target=_run_loop,
                    daemon=True,
                    name=f"xwlazy-{self._package_name}-async"  # type: ignore[attr-defined]
                )
                self._loop_thread.start()  # type: ignore[attr-defined]
                
                if not loop_ready.wait(timeout=5.0):
                    raise RuntimeError(f"Failed to start async loop for {self._package_name}")  # type: ignore[attr-defined]
        
        return self._async_loop  # type: ignore[attr-defined]
    
    def apply_manifest(self, manifest: Optional[PackageManifest]) -> None:
        """Apply manifest-driven configuration such as async installs."""
        env_override = _ENV_ASYNC_INSTALL
        # Force disable async install unless strictly overridden by env var (safety default)
        if not env_override:
            desired_async = False
        else:
            desired_async = True
        # desired_async = bool(env_override or (manifest and manifest.async_installs))
        desired_workers = _ENV_ASYNC_WORKERS or (manifest.async_workers if manifest else 1)
        desired_workers = max(1, desired_workers)
        
        with self._lock:  # type: ignore[attr-defined]
            self._async_workers = desired_workers  # type: ignore[attr-defined]
            
            if desired_async:
                self._ensure_async_loop()
            else:
                if self._async_loop is not None:  # type: ignore[attr-defined]
                    for task in list(self._async_tasks.values()):  # type: ignore[attr-defined]
                        if not task.done():
                            task.cancel()
                    self._async_tasks.clear()  # type: ignore[attr-defined]
            
            self._async_enabled = desired_async  # type: ignore[attr-defined]
    
    def is_async_enabled(self) -> bool:
        """Return True if async installers are enabled for this package."""
        return self._async_enabled  # type: ignore[attr-defined]
    
    def ensure_async_install(self, module_name: str) -> Optional[AsyncInstallHandle]:
        """Schedule (or reuse) an async install job for module_name if async is enabled."""
        if not self._async_enabled:  # type: ignore[attr-defined]
            return None
        return self.schedule_async_install(module_name)
    
    async def _get_package_size_mb(self, package_name: str) -> Optional[float]:
        """Get package size in MB by checking pip show or download size."""
        from ...common.services.install_async_utils import get_package_size_mb
        return await get_package_size_mb(package_name)
    
    async def _async_install_package(self, package_name: str, module_name: str) -> bool:
        """Async version of install_package using asyncio subprocess."""
        _ensure_logging_initialized()
        # SIZE_AWARE mode: Check package size before installing
        if self._mode == LazyInstallMode.SIZE_AWARE:  # type: ignore[attr-defined]
            mode_config = LazyInstallConfig.get_mode_config(self._package_name)  # type: ignore[attr-defined]
            threshold_mb = mode_config.large_package_threshold_mb if mode_config else 50.0
            
            size_mb = await self._get_package_size_mb(package_name)
            if size_mb is not None and size_mb >= threshold_mb:
                logger.warning(
                    f"Package '{package_name}' is {size_mb:.1f}MB (>= {threshold_mb}MB threshold), "
                    f"skipping installation in SIZE_AWARE mode"
                )
                print(
                    f"[SIZE_AWARE] Skipping large package '{package_name}' "
                    f"({size_mb:.1f}MB >= {threshold_mb}MB)"
                )
                self._failed_packages.add(package_name)  # type: ignore[attr-defined]
                return False
        
        # Check cache first
        if self._install_from_cached_tree(package_name):  # type: ignore[attr-defined]
            self._finalize_install_success(package_name, "cache-tree")  # type: ignore[attr-defined]
            return True
        
        # Use asyncio subprocess for pip install
        try:
            policy_args = LazyInstallPolicy.get_pip_args(self._package_name) or []  # type: ignore[attr-defined]
            from ...common.services.install_async_utils import async_install_package
            success, error_msg = await async_install_package(package_name, policy_args)
            
            if success:
                self._finalize_install_success(package_name, "pip-async")  # type: ignore[attr-defined]
                
                # For CLEAN mode, schedule async uninstall after completion
                if self._mode == LazyInstallMode.CLEAN:  # type: ignore[attr-defined]
                    asyncio.create_task(self._schedule_clean_uninstall(package_name))
                
                # For TEMPORARY mode, uninstall immediately after installation
                if self._mode == LazyInstallMode.TEMPORARY:  # type: ignore[attr-defined]
                    asyncio.create_task(self.uninstall_package_async(package_name, quiet=True))
                
                return True
            else:
                self._failed_packages.add(package_name)  # type: ignore[attr-defined]
                return False
        except Exception as e:
            logger.error(f"Error in async install of {package_name}: {e}")
            self._failed_packages.add(package_name)  # type: ignore[attr-defined]
            return False
    
    async def _schedule_clean_uninstall(self, package_name: str) -> None:
        """Schedule uninstall for CLEAN mode after a delay."""
        await asyncio.sleep(1.0)
        await self.uninstall_package_async(package_name, quiet=True)
    
    async def uninstall_package_async(self, package_name: str, quiet: bool = True) -> bool:
        """Uninstall a package asynchronously in quiet mode."""
        with self._lock:  # type: ignore[attr-defined]
            if package_name not in self._installed_packages:  # type: ignore[attr-defined]
                return True
        
        from ...common.services.install_async_utils import async_uninstall_package
        success = await async_uninstall_package(package_name, quiet)
        
        if success:
            with self._lock:  # type: ignore[attr-defined]
                self._installed_packages.discard(package_name)  # type: ignore[attr-defined]
        
        return success
    
    def schedule_async_install(self, module_name: str) -> Optional[AsyncInstallHandle]:
        """Schedule installation of a dependency in the background using asyncio."""
        _ensure_logging_initialized()
        if not self._async_enabled:  # type: ignore[attr-defined]
            return None
        
        package_name = self._dependency_mapper.get_package_name(module_name) or module_name  # type: ignore[attr-defined]
        if not package_name:
            return None
        
        with self._lock:  # type: ignore[attr-defined]
            task = self._async_tasks.get(module_name)  # type: ignore[attr-defined]
            if task is None or task.done():
                self._mark_module_missing(module_name)  # type: ignore[attr-defined]
                loop = self._ensure_async_loop()
                
                async def _install_and_cleanup():
                    try:
                        result = await self._async_install_package(package_name, module_name)
                        if result:
                            self._clear_module_missing(module_name)  # type: ignore[attr-defined]
                            try:
                                imported_module = importlib.import_module(module_name)
                                if self._mode == LazyInstallMode.TEMPORARY:  # type: ignore[attr-defined]
                                    asyncio.create_task(self.uninstall_package_async(package_name, quiet=True))
                            except Exception:
                                pass
                        return result
                    finally:
                        with self._lock:  # type: ignore[attr-defined]
                            self._async_tasks.pop(module_name, None)  # type: ignore[attr-defined]
                
                task = asyncio.run_coroutine_threadsafe(_install_and_cleanup(), loop)
                self._async_tasks[module_name] = task  # type: ignore[attr-defined]
        
        return AsyncInstallHandle(task, module_name, package_name, self._package_name)  # type: ignore[attr-defined]
    
    async def install_all_dependencies(self) -> None:
        """Install all dependencies from discovered requirements (FULL mode)."""
        _ensure_logging_initialized()
        if self._mode != LazyInstallMode.FULL:  # type: ignore[attr-defined]
            return
        
        try:
            # Lazy import to avoid circular dependency
            from .discovery import get_lazy_discovery
            discovery = get_lazy_discovery()
            if discovery:
                all_deps = discovery.discover_all_dependencies()
                if not all_deps:
                    return
                
                packages_to_install = [
                    (import_name, package_name)
                    for import_name, package_name in all_deps.items()
                    if package_name not in self._installed_packages  # type: ignore[attr-defined]
                ]
                
                if not packages_to_install:
                    _log("install", f"All dependencies already installed for {self._package_name}")  # type: ignore[attr-defined]
                    return
                
                _log(
                    "install",
                    f"Installing {len(packages_to_install)} dependencies for {self._package_name} (FULL mode)"
                )
                
                batch_size = min(self._async_workers * 2, 10)  # type: ignore[attr-defined]
                for i in range(0, len(packages_to_install), batch_size):
                    batch = packages_to_install[i:i + batch_size]
                    tasks = [
                        self._async_install_package(package_name, import_name)
                        for import_name, package_name in batch
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for (import_name, package_name), result in zip(batch, results):
                        if isinstance(result, Exception):
                            logger.error(f"Failed to install {package_name}: {result}")
                        elif result:
                            _log("install", f"✓ Installed {package_name}")
                
                _log("install", f"Completed installing all dependencies for {self._package_name}")  # type: ignore[attr-defined]
        except Exception as e:
            logger.warning(f"Failed to install all dependencies for {self._package_name}: {e}")  # type: ignore[attr-defined]

