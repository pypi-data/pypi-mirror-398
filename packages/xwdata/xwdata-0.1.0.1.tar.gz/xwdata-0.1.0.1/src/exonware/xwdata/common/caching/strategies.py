#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/caching/strategies.py

Cache Strategy Implementations

Specialized caches for parse and serialize operations.

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

logger = get_logger(__name__)


class LRUCache:
    """Thread-safe LRU cache with statistics."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum cache size
        """
        self._cache: OrderedDict = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
        self._stats = {'hits': 0, 'misses': 0, 'sets': 0, 'evictions': 0}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache with LRU update."""
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._stats['hits'] += 1
                return self._cache[key]
            
            self._stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set in cache with LRU eviction."""
        with self._lock:
            # Remove if exists (will re-add)
            if key in self._cache:
                del self._cache[key]
            
            # Add to cache
            self._cache[key] = value
            self._stats['sets'] += 1
            
            # Evict oldest if over size
            if len(self._cache) > self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats['evictions'] += 1
    
    async def invalidate(self, key: str) -> None:
        """Invalidate cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """Clear cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
            
            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'sets': self._stats['sets'],
                'evictions': self._stats['evictions'],
                'hit_rate': f"{hit_rate:.1f}%",
                'size': len(self._cache),
                'max_size': self._max_size
            }


class ParseCache(LRUCache):
    """Specialized cache for parse operations."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize parse cache."""
        super().__init__(max_size)
        logger.debug(f"ParseCache initialized (max_size={max_size})")


class SerializeCache(LRUCache):
    """Specialized cache for serialize operations."""
    
    def __init__(self, max_size: int = 500):
        """Initialize serialize cache."""
        super().__init__(max_size)
        logger.debug(f"SerializeCache initialized (max_size={max_size})")


__all__ = ['ParseCache', 'SerializeCache', 'LRUCache']

