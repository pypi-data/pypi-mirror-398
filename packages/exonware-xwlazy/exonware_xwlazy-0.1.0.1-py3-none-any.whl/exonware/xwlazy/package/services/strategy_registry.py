"""
Strategy Registry

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Registry to store custom strategies per package for both package and module operations.
"""

import threading
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ...contracts import (
        IInstallExecutionStrategy,
        IInstallTimingStrategy,
        IDiscoveryStrategy,
        IPolicyStrategy,
        IMappingStrategy,
        IModuleHelperStrategy,
        IModuleManagerStrategy,
        ICachingStrategy,
        IInstallStrategy,
        ILoadStrategy,
        ICacheStrategy,
    )

class StrategyRegistry:
    """
    Registry to store custom strategies per package and enable runtime strategy swapping.
    
    Supports both:
    - Per-package strategies (different strategies for different packages)
    - Global strategy swapping (change default strategies used by all packages)
    """
    
    # Package strategies (per-package)
    _package_execution_strategies: dict[str, 'IInstallExecutionStrategy'] = {}
    _package_timing_strategies: dict[str, 'IInstallTimingStrategy'] = {}
    _package_discovery_strategies: dict[str, 'IDiscoveryStrategy'] = {}
    _package_policy_strategies: dict[str, 'IPolicyStrategy'] = {}
    _package_mapping_strategies: dict[str, 'IMappingStrategy'] = {}
    
    # Module strategies (per-package)
    _module_helper_strategies: dict[str, 'IModuleHelperStrategy'] = {}
    _module_manager_strategies: dict[str, 'IModuleManagerStrategy'] = {}
    _module_caching_strategies: dict[str, 'ICachingStrategy'] = {}
    
    # Global strategies (for runtime swapping)
    _global_install_strategies: dict[str, 'IInstallStrategy'] = {}
    _global_load_strategies: dict[str, 'ILoadStrategy'] = {}
    _global_cache_strategies: dict[str, 'ICacheStrategy'] = {}
    _default_install_strategy: Optional[str] = None
    _default_load_strategy: Optional[str] = None
    _default_cache_strategy: Optional[str] = None
    
    _lock = threading.RLock()
    
    @classmethod
    def set_package_strategy(
        cls,
        package_name: str,
        strategy_type: str,
        strategy: Any,
    ) -> None:
        """
        Set a package strategy for a package.
        
        Args:
            package_name: Package name
            strategy_type: One of 'execution', 'timing', 'discovery', 'policy', 'mapping'
            strategy: Strategy instance
        """
        package_key = package_name.lower()
        with cls._lock:
            if strategy_type == 'execution':
                cls._package_execution_strategies[package_key] = strategy
            elif strategy_type == 'timing':
                cls._package_timing_strategies[package_key] = strategy
            elif strategy_type == 'discovery':
                cls._package_discovery_strategies[package_key] = strategy
            elif strategy_type == 'policy':
                cls._package_policy_strategies[package_key] = strategy
            elif strategy_type == 'mapping':
                cls._package_mapping_strategies[package_key] = strategy
            else:
                raise ValueError(f"Unknown package strategy type: {strategy_type}")
    
    @classmethod
    def get_package_strategy(
        cls,
        package_name: str,
        strategy_type: str,
    ) -> Optional[Any]:
        """
        Get a package strategy for a package.
        
        Args:
            package_name: Package name
            strategy_type: One of 'execution', 'timing', 'discovery', 'policy', 'mapping'
            
        Returns:
            Strategy instance or None if not set
        """
        package_key = package_name.lower()
        with cls._lock:
            if strategy_type == 'execution':
                return cls._package_execution_strategies.get(package_key)
            elif strategy_type == 'timing':
                return cls._package_timing_strategies.get(package_key)
            elif strategy_type == 'discovery':
                return cls._package_discovery_strategies.get(package_key)
            elif strategy_type == 'policy':
                return cls._package_policy_strategies.get(package_key)
            elif strategy_type == 'mapping':
                return cls._package_mapping_strategies.get(package_key)
            else:
                raise ValueError(f"Unknown package strategy type: {strategy_type}")
    
    @classmethod
    def set_module_strategy(
        cls,
        package_name: str,
        strategy_type: str,
        strategy: Any,
    ) -> None:
        """
        Set a module strategy for a package.
        
        Args:
            package_name: Package name
            strategy_type: One of 'helper', 'manager', 'caching'
            strategy: Strategy instance
        """
        package_key = package_name.lower()
        with cls._lock:
            if strategy_type == 'helper':
                cls._module_helper_strategies[package_key] = strategy
            elif strategy_type == 'manager':
                cls._module_manager_strategies[package_key] = strategy
            elif strategy_type == 'caching':
                cls._module_caching_strategies[package_key] = strategy
            else:
                raise ValueError(f"Unknown module strategy type: {strategy_type}")
    
    @classmethod
    def get_module_strategy(
        cls,
        package_name: str,
        strategy_type: str,
    ) -> Optional[Any]:
        """
        Get a module strategy for a package.
        
        Args:
            package_name: Package name
            strategy_type: One of 'helper', 'manager', 'caching'
            
        Returns:
            Strategy instance or None if not set
        """
        package_key = package_name.lower()
        with cls._lock:
            if strategy_type == 'helper':
                return cls._module_helper_strategies.get(package_key)
            elif strategy_type == 'manager':
                return cls._module_manager_strategies.get(package_key)
            elif strategy_type == 'caching':
                return cls._module_caching_strategies.get(package_key)
            else:
                raise ValueError(f"Unknown module strategy type: {strategy_type}")
    
    @classmethod
    def clear_package_strategies(cls, package_name: str) -> None:
        """Clear all package strategies for a package."""
        package_key = package_name.lower()
        with cls._lock:
            cls._package_execution_strategies.pop(package_key, None)
            cls._package_timing_strategies.pop(package_key, None)
            cls._package_discovery_strategies.pop(package_key, None)
            cls._package_policy_strategies.pop(package_key, None)
            cls._package_mapping_strategies.pop(package_key, None)
    
    @classmethod
    def clear_module_strategies(cls, package_name: str) -> None:
        """Clear all module strategies for a package."""
        package_key = package_name.lower()
        with cls._lock:
            cls._module_helper_strategies.pop(package_key, None)
            cls._module_manager_strategies.pop(package_key, None)
            cls._module_caching_strategies.pop(package_key, None)
    
    @classmethod
    def clear_all_strategies(cls, package_name: str) -> None:
        """Clear all strategies (package and module) for a package."""
        cls.clear_package_strategies(package_name)
        cls.clear_module_strategies(package_name)
    
    # ========================================================================
    # Global Strategy Management (for runtime swapping)
    # ========================================================================
    
    @classmethod
    def register_install_strategy(cls, name: str, strategy: 'IInstallStrategy') -> None:
        """
        Register a global installation strategy for runtime swapping.
        
        Args:
            name: Strategy name (e.g., 'pip', 'wheel', 'async', 'cached')
            strategy: Strategy instance implementing IInstallStrategy
        """
        with cls._lock:
            cls._global_install_strategies[name] = strategy
            if cls._default_install_strategy is None:
                cls._default_install_strategy = name
    
    @classmethod
    def get_install_strategy(cls, name: Optional[str] = None) -> Optional['IInstallStrategy']:
        """
        Get global installation strategy by name.
        
        Args:
            name: Strategy name (uses default if None)
            
        Returns:
            Strategy instance or None if not found
        """
        with cls._lock:
            if name is None:
                name = cls._default_install_strategy
            return cls._global_install_strategies.get(name) if name else None
    
    @classmethod
    def register_load_strategy(cls, name: str, strategy: 'ILoadStrategy') -> None:
        """
        Register a global loading strategy for runtime swapping.
        
        Args:
            name: Strategy name (e.g., 'lazy', 'simple', 'advanced')
            strategy: Strategy instance implementing ILoadStrategy
        """
        with cls._lock:
            cls._global_load_strategies[name] = strategy
            if cls._default_load_strategy is None:
                cls._default_load_strategy = name
    
    @classmethod
    def get_load_strategy(cls, name: Optional[str] = None) -> Optional['ILoadStrategy']:
        """
        Get global loading strategy by name.
        
        Args:
            name: Strategy name (uses default if None)
            
        Returns:
            Strategy instance or None if not found
        """
        with cls._lock:
            if name is None:
                name = cls._default_load_strategy
            return cls._global_load_strategies.get(name) if name else None
    
    @classmethod
    def register_cache_strategy(cls, name: str, strategy: 'ICacheStrategy') -> None:
        """
        Register a global caching strategy for runtime swapping.
        
        Args:
            name: Strategy name (e.g., 'lru', 'lfu', 'ttl', 'multitier')
            strategy: Strategy instance implementing ICacheStrategy
        """
        with cls._lock:
            cls._global_cache_strategies[name] = strategy
            if cls._default_cache_strategy is None:
                cls._default_cache_strategy = name
    
    @classmethod
    def get_cache_strategy(cls, name: Optional[str] = None) -> Optional['ICacheStrategy']:
        """
        Get global caching strategy by name.
        
        Args:
            name: Strategy name (uses default if None)
            
        Returns:
            Strategy instance or None if not found
        """
        with cls._lock:
            if name is None:
                name = cls._default_cache_strategy
            return cls._global_cache_strategies.get(name) if name else None
    
    @classmethod
    def swap_install_strategy(cls, name: str) -> bool:
        """Swap to a different global installation strategy."""
        with cls._lock:
            if name in cls._global_install_strategies:
                cls._default_install_strategy = name
                return True
            return False
    
    @classmethod
    def swap_load_strategy(cls, name: str) -> bool:
        """Swap to a different global loading strategy."""
        with cls._lock:
            if name in cls._global_load_strategies:
                cls._default_load_strategy = name
                return True
            return False
    
    @classmethod
    def swap_cache_strategy(cls, name: str) -> bool:
        """Swap to a different global caching strategy."""
        with cls._lock:
            if name in cls._global_cache_strategies:
                cls._default_cache_strategy = name
                return True
            return False

__all__ = ['StrategyRegistry']

