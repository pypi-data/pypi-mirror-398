"""
Keyword-based detection for lazy installation.

This module provides functionality to detect packages that opt-in to lazy loading
by including specific keywords in their metadata.
"""

import os
import sys
import threading
from typing import Optional

from ..logger import get_logger

logger = get_logger("xwlazy.discovery.keyword")

# Global configuration
_KEYWORD_DETECTION_ENABLED: bool = True
_KEYWORD_TO_CHECK: str = "xwlazy-enabled"
_keyword_config_lock = threading.RLock()

# Detection cache
_lazy_detection_cache: dict[str, bool] = {}
_lazy_detection_lock = threading.RLock()

def _check_package_keywords(package_name: Optional[str] = None, keyword: Optional[str] = None) -> bool:
    """
    Check if any installed package has the specified keyword in its metadata.
    
    This allows packages to opt-in to lazy loading by adding:
    [project]
    keywords = ["xwlazy-enabled"]
    
    in their pyproject.toml file. The keyword is stored in the package's
    metadata when installed.
    
    Args:
        package_name: The package name to check (or None to check all packages)
        keyword: The keyword to look for (default: uses _KEYWORD_TO_CHECK)
    
    Returns:
        True if the keyword is found in any relevant package's metadata
    """
    if not _KEYWORD_DETECTION_ENABLED:
        return False
    
    if sys.version_info < (3, 8):
        return False
    
    try:
        from importlib import metadata
    except Exception as exc:
        logger.debug(f"importlib.metadata unavailable for keyword detection: {exc}")
        return False
    
    with _keyword_config_lock:
        search_keyword = (keyword or _KEYWORD_TO_CHECK).lower()
    
    try:
        if package_name:
            # Check specific package
            try:
                dist = metadata.distribution(package_name)
                keywords = dist.metadata.get_all('Keywords', [])
                if keywords:
                    # Keywords can be a single string or list
                    all_keywords = []
                    for kw in keywords:
                        if isinstance(kw, str):
                            # Split comma-separated keywords
                            all_keywords.extend(k.strip().lower() for k in kw.split(','))
                        else:
                            all_keywords.append(str(kw).lower())
                    
                    if search_keyword in all_keywords:
                        logger.info(f"✅ Detected '{search_keyword}' keyword in package: {package_name}")
                        return True
            except metadata.PackageNotFoundError:
                return False
        else:
            # Check all installed packages
            for dist in metadata.distributions():
                try:
                    keywords = dist.metadata.get_all('Keywords', [])
                    if keywords:
                        all_keywords = []
                        for kw in keywords:
                            if isinstance(kw, str):
                                all_keywords.extend(k.strip().lower() for k in kw.split(','))
                            else:
                                all_keywords.append(str(kw).lower())
                        
                        if search_keyword in all_keywords:
                            package_found = dist.metadata.get('Name', 'unknown')
                            logger.info(f"✅ Detected '{search_keyword}' keyword in package: {package_found}")
                            return True
                except Exception:
                    continue
    except Exception as exc:
        logger.debug(f"Failed to check package keywords: {exc}")
    
    return False

def _lazy_marker_installed() -> bool:
    """Check if the exonware-xwlazy marker package is installed."""
    if sys.version_info < (3, 8):
        return False

    try:
        from importlib import metadata
    except Exception as exc:
        logger.debug(f"importlib.metadata unavailable for lazy detection: {exc}")
        return False

    try:
        metadata.distribution("exonware-xwlazy")
        logger.info("✅ Detected exonware-xwlazy marker package")
        return True
    except metadata.PackageNotFoundError:
        logger.debug("❌ exonware-xwlazy marker package not installed")
        return False

def _lazy_env_override(package_name: str) -> Optional[bool]:
    """Check environment variable override for lazy installation."""
    env_var = f"{package_name.upper()}_LAZY_INSTALL"
    raw_value = os.environ.get(env_var)
    if raw_value is None:
        return None

    normalized = raw_value.strip().lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False
    return None

