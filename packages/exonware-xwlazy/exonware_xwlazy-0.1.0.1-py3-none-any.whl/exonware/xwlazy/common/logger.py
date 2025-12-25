"""
#exonware/xwlazy/src/exonware/xwlazy/common/logger.py

Logging utilities for xwlazy - shared across package, module, and runtime.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

This module provides unified logging functionality for all xwlazy components.
All logging code is centralized here to avoid duplication.
"""

import os
import sys
import logging
import io
from typing import Optional
from datetime import datetime

# =============================================================================
# CONSTANTS
# =============================================================================

# Emoji mapping for log flags (shared across formatter and format_message)
_EMOJI_MAP = {
    "WARN": "⚠️",
    "INFO": "ℹ️",
    "ACTION": "⚙️",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "FAIL": "⛔",
    "DEBUG": "🔍",
    "CRITICAL": "🚨",
}

# Default log category states
_CATEGORY_DEFAULTS: dict[str, bool] = {
    "install": True,
    "hook": False,
    "enhance": False,
    "audit": False,
    "sbom": False,
    "config": False,
    "discovery": False,
}

# =============================================================================
# MODULE STATE
# =============================================================================

_configured = False
_category_overrides: dict[str, bool] = {}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _normalize_category(name: str) -> str:
    """Normalize category name to lowercase."""
    return name.strip().lower()

def _load_env_overrides() -> None:
    """Load log category overrides from environment variables."""
    for category in _CATEGORY_DEFAULTS:
        env_key = f"XWLAZY_LOG_{category.upper()}"
        env_val = os.getenv(env_key)
        if env_val is None:
            continue
        enabled = env_val.strip().lower() not in {"0", "false", "off", "no"}
        _category_overrides[_normalize_category(category)] = enabled

# =============================================================================
# FORMATTER
# =============================================================================

class XWLazyFormatter(logging.Formatter):
    """Custom formatter for xwlazy that uses exonware.xwlazy [HH:MM:SS]: [FLAG] format."""
    
    LEVEL_FLAGS = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with emoji and timestamp."""
        flag = self.LEVEL_FLAGS.get(record.levelno, "INFO")
        emoji = _EMOJI_MAP.get(flag, "ℹ️")
        time_str = datetime.now().strftime("%H:%M:%S")
        message = record.getMessage()
        return f"{emoji} exonware.xwlazy [{time_str}]: [{flag}] {message}"

# =============================================================================
# CONFIGURATION
# =============================================================================

def _ensure_basic_config() -> None:
    """Ensure logging is configured (called once)."""
    global _configured
    if _configured:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler with custom formatter and UTF-8 encoding for Windows
    # Wrap stdout with UTF-8 encoding to handle emoji characters on Windows
    if sys.platform == "win32":
        # On Windows, wrap stdout with UTF-8 encoding
        try:
            # Try to set UTF-8 encoding for stdout
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            # Create a wrapper stream that handles encoding
            utf8_stream = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
            console_handler = logging.StreamHandler(utf8_stream)
        except (AttributeError, OSError):
            # Fallback to regular stdout if reconfiguration fails
            console_handler = logging.StreamHandler(sys.stdout)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(XWLazyFormatter())
    root_logger.addHandler(console_handler)
    
    # Load environment overrides
    _load_env_overrides()
    
    _configured = True

# =============================================================================
# PUBLIC API
# =============================================================================

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger configured for the lazy subsystem.
    
    Args:
        name: Optional logger name (defaults to "xwlazy.lazy")
        
    Returns:
        Configured logger instance
    """
    _ensure_basic_config()
    return logging.getLogger(name or "xwlazy.lazy")

def is_log_category_enabled(category: str) -> bool:
    """
    Return True if the provided log category is enabled.
    
    Args:
        category: Log category name (e.g., "install", "hook")
        
    Returns:
        True if category is enabled, False otherwise
    """
    _ensure_basic_config()
    normalized = _normalize_category(category)
    if normalized in _category_overrides:
        return _category_overrides[normalized]
    return _CATEGORY_DEFAULTS.get(normalized, True)

def set_log_category(category: str, enabled: bool) -> None:
    """
    Enable/disable an individual log category at runtime.
    
    Args:
        category: Log category name
        enabled: True to enable, False to disable
    """
    _category_overrides[_normalize_category(category)] = bool(enabled)

def set_log_categories(overrides: dict[str, bool]) -> None:
    """
    Bulk update multiple log categories.
    
    Args:
        overrides: Dictionary mapping category names to enabled state
    """
    for category, enabled in overrides.items():
        set_log_category(category, enabled)

def get_log_categories() -> dict[str, bool]:
    """
    Return the effective state for each built-in log category.
    
    Returns:
        Dictionary mapping category names to enabled state
    """
    _ensure_basic_config()
    result = {}
    for category, default_enabled in _CATEGORY_DEFAULTS.items():
        normalized = _normalize_category(category)
        result[category] = _category_overrides.get(normalized, default_enabled)
    return result

def log_event(category: str, level_fn, msg: str, *args, **kwargs) -> None:
    """
    Emit a log for the given category if it is enabled.
    
    Args:
        category: Log category name
        level_fn: Logging function (e.g., logger.info, logger.warning)
        msg: Log message format string
        *args: Positional arguments for message formatting
        **kwargs: Keyword arguments for message formatting
    """
    if is_log_category_enabled(category):
        level_fn(msg, *args, **kwargs)

def format_message(flag: str, message: str) -> str:
    """
    Format a message with exonware.xwlazy [HH:MM:SS]: [FLAG] format.
    
    Args:
        flag: Log flag (e.g., "INFO", "WARN", "ERROR")
        message: Message text
        
    Returns:
        Formatted message string
    """
    emoji = _EMOJI_MAP.get(flag, "ℹ️")
    time_str = datetime.now().strftime("%H:%M:%S")
    return f"{emoji} exonware.xwlazy [{time_str}]: [{flag}] {message}"

def print_formatted(flag: str, message: str, same_line: bool = False) -> None:
    """
    Print a formatted message with optional same-line support.
    
    Args:
        flag: Log flag (e.g., "INFO", "WARN", "ERROR")
        message: Message text
        same_line: If True, use carriage return for same-line output
    """
    formatted = format_message(flag, message)
    if same_line:
        sys.stdout.write(f"\r{formatted}")
        sys.stdout.flush()
    else:
        print(formatted)

