"""
Installation Cache Utilities

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Shared utilities for cache management (wheels, install trees).
Used by both execution strategies and LazyInstaller.
"""

import os
import sys
import shutil
import sysconfig
import tempfile
import subprocess
import zipfile
from pathlib import Path
from typing import Optional
from contextlib import suppress

# Lazy imports
def _get_logger():
    """Get logger (lazy import to avoid circular dependency)."""
    from ..logger import get_logger
    return get_logger("xwlazy.install_cache_utils")

logger = None

# Environment variables
_DEFAULT_ASYNC_CACHE_DIR = Path(
    os.environ.get(
        "XWLAZY_ASYNC_CACHE_DIR",
        os.path.join(os.path.expanduser("~"), ".xwlazy", "wheel-cache"),
    )
)

def _ensure_logging_initialized():
    """Ensure logging utilities are initialized."""
    global logger
    if logger is None:
        logger = _get_logger()

def get_default_cache_dir() -> Path:
    """Get the default cache directory."""
    return _DEFAULT_ASYNC_CACHE_DIR

def get_cache_dir(cache_dir: Optional[Path] = None) -> Path:
    """Get cache directory, creating it if necessary."""
    if cache_dir is None:
        cache_dir = _DEFAULT_ASYNC_CACHE_DIR
    path = Path(cache_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_wheel_path(package_name: str, cache_dir: Optional[Path] = None) -> Path:
    """Get the cached wheel file path for a package."""
    cache = get_cache_dir(cache_dir)
    safe = package_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    return cache / f"{safe}.whl"

def get_install_tree_dir(package_name: str, cache_dir: Optional[Path] = None) -> Path:
    """Get the cached install directory for a package."""
    cache = get_cache_dir(cache_dir)
    safe = package_name.replace("/", "_").replace("\\", "_").replace(":", "_")
    return cache / "installs" / safe

def get_site_packages_dir() -> Path:
    """Get the site-packages directory."""
    purelib = sysconfig.get_paths().get("purelib")
    if not purelib:
        purelib = sysconfig.get_paths().get("platlib", sys.prefix)
    path = Path(purelib)
    path.mkdir(parents=True, exist_ok=True)
    return path

def pip_install_from_path(wheel_path: Path, policy_args: Optional[list[str]] = None) -> bool:
    """Install a wheel file using pip."""
    try:
        pip_args = [
            sys.executable,
            '-m',
            'pip',
            'install',
            '--no-deps',
            '--no-input',
            '--disable-pip-version-check',
        ]
        if policy_args:
            pip_args.extend(policy_args)
        pip_args.append(str(wheel_path))
        result = subprocess.run(
            pip_args,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def ensure_cached_wheel(
    package_name: str,
    policy_args: Optional[list[str]] = None,
    cache_dir: Optional[Path] = None
) -> Optional[Path]:
    """Ensure a wheel is cached, downloading it if necessary."""
    wheel_path = get_wheel_path(package_name, cache_dir)
    if wheel_path.exists():
        return wheel_path
    
    cache = get_cache_dir(cache_dir)
    try:
        pip_args = [
            sys.executable,
            '-m',
            'pip',
            'wheel',
            '--no-deps',
            '--disable-pip-version-check',
        ]
        if policy_args:
            pip_args.extend(policy_args)
        pip_args.extend(['--wheel-dir', str(cache), package_name])
        result = subprocess.run(
            pip_args,
            capture_output=True,
            text=True,
            check=True,
        )
        if result.returncode != 0:
            return None
        candidates = sorted(cache.glob("*.whl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            return None
        primary = candidates[0]
        if wheel_path.exists():
            with suppress(Exception):
                wheel_path.unlink()
        primary.rename(wheel_path)
        for leftover in candidates[1:]:
            with suppress(Exception):
                leftover.unlink()
        return wheel_path
    except subprocess.CalledProcessError:
        return None

def install_from_cached_tree(
    package_name: str,
    cache_dir: Optional[Path] = None
) -> bool:
    """Install from a cached install tree."""
    _ensure_logging_initialized()
    src = get_install_tree_dir(package_name, cache_dir)
    if not src.exists() or not any(src.iterdir()):
        return False
    target_root = get_site_packages_dir()
    try:
        for item in src.iterdir():
            dest = target_root / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest, ignore_errors=True)
                else:
                    with suppress(FileNotFoundError):
                        dest.unlink()
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
        return True
    except Exception as exc:
        logger.debug("Cached tree install failed for %s: %s", package_name, exc)
        return False

def materialize_cached_tree(
    package_name: str,
    wheel_path: Path,
    cache_dir: Optional[Path] = None
) -> None:
    """Materialize a cached install tree from a wheel file."""
    _ensure_logging_initialized()
    if not wheel_path or not wheel_path.exists():
        return
    target_dir = get_install_tree_dir(package_name, cache_dir)
    if target_dir.exists() and any(target_dir.iterdir()):
        return
    parent = target_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(
        tempfile.mkdtemp(prefix="xwlazy-cache-", dir=str(parent))
    )
    try:
        with zipfile.ZipFile(wheel_path, "r") as archive:
            archive.extractall(temp_dir)
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.move(str(temp_dir), str(target_dir))
    except Exception as exc:
        logger.debug("Failed to materialize cached tree for %s: %s", package_name, exc)
        with suppress(Exception):
            shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        return
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

def has_cached_install_tree(
    package_name: str,
    cache_dir: Optional[Path] = None
) -> bool:
    """Check if a cached install tree exists."""
    target = get_install_tree_dir(package_name, cache_dir)
    return target.exists() and any(target.iterdir())

def install_from_cached_wheel(
    package_name: str,
    policy_args: Optional[list[str]] = None,
    cache_dir: Optional[Path] = None
) -> bool:
    """Install from a cached wheel file."""
    wheel_path = get_wheel_path(package_name, cache_dir)
    if not wheel_path.exists():
        return False
    return pip_install_from_path(wheel_path, policy_args)

__all__ = [
    'get_default_cache_dir',
    'get_cache_dir',
    'get_wheel_path',
    'get_install_tree_dir',
    'get_site_packages_dir',
    'pip_install_from_path',
    'ensure_cached_wheel',
    'install_from_cached_tree',
    'materialize_cached_tree',
    'has_cached_install_tree',
    'install_from_cached_wheel',
]