def _detect_meta_info_mode(package_name: str) -> Optional[str]:
    """
    Detect lazy mode from package metadata keywords.
    
    Checks for keywords like:
    - xwlazy-load-install-uninstall (clean mode)
    - xwlazy-lite (lite mode)
    - xwlazy-smart (smart mode)
    - xwlazy-full (full mode)
    - xwlazy-auto (auto mode)
    
    Returns:
        Mode string or None if not found
    """
    try:
        import importlib.metadata
        try:
            dist = importlib.metadata.distribution(package_name)
            keywords = dist.metadata.get_all("Keywords", [])
            if not keywords:
                return None
            
            keyword_str = " ".join(keywords).lower()
            
            if "xwlazy-load-install-uninstall" in keyword_str:
                return "clean"
            if "xwlazy-lite" in keyword_str:
                return "lite"
            if "xwlazy-smart" in keyword_str:
                return "smart"
            if "xwlazy-full" in keyword_str:
                return "full"
            if "xwlazy-auto" in keyword_str:
                return "auto"
        except importlib.metadata.PackageNotFoundError:
            return None
    except Exception:
        pass
    return None

def enable_keyword_detection(enabled: bool = True, keyword: Optional[str] = None) -> None:
    """
    Enable/disable keyword-based auto-detection of lazy loading.
    
    When enabled, xwlazy will check installed packages for a keyword
    (default: "xwlazy-enabled") in their metadata. Packages can opt-in
    by adding the keyword to their pyproject.toml:
    
    [project]
    keywords = ["xwlazy-enabled"]
    
    Args:
        enabled: Whether to enable keyword detection (default: True)
        keyword: Custom keyword to check (default: "xwlazy-enabled")
    """
    global _KEYWORD_DETECTION_ENABLED, _KEYWORD_TO_CHECK
    with _keyword_config_lock:
        _KEYWORD_DETECTION_ENABLED = enabled
        if keyword is not None:
            _KEYWORD_TO_CHECK = keyword
        # Clear cache to force re-detection
        with _lazy_detection_lock:
            _lazy_detection_cache.clear()

def is_keyword_detection_enabled() -> bool:
    """Return whether keyword-based detection is enabled."""
    with _keyword_config_lock:
        return _KEYWORD_DETECTION_ENABLED

def get_keyword_detection_keyword() -> str:
    """Get the keyword currently being checked for auto-detection."""
    with _keyword_config_lock:
        return _KEYWORD_TO_CHECK

def check_package_keywords(package_name: Optional[str] = None, keyword: Optional[str] = None) -> bool:
    """
    Check if a package (or any package) has the specified keyword in its metadata.
    
    This is the public API for the keyword detection functionality.
    
    Args:
        package_name: The package name to check (or None to check all packages)
        keyword: The keyword to look for (default: uses configured keyword)
    
    Returns:
        True if the keyword is found in the package's metadata
    """
    return _check_package_keywords(package_name, keyword)

def _detect_lazy_installation(package_name: str) -> bool:
    """
    Detect if lazy installation should be enabled for a package.
    
    This function checks multiple sources in order:
    1. Environment variable override
    2. Manual state (from state manager)
    3. Cached auto state
    4. Marker package detection
    5. Keyword detection
    
    Args:
        package_name: The package name to check
    
    Returns:
        True if lazy installation should be enabled
    """
    with _lazy_detection_lock:
        cached = _lazy_detection_cache.get(package_name)
        if cached is not None:
            return cached

    env_override = _lazy_env_override(package_name)
    if env_override is not None:
        with _lazy_detection_lock:
            _lazy_detection_cache[package_name] = env_override
        return env_override

    from .state_manager import LazyStateManager
    state_manager = LazyStateManager(package_name)
    manual_state = state_manager.get_manual_state()
    if manual_state is not None:
        with _lazy_detection_lock:
            _lazy_detection_cache[package_name] = manual_state
        return manual_state

    cached_state = state_manager.get_cached_auto_state()
    if cached_state is not None:
        with _lazy_detection_lock:
            _lazy_detection_cache[package_name] = cached_state
        return cached_state

    # Check marker package first (existing behavior)
    marker_detected = _lazy_marker_installed()
    
    # Also check for keyword in package metadata (new feature)
    keyword_detected = _check_package_keywords(package_name)
    
    # Enable if either marker package OR keyword is found
    detected = marker_detected or keyword_detected
    
    state_manager.set_auto_state(detected)

    with _lazy_detection_lock:
        _lazy_detection_cache[package_name] = detected

    return detected

