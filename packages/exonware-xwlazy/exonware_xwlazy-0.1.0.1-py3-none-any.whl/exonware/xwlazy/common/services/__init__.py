"""
Common Services

Shared services used by both modules and packages.
"""

from .dependency_mapper import DependencyMapper
from .spec_cache import (
    _spec_cache_get,
    _spec_cache_put,
    _spec_cache_clear,
    _cache_spec_if_missing,
    get_stdlib_module_set,
)
from .state_manager import LazyStateManager
from .keyword_detection import (
    enable_keyword_detection,
    is_keyword_detection_enabled,
    get_keyword_detection_keyword,
    check_package_keywords,
    _detect_lazy_installation,
    _detect_meta_info_mode,
)
from .install_cache_utils import (
    get_default_cache_dir,
    get_cache_dir,
    get_wheel_path,
    get_install_tree_dir,
    get_site_packages_dir,
    pip_install_from_path,
    ensure_cached_wheel,
    install_from_cached_tree,
    materialize_cached_tree,
    has_cached_install_tree,
    install_from_cached_wheel,
)
from .install_async_utils import (
    get_package_size_mb,
    async_install_package,
    async_uninstall_package,
)

__all__ = [
    'DependencyMapper',
    '_spec_cache_get',
    '_spec_cache_put',
    '_spec_cache_clear',
    '_cache_spec_if_missing',
    'get_stdlib_module_set',
    'LazyStateManager',
    'enable_keyword_detection',
    'is_keyword_detection_enabled',
    'get_keyword_detection_keyword',
    'check_package_keywords',
    '_detect_lazy_installation',
    '_detect_meta_info_mode',
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
    'get_package_size_mb',
    'async_install_package',
    'async_uninstall_package',
]

