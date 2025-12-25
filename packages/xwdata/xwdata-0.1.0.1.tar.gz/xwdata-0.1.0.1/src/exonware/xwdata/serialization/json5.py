#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/serialization/json5.py

JSON5 Serializer

Extended JSON serializer with JSON5 support (comments, trailing commas, etc.).
This is an xwdata-exclusive format.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any, Union
from exonware.xwsystem import get_logger

from ..base import AXWDataSerializer
from ..errors import XWDataParseError, XWDataSerializeError

logger = get_logger(__name__)


class JSON5Serializer(AXWDataSerializer):
    """
    JSON5 serializer supporting comments and relaxed syntax.
    
    JSON5 features:
    - Single and multi-line comments
    - Trailing commas in objects and arrays
    - Unquoted keys
    - Single-quoted strings
    - Hexadecimal numbers
    - Plus sign for positive numbers
    """
    
    def __init__(self):
        """Initialize JSON5 serializer."""
        super().__init__()
        self._name = 'json5'
        self._extensions = ['json5']
        
        # Try to import json5 library
        try:
            import json5 as _json5
            self._json5 = _json5
            self._available = True
        except ImportError:
            self._json5 = None
            self._available = False
            logger.warning("json5 library not available, install with: pip install json5")
    
    async def serialize(self, data: Any, **opts) -> str:
        """
        Serialize to JSON5 format.
        
        Args:
            data: Data to serialize
            **opts: Serialization options
            
        Returns:
            JSON5 string
        """
        if not self._available:
            raise XWDataSerializeError(
                "JSON5 serializer not available - install json5 library",
                format='json5',
                suggestion="Run: pip install json5"
            )
        
        try:
            indent = opts.get('indent', 2)
            return self._json5.dumps(data, indent=indent)
        except Exception as e:
            raise XWDataSerializeError(
                f"Failed to serialize to JSON5: {e}",
                format='json5'
            ) from e
    
    async def deserialize(self, content: Union[str, bytes], **opts) -> Any:
        """
        Deserialize from JSON5 format.
        
        Args:
            content: JSON5 content
            **opts: Parse options
            
        Returns:
            Parsed data
        """
        if not self._available:
            raise XWDataParseError(
                "JSON5 parser not available - install json5 library",
                format='json5',
                suggestion="Run: pip install json5"
            )
        
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        try:
            return self._json5.loads(content)
        except Exception as e:
            raise XWDataParseError(
                f"Failed to parse JSON5: {e}",
                format='json5'
            ) from e
    
    def detect(self, content: Union[str, bytes]) -> float:
        """
        Detect if content is JSON5.
        
        Args:
            content: Content to check
            
        Returns:
            Confidence score 0.0-1.0
        """
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8', errors='ignore')
            except:
                return 0.0
        
        content = content.strip()
        
        # Check for JSON5-specific features
        confidence = 0.0
        
        # Comments
        if '//' in content or '/*' in content:
            confidence += 0.3
        
        # Trailing commas
        if ',]' in content or ',}' in content:
            confidence += 0.2
        
        # JSON-like structure
        if content.startswith(('{', '[')):
            confidence += 0.3
        
        # Single quotes
        if "'" in content and '"' not in content:
            confidence += 0.2
        
        return min(confidence, 1.0)


__all__ = ['JSON5Serializer']

