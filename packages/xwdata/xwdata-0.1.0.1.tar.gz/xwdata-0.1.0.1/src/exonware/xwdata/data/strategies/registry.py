#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/registry.py

Format Strategy Registry

Registry for format-specific strategies with auto-discovery and
thread-safe registration.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import threading
from typing import Optional
from pathlib import Path
from exonware.xwsystem import get_logger

from ...contracts import IFormatStrategy
from ...errors import XWDataStrategyError

logger = get_logger(__name__)


class FormatStrategyRegistry:
    """
    Thread-safe registry for format strategies.
    
    Features:
    - Thread-safe registration
    - Auto-discovery of strategy modules
    - Extension-based lookup
    - Format-based lookup
    """
    
    def __init__(self):
        """Initialize strategy registry."""
        self._strategies: dict[str, IFormatStrategy] = {}
        self._extensions: dict[str, IFormatStrategy] = {}
        self._lock = threading.RLock()
        self._auto_discovery_enabled = True
        self._discovery_complete = False
    
    def register(self, strategy: IFormatStrategy) -> None:
        """
        Register a format strategy.
        
        Args:
            strategy: Strategy instance to register
        """
        with self._lock:
            # Register by name
            self._strategies[strategy.name] = strategy
            
            # Register by extensions
            for ext in strategy.extensions:
                clean_ext = ext.lstrip('.')
                if clean_ext in self._extensions:
                    logger.warning(
                        f"Extension '{clean_ext}' already registered, "
                        f"overriding with {strategy.name}"
                    )
                self._extensions[clean_ext] = strategy
            
            logger.debug(f"Registered strategy: {strategy.name}")
    
    def get(self, format_or_ext: str) -> Optional[IFormatStrategy]:
        """
        Get strategy by format name or extension.
        
        Args:
            format_or_ext: Format name or extension
            
        Returns:
            Strategy instance or None
        """
        with self._lock:
            # Ensure auto-discovery has run
            if not self._discovery_complete and self._auto_discovery_enabled:
                self._auto_discover()
            
            # Clean format/extension
            clean_name = format_or_ext.lstrip('.').lower()
            
            # Try format name first
            if clean_name in self._strategies:
                return self._strategies[clean_name]
            
            # Try extension
            if clean_name in self._extensions:
                return self._extensions[clean_name]
            
            return None
    
    def get_available_formats(self) -> list[str]:
        """Get list of all registered formats."""
        with self._lock:
            if not self._discovery_complete and self._auto_discovery_enabled:
                self._auto_discover()
            
            return list(self._strategies.keys())
    
    def _auto_discover(self) -> None:
        """Auto-discover and register strategies."""
        if self._discovery_complete:
            return
        
        try:
            # Import and register built-in strategies
            from .json import JSONFormatStrategy
            from .xml import XMLFormatStrategy
            from .yaml import YAMLFormatStrategy
            
            self.register(JSONFormatStrategy())
            self.register(XMLFormatStrategy())
            self.register(YAMLFormatStrategy())
            
            # Try optional formats
            try:
                from .toml import TOMLFormatStrategy, TOML_AVAILABLE
                if TOML_AVAILABLE:
                    self.register(TOMLFormatStrategy())
            except (ImportError, NameError, AttributeError):
                logger.debug("TOML strategy not available")
            
            try:
                from .csv import CSVFormatStrategy
                # CSV is always available (uses stdlib)
                self.register(CSVFormatStrategy())
            except (ImportError, NameError, AttributeError):
                logger.debug("CSV strategy not available")
            
            self._discovery_complete = True
            logger.debug(f"Auto-discovery complete: {len(self._strategies)} strategies registered")
            
        except Exception as e:
            logger.warning(f"Auto-discovery failed: {e}")
    
    def unregister(self, format_name: str) -> bool:
        """
        Unregister a strategy.
        
        Args:
            format_name: Format name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        with self._lock:
            if format_name not in self._strategies:
                return False
            
            strategy = self._strategies[format_name]
            
            # Remove from strategies
            del self._strategies[format_name]
            
            # Remove from extensions
            for ext in list(self._extensions.keys()):
                if self._extensions[ext] is strategy:
                    del self._extensions[ext]
            
            logger.debug(f"Unregistered strategy: {format_name}")
            return True


__all__ = ['FormatStrategyRegistry']

