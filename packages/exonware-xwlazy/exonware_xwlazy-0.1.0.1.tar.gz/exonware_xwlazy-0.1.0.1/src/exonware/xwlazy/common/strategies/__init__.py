"""
Common Caching Strategies - Shared by modules and packages.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 15-Nov-2025

Generic caching strategies that work with ANY data type.
"""

from .caching_dict import DictCache
from .caching_lru import LRUCache
from .caching_lfu import LFUCache
from .caching_ttl import TTLCache
from .caching_multitier import MultiTierCacheStrategy
from .caching_installation import InstallationCacheWrapper

__all__ = [
    'DictCache',
    'LRUCache',
    'LFUCache',
    'TTLCache',
    'MultiTierCacheStrategy',
    'InstallationCacheWrapper',
]

