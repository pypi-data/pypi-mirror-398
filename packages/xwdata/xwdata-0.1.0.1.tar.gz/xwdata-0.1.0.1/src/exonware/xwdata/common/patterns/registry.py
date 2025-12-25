#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/common/patterns/registry.py

Generic Registry Pattern

Thread-safe registry for managing components.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import threading
from typing import Any, Optional
from exonware.xwsystem import get_logger

logger = get_logger(__name__)


class Registry:
    """
    Generic thread-safe registry pattern.
    
    Provides registration and lookup for components.
    """
    
    def __init__(self, name: str = "Registry"):
        """
        Initialize registry.
        
        Args:
            name: Registry name for logging
        """
        self._name = name
        self._items: dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register(self, key: str, item: Any) -> None:
        """Register an item."""
        with self._lock:
            if key in self._items:
                logger.warning(f"{self._name}: Overriding existing registration for '{key}'")
            self._items[key] = item
            logger.debug(f"{self._name}: Registered '{key}'")
    
    def get(self, key: str) -> Optional[Any]:
        """Get registered item."""
        with self._lock:
            return self._items.get(key)
    
    def unregister(self, key: str) -> bool:
        """Unregister an item."""
        with self._lock:
            if key in self._items:
                del self._items[key]
                logger.debug(f"{self._name}: Unregistered '{key}'")
                return True
            return False
    
    def list_keys(self) -> list[str]:
        """List all registered keys."""
        with self._lock:
            return list(self._items.keys())
    
    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._items.clear()
            logger.debug(f"{self._name}: Cleared all registrations")


__all__ = ['Registry']

