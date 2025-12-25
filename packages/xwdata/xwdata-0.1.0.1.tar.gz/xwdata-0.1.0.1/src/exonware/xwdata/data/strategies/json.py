#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/json.py

JSON Format Strategy

Lightweight JSON-specific logic for metadata and references.
Serialization is handled by xwsystem.serialization.JsonSerializer.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any
from ...base import AFormatStrategy


class JSONFormatStrategy(AFormatStrategy):
    """
    JSON format strategy providing xwdata-specific logic.
    
    Provides:
    - Metadata extraction (reserved chars like $, @)
    - Reference detection ($ref, @id patterns)
    - Type mapping (JSON types ↔ universal types)
    
    Does NOT provide:
    - Serialization (uses xwsystem.serialization.JsonSerializer)
    """
    
    def __init__(self):
        """Initialize JSON strategy."""
        super().__init__()
        self._name = 'json'
        self._extensions = ['json', 'js']
        
        # Reference patterns for JSON
        self._reference_patterns = {
            'json_schema_ref': {
                'key': '$ref',
                'pattern': r'^\$ref$'
            },
            'json_ld_ref': {
                'key': '@id',
                'pattern': r'^@id$'
            }
        }
        
        # Type mapping
        self._type_mapping = {
            'string': 'str',
            'number': 'float',
            'integer': 'int',
            'boolean': 'bool',
            'array': 'list',
            'object': 'dict',
            'null': 'NoneType'
        }
    
    async def extract_metadata(self, data: Any, **opts) -> dict[str, Any]:
        """Extract JSON-specific metadata."""
        metadata = {}
        
        if isinstance(data, dict):
            # Detect reserved characters in keys
            reserved_keys = [k for k in data.keys() if k.startswith(('$', '@'))]
            if reserved_keys:
                metadata['reserved_chars'] = list(set(k[0] for k in reserved_keys))
                metadata['reserved_keys'] = reserved_keys
            
            # Detect semantic types
            if '$schema' in data:
                metadata['has_schema'] = True
                metadata['schema_uri'] = data['$schema']
            
            if '@context' in data:
                metadata['has_json_ld'] = True
                metadata['context'] = data['@context']
        
        metadata['format'] = 'json'
        return metadata
    
    async def detect_references(self, data: Any, **opts) -> list[dict[str, Any]]:
        """Detect JSON-specific references."""
        references = []
        
        if isinstance(data, dict):
            # JSON Schema $ref pattern
            if '$ref' in data and isinstance(data['$ref'], str):
                references.append({
                    'type': 'json_schema_ref',
                    'uri': data['$ref'],
                    'format': 'json',
                    'metadata': {k: v for k, v in data.items() if k != '$ref'}
                })
            
            # JSON-LD @id pattern
            if '@id' in data and isinstance(data['@id'], str):
                references.append({
                    'type': 'json_ld_ref',
                    'uri': data['@id'],
                    'format': 'json',
                    'metadata': {k: v for k, v in data.items() if k != '@id'}
                })
            
            # Recursively check nested structures
            for value in data.values():
                if isinstance(value, (dict, list)):
                    nested_refs = await self.detect_references(value)
                    references.extend(nested_refs)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    nested_refs = await self.detect_references(item)
                    references.extend(nested_refs)
        
        return references


__all__ = ['JSONFormatStrategy']

