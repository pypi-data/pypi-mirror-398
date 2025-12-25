#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/caching/cache_manager.py

Cache Manager Implementation

Manages parse and serialize caches for performance optimization.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Optional
from collections import OrderedDict
import threading
from exonware.xwsystem import get_logger

from ...base import ACacheManager
from ...config import XWDataConfig
from .strategies import ParseCache, SerializeCache

logger = get_logger(__name__)


class CacheManager(ACacheManager):
    """
    Unified cache manager for parse and serialize operations.
    
    Features:
    - LRU eviction policy
    - Thread-safe operations
    - Separate caches for parse/serialize
    - Statistics tracking
    """
    
    def __init__(self, config: Optional[XWDataConfig] = None):
        """
        Initialize cache manager.
        
        Args:
            config: Optional configuration
        """
        super().__init__()
        self._config = config or XWDataConfig.default()
        
        # Separate caches
        self._parse_cache = ParseCache(self._config.performance.cache_size)
        self._serialize_cache = SerializeCache(self._config.performance.cache_size)
        
        self._enabled = self._config.performance.enable_caching
        
        logger.debug(f"CacheManager initialized (enabled={self._enabled})")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from appropriate cache based on key prefix."""
        if not self._enabled:
            return None
        
        if key.startswith('parse:'):
            return await self._parse_cache.get(key)
        elif key.startswith('serialize:'):
            return await self._serialize_cache.get(key)
        else:
            # Use default cache
            return await super().get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in appropriate cache based on key prefix."""
        if not self._enabled:
            return
        
        if key.startswith('parse:'):
            await self._parse_cache.set(key, value, ttl)
        elif key.startswith('serialize:'):
            await self._serialize_cache.set(key, value, ttl)
        else:
            # Use default cache
            await super().set(key, value, ttl)
    
    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        if key.startswith('parse:'):
            await self._parse_cache.invalidate(key)
        elif key.startswith('serialize:'):
            await self._serialize_cache.invalidate(key)
        else:
            await super().invalidate(key)
    
    async def clear(self) -> None:
        """Clear all caches."""
        await self._parse_cache.clear()
        await self._serialize_cache.clear()
        await super().clear()
        logger.debug("All caches cleared")
    
    def get_stats(self) -> dict[str, Any]:
        """Get combined cache statistics."""
        return {
            'enabled': self._enabled,
            'parse_cache': self._parse_cache.get_stats(),
            'serialize_cache': self._serialize_cache.get_stats(),
            'general_cache': super().get_stats()
        }


__all__ = ['CacheManager']

