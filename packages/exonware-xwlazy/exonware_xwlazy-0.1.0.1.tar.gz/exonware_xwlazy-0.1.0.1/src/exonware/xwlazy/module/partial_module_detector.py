"""
Partial Module Detection Strategies

Detects if a module in sys.modules is partially initialized (still being imported).
This prevents returning partially initialized modules that cause ImportErrors.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 27-Dec-2025
"""

import sys
import threading
from types import ModuleType
from typing import Optional
from enum import Enum

class DetectionStrategy(Enum):
    """Different strategies for detecting partially initialized modules."""
    FRAME_STACK = "frame_stack"  # Check call stack for import functions
    ATTRIBUTE_CHECK = "attribute_check"  # Check if expected attributes exist
    IMPORT_LOCK = "import_lock"  # Use importlib's import lock state
    MODULE_STATE = "module_state"  # Check module's __spec__ and loader state
    HYBRID = "hybrid"  # Combine multiple strategies

# Track modules currently being imported (thread-safe)
_importing_modules: set[str] = set()
_import_lock = threading.RLock()

def mark_module_importing(module_name: str) -> None:
    """Mark a module as currently being imported."""
    with _import_lock:
        _importing_modules.add(module_name)

def unmark_module_importing(module_name: str) -> None:
    """Unmark a module as no longer being imported."""
    with _import_lock:
        _importing_modules.discard(module_name)

def is_module_importing(module_name: str) -> bool:
    """Check if a module is currently being imported."""
    with _import_lock:
        return module_name in _importing_modules

