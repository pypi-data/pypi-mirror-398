"""
Install Policy

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Security and policy configuration for lazy installation.
"""

import threading
from typing import Optional

# Lazy import to avoid circular dependency
def _get_log_event():
    """Get log_event function (lazy import to avoid circular dependency)."""
    from ...common.logger import log_event
    return log_event

_log = None  # Will be initialized on first use

class LazyInstallPolicy:
    """
    Security and policy configuration for lazy installation.
    Per-package allow/deny lists, index URLs, and security settings.
    """
    __slots__ = ()
    
    _allow_lists: dict[str, set[str]] = {}
    _deny_lists: dict[str, set[str]] = {}
    _index_urls: dict[str, str] = {}
    _extra_index_urls: dict[str, list[str]] = {}
    _trusted_hosts: dict[str, list[str]] = {}
    _require_hashes: dict[str, bool] = {}
    _verify_ssl: dict[str, bool] = {}
    _lockfile_paths: dict[str, str] = {}
    _lock = threading.RLock()
    
    @classmethod
    def _ensure_logging(cls):
        """Ensure logging is initialized."""
        global _log
        if _log is None:
            _log = _get_log_event()
    
    @classmethod
    def set_allow_list(cls, package_name: str, allowed_packages: list[str]) -> None:
        """Set allow list for a package (only these can be installed)."""
        cls._ensure_logging()
        with cls._lock:
            cls._allow_lists[package_name] = set(allowed_packages)
            _log("config", f"Set allow list for {package_name}: {len(allowed_packages)} packages")
    
    @classmethod
    def set_deny_list(cls, package_name: str, denied_packages: list[str]) -> None:
        """Set deny list for a package (these cannot be installed)."""
        cls._ensure_logging()
        with cls._lock:
            cls._deny_lists[package_name] = set(denied_packages)
            _log("config", f"Set deny list for {package_name}: {len(denied_packages)} packages")
    
    @classmethod
    def add_to_allow_list(cls, package_name: str, allowed_package: str) -> None:
        """Add single package to allow list."""
        with cls._lock:
            if package_name not in cls._allow_lists:
                cls._allow_lists[package_name] = set()
            cls._allow_lists[package_name].add(allowed_package)
    
    @classmethod
    def add_to_deny_list(cls, package_name: str, denied_package: str) -> None:
        """Add single package to deny list."""
        with cls._lock:
            if package_name not in cls._deny_lists:
                cls._deny_lists[package_name] = set()
            cls._deny_lists[package_name].add(denied_package)
    
    @classmethod
    def is_package_allowed(cls, installer_package: str, target_package: str) -> tuple[bool, str]:
        """Check if target_package can be installed by installer_package."""
        with cls._lock:
            if installer_package in cls._deny_lists:
                if target_package in cls._deny_lists[installer_package]:
                    return False, f"Package '{target_package}' is in deny list"
            
            if installer_package in cls._allow_lists:
                if target_package not in cls._allow_lists[installer_package]:
                    return False, f"Package '{target_package}' not in allow list"
            
            return True, "OK"
    
    @classmethod
    def set_index_url(cls, package_name: str, index_url: str) -> None:
        """Set PyPI index URL for a package."""
        cls._ensure_logging()
        with cls._lock:
            cls._index_urls[package_name] = index_url
            _log("config", f"Set index URL for {package_name}: {index_url}")
    
    @classmethod
    def set_extra_index_urls(cls, package_name: str, urls: list[str]) -> None:
        """Set extra index URLs for a package."""
        cls._ensure_logging()
        with cls._lock:
            cls._extra_index_urls[package_name] = urls
            _log("config", f"Set {len(urls)} extra index URLs for {package_name}")
    
    @classmethod
    def add_trusted_host(cls, package_name: str, host: str) -> None:
        """Add trusted host for a package."""
        with cls._lock:
            if package_name not in cls._trusted_hosts:
                cls._trusted_hosts[package_name] = []
            cls._trusted_hosts[package_name].append(host)
    
    @classmethod
    def get_pip_args(cls, package_name: str) -> list[str]:
        """Get pip install arguments for a package based on policy."""
        args = []
        
        with cls._lock:
            if package_name in cls._index_urls:
                args.extend(['--index-url', cls._index_urls[package_name]])
            
            if package_name in cls._extra_index_urls:
                for url in cls._extra_index_urls[package_name]:
                    args.extend(['--extra-index-url', url])
            
            if package_name in cls._trusted_hosts:
                for host in cls._trusted_hosts[package_name]:
                    args.extend(['--trusted-host', host])
            
            if cls._require_hashes.get(package_name, False):
                args.append('--require-hashes')
            
            if not cls._verify_ssl.get(package_name, True):
                args.append('--no-verify-ssl')
        
        return args
    
    @classmethod
    def set_lockfile_path(cls, package_name: str, path: str) -> None:
        """Set lockfile path for a package."""
        with cls._lock:
            cls._lockfile_paths[package_name] = path
    
    @classmethod
    def get_lockfile_path(cls, package_name: str) -> Optional[str]:
        """Get lockfile path for a package."""
        with cls._lock:
            return cls._lockfile_paths.get(package_name)

__all__ = ['LazyInstallPolicy']

