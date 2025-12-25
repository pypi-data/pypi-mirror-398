#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/serialization/jsonlines.py

JSON Lines Serializer

Streaming JSON format (one JSON object per line).
This is an xwdata-exclusive format optimized for streaming.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

import json
from typing import Any, Union
from exonware.xwsystem import get_logger

from ..base import AXWDataSerializer
from ..errors import XWDataParseError, XWDataSerializeError

logger = get_logger(__name__)


class JSONLinesSerializer(AXWDataSerializer):
    """
    JSON Lines (JSONL/NDJSON) serializer for streaming data.
    
    Format: One JSON object per line
    - Optimized for streaming large datasets
    - Each line is valid JSON
    - No commas between objects
    - Efficient for append operations
    """
    
    def __init__(self):
        """Initialize JSON Lines serializer."""
        super().__init__()
        self._name = 'jsonlines'
        self._extensions = ['jsonl', 'ndjson']
    
    async def serialize(self, data: Any, **opts) -> str:
        """
        Serialize to JSON Lines format.
        
        Args:
            data: Data to serialize (should be list of objects)
            **opts: Serialization options
            
        Returns:
            JSON Lines string
        """
        try:
            # If data is a list, serialize each item as a line
            if isinstance(data, list):
                lines = []
                for item in data:
                    line = json.dumps(item, ensure_ascii=False)
                    lines.append(line)
                return '\n'.join(lines)
            
            # If single object, serialize as single line
            return json.dumps(data, ensure_ascii=False)
            
        except Exception as e:
            raise XWDataSerializeError(
                f"Failed to serialize to JSON Lines: {e}",
                format='jsonlines'
            ) from e
    
    async def deserialize(self, content: Union[str, bytes], **opts) -> list[Any]:
        """
        Deserialize from JSON Lines format.
        
        Args:
            content: JSON Lines content
            **opts: Parse options
            
        Returns:
            List of parsed objects
        """
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        try:
            lines = content.strip().split('\n')
            results = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines
                
                try:
                    obj = json.loads(line)
                    results.append(obj)
                except json.JSONDecodeError as e:
                    raise XWDataParseError(
                        f"Invalid JSON on line {i+1}: {e.msg}",
                        format='jsonlines',
                        line=i+1,
                        column=e.colno
                    ) from e
            
            return results
            
        except XWDataParseError:
            raise
        except Exception as e:
            raise XWDataParseError(
                f"Failed to parse JSON Lines: {e}",
                format='jsonlines'
            ) from e
    
    def detect(self, content: Union[str, bytes]) -> float:
        """
        Detect if content is JSON Lines.
        
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
        
        lines = content.strip().split('\n')
        
        # Empty content
        if not lines or all(not line.strip() for line in lines):
            return 0.0
        
        # Check if each line is valid JSON
        valid_json_lines = 0
        non_empty_lines = 0
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
            
            non_empty_lines += 1
            
            try:
                json.loads(line)
                valid_json_lines += 1
            except:
                pass
        
        if non_empty_lines == 0:
            return 0.0
        
        ratio = valid_json_lines / non_empty_lines
        
        # High confidence if most lines are valid JSON
        if ratio >= 0.8:
            return 0.9
        elif ratio >= 0.5:
            return 0.6
        else:
            return 0.0


__all__ = ['JSONLinesSerializer']

