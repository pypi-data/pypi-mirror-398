#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/serialization/registry.py

XWData Serializer Registry

Unified registry combining:
- xwsystem base serializers (24+ formats)
- xwdata extended serializers (JSON5, JSONL, etc.)

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Optional
import threading
from exonware.xwsystem import get_logger
from exonware.xwsystem.serialization import XWSerializer

from ..contracts import IXWDataSerializer

logger = get_logger(__name__)


class XWDataSerializerRegistry:
    """
    Unified serializer registry.
    
    Automatically includes:
    - All xwsystem base serializers (JSON, XML, YAML, etc.)
    - xwdata extended serializers (JSON5, JSONL, etc.)
    - Auto-discovered custom serializers
    
    Priority: xwdata extensions > xwsystem base
    """
    
    def __init__(self):
        """Initialize serializer registry."""
        self._xwsystem_serializer = XWSerializer()
        self._extended_serializers: dict[str, IXWDataSerializer] = {}
        self._lock = threading.RLock()
        self._discovery_complete = False
        
        # Auto-discover xwdata serializers
        self._auto_discover()
    
    def _auto_discover(self) -> None:
        """Auto-discover xwdata extended serializers."""
        if self._discovery_complete:
            return
        
        try:
            # Import and register extended serializers
            from .json5 import JSON5Serializer
            from .jsonlines import JSONLinesSerializer
            
            self.register(JSON5Serializer())
            self.register(JSONLinesSerializer())
            
            self._discovery_complete = True
            logger.debug("Auto-discovered xwdata extended serializers")
            
        except Exception as e:
            logger.warning(f"Auto-discovery failed: {e}")
    
    def register(self, serializer: IXWDataSerializer) -> None:
        """
        Register extended serializer.
        
        Args:
            serializer: Serializer to register
        """
        with self._lock:
            self._extended_serializers[serializer.name] = serializer
            logger.debug(f"Registered extended serializer: {serializer.name}")
    
    def get_serializer(self, format_name: str) -> Optional[Any]:
        """
        Get serializer for format.
        
        Priority: xwdata extensions first, then xwsystem base.
        
        Args:
            format_name: Format name
            
        Returns:
            Serializer instance or None
        """
        with self._lock:
            format_lower = format_name.lower()
            
            # Check xwdata extensions first
            if format_lower in self._extended_serializers:
                logger.debug(f"Using xwdata extended serializer for {format_name}")
                return self._extended_serializers[format_lower]
            
            # Fallback to xwsystem
            logger.debug(f"Using xwsystem base serializer for {format_name}")
            return self._xwsystem_serializer
    
    def get_available_formats(self) -> list[str]:
        """Get all available formats (xwsystem + xwdata)."""
        with self._lock:
            # Get xwsystem formats
            xwsystem_formats = []
            # Get xwdata formats
            xwdata_formats = list(self._extended_serializers.keys())
            
            # Combine
            all_formats = list(set(xwsystem_formats + xwdata_formats))
            return sorted(all_formats)


__all__ = ['XWDataSerializerRegistry']