class PartialModuleDetector:
    """
    Modular detector for partially initialized modules.
    
    Uses different strategies to detect if a module in sys.modules
    is still being initialized and shouldn't be returned yet.
    """
    
    def __init__(self, strategy: DetectionStrategy = DetectionStrategy.HYBRID):
        self.strategy = strategy
    
    def is_partially_initialized(self, module_name: str, module: ModuleType) -> bool:
        """
        Check if module is partially initialized (still being imported).
        
        Args:
            module_name: Name of the module
            module: Module object from sys.modules
            
        Returns:
            True if module is partially initialized, False if fully loaded
        """
        if self.strategy == DetectionStrategy.FRAME_STACK:
            return self._check_frame_stack(module_name)
        elif self.strategy == DetectionStrategy.ATTRIBUTE_CHECK:
            return self._check_attributes(module_name, module)
        elif self.strategy == DetectionStrategy.IMPORT_LOCK:
            return self._check_import_lock(module_name)
        elif self.strategy == DetectionStrategy.MODULE_STATE:
            return self._check_module_state(module_name, module)
        elif self.strategy == DetectionStrategy.HYBRID:
            return self._check_hybrid(module_name, module)
        else:
            return False
    
    def _check_frame_stack(self, module_name: str) -> bool:
        """
        Strategy 1: Check call stack for import-related functions.
        
        If we're in _find_and_load, _load_unlocked, or exec_module,
        the module is likely still being imported.
        
        CRITICAL: This checks if the CURRENT import call is for this module,
        not just if we're in an import function.
        """
        try:
            # Start from frame 2 (skip our own function and the caller)
            frame = sys._getframe(2)
            depth = 0
            max_depth = 30  # Increased depth to catch deeper import chains
            
            while frame and depth < max_depth:
                code = frame.f_code
                func_name = code.co_name
                
                # Check for import-related functions in Python's importlib
                import_keywords = [
                    '_find_and_load', '_load_unlocked', 'exec_module',
                    '_call_with_frames_removed', '_load_module_spec',
                    '_intercepting_import', '__import__'
                ]
                
                if any(keyword in func_name for keyword in import_keywords):
                    # Check if this module is in the frame's locals or globals
                    if hasattr(frame, 'f_locals'):
                        locals_dict = frame.f_locals
                        # Check various ways module name might appear
                        frame_module_name = (
                            locals_dict.get('name') or
                            locals_dict.get('fullname') or
                            locals_dict.get('__name__') or
                            (locals_dict.get('module') and getattr(locals_dict.get('module'), '__name__', None))
                        )
                        
                        if frame_module_name == module_name:
                            return True
                    
                    # Also check globals
                    if hasattr(frame, 'f_globals'):
                        globals_dict = frame.f_globals
                        if '__name__' in globals_dict and globals_dict.get('__name__') == module_name:
                            return True
                
                frame = frame.f_back
                depth += 1
        except (AttributeError, ValueError):
            # Frame inspection failed, assume not importing
            pass
        
        return False
    
    def _check_attributes(self, module_name: str, module: ModuleType) -> bool:
        """
        Strategy 2: Check if module has expected attributes.
        
        A fully initialized module should have certain attributes.
        If key attributes are missing, it might be partially initialized.
        
        CRITICAL: We need to be careful - some modules legitimately don't have
        __file__ (namespace packages, built-ins). We only flag as partial if
        we're CERTAIN it's not fully initialized.
        """
        module_dict = getattr(module, '__dict__', {})
        
        # Check for placeholder patterns (lazy loaders often add __getattr__)
        if hasattr(module, '__getattr__'):
            # If it has __getattr__ but very few attributes, it's likely a placeholder
            if len(module_dict) <= 5:  # Only __name__, __loader__, __spec__, __getattr__, etc.
                if not hasattr(module, '__file__') and not hasattr(module, '__path__'):
                    # Not a namespace package and no file - likely placeholder
                    return True
        
        # Check if module has __spec__ but loader hasn't executed yet
        if hasattr(module, '__spec__') and module.__spec__ is not None:
            spec = module.__spec__
            # If loader exists but module dict is very small, it might not be fully loaded
            if hasattr(spec, 'loader') and spec.loader is not None:
                # Check if module dict is suspiciously small (only metadata, no actual content)
                if len(module_dict) <= 3:
                    # Only has __name__, __loader__, __spec__ - likely not executed
                    if not hasattr(module, '__file__') and not hasattr(module, '__path__'):
                        # Not a namespace package - likely partial
                        return True
        
        # If module is in sys.modules but has no meaningful content, it's likely partial
        # This is a heuristic - be conservative
        if module_name in sys.modules:
            # Check if module has been executed by looking for non-metadata attributes
            metadata_attrs = {'__name__', '__loader__', '__spec__', '__package__', '__file__', '__path__', '__cached__'}
            content_attrs = set(module_dict.keys()) - metadata_attrs
            if len(content_attrs) == 0 and len(module_dict) > 0:
                # Has metadata but no content - might be partial
                # But be conservative - only flag if we're sure
                if hasattr(module, '__loader__') and module.__loader__ is not None:
                    # Has loader but no content - likely partial
                    return True
        
        return False
    
    def _check_import_lock(self, module_name: str) -> bool:
        """
        Strategy 3: Use our own import tracking.
        
        Check if module is marked as currently being imported.
        """
        return is_module_importing(module_name)
    
    def _check_module_state(self, module_name: str, module: ModuleType) -> bool:
        """
        Strategy 4: Check module's internal state.
        
        Look at __spec__, __loader__, and other state indicators.
        """
        # If module doesn't have __spec__, it's likely not fully initialized
        if not hasattr(module, '__spec__') or module.__spec__ is None:
            # Exception: Some built-in modules don't have __spec__
            if module_name not in sys.builtin_module_names:
                return True
        
        # Check if module has __loader__ but loader hasn't executed
        if hasattr(module, '__loader__') and module.__loader__ is not None:
            loader = module.__loader__
            # If loader has exec_module but module doesn't have expected attributes,
            # it might not be fully executed
            if hasattr(loader, 'exec_module'):
                # Check if module has been executed by looking for common attributes
                # This is heuristic - modules should have some content after execution
                module_dict = getattr(module, '__dict__', {})
                # If dict is mostly empty (only has __name__, __loader__, __spec__),
                # it might not be fully initialized
                if len(module_dict) <= 3:
                    # Check if it's a legitimate empty module
                    if '__file__' not in module_dict and '__path__' not in module_dict:
                        return True
        
        return False
    
    def _check_hybrid(self, module_name: str, module: ModuleType) -> bool:
        """
        Strategy 5: Hybrid - combine multiple strategies.
        
        Returns True if ANY strategy indicates partial initialization.
        This is the most conservative approach.
        
        NOTE: We check frame stack FIRST because it's most accurate for detecting
        modules currently being imported. Import lock is secondary.
        """
        # Check frame stack first (most accurate for detecting active imports)
        if self._check_frame_stack(module_name):
            return True
        
        # Check attributes (fast, reliable)
        if self._check_attributes(module_name, module):
            return True
        
        # Check module state (medium speed)
        if self._check_module_state(module_name, module):
            return True
        
        # Check import lock last (may have false positives)
        # Only use if other checks are inconclusive
        if is_module_importing(module_name):
            # Double-check with frame stack to avoid false positives
            if self._check_frame_stack(module_name):
                return True
        
        return False

# Global detector instance (defaults to HYBRID strategy)
_default_detector = PartialModuleDetector(DetectionStrategy.HYBRID)

def is_partially_initialized(module_name: str, module: ModuleType, 
                            strategy: Optional[DetectionStrategy] = None) -> bool:
    """
    Convenience function to check if module is partially initialized.
    
    Args:
        module_name: Name of the module
        module: Module object from sys.modules
        strategy: Optional strategy override
        
    Returns:
        True if module is partially initialized
    """
    if strategy:
        detector = PartialModuleDetector(strategy)
        return detector.is_partially_initialized(module_name, module)
    return _default_detector.is_partially_initialized(module_name, module)

