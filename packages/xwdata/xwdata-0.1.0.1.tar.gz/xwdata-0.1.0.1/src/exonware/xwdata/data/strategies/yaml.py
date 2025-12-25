#!/usr/bin/env python3
"""
#exonware/xwdata/src/exonware/xwdata/data/strategies/yaml.py

YAML Format Strategy

Lightweight YAML-specific logic for metadata and references.
Serialization is handled by xwsystem.serialization.YamlSerializer.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: 26-Oct-2025
"""

from typing import Any
from ...base import AFormatStrategy


class YAMLFormatStrategy(AFormatStrategy):
    """
    YAML format strategy providing xwdata-specific logic.
    
    Provides:
    - Metadata extraction (anchors, tags, multi-document)
    - Reference detection (anchor references *anchor)
    - Type mapping (YAML types ↔ universal types)
    
    Does NOT provide:
    - Serialization (uses xwsystem.serialization.YamlSerializer)
    """
    
    def __init__(self):
        """Initialize YAML strategy."""
        super().__init__()
        self._name = 'yaml'
        self._extensions = ['yaml', 'yml']
        
        # Reference patterns for YAML
        self._reference_patterns = {
            'yaml_anchor_ref': {
                'pattern': r'^\*\w+'  # *anchor_name
            },
            'yaml_merge_ref': {
                'pattern': r'^<<$'    # << merge key
            }
        }
        
        # Type mapping
        self._type_mapping = {
            'str': 'str',
            'int': 'int',
            'float': 'float',
            'bool': 'bool',
            'list': 'list',
            'dict': 'dict',
            'null': 'NoneType'
        }
    
    async def extract_metadata(self, data: Any, **opts) -> dict[str, Any]:
        """Extract YAML-specific metadata."""
        metadata = {}
        
        # YAML can have multiple documents (list of dicts/lists)
        if isinstance(data, list) and len(data) > 1:
            # Check if this looks like multi-document YAML
            if all(isinstance(item, (dict, list)) for item in data):
                metadata['multi_document'] = True
                metadata['document_count'] = len(data)
        
        # Detect YAML tags (usually preserved in metadata by some parsers)
        if isinstance(data, dict):
            if '!!python/object' in str(data):
                metadata['has_custom_tags'] = True
        
        metadata['format'] = 'yaml'
        return metadata
    
    async def detect_references(self, data: Any, **opts) -> list[dict[str, Any]]:
        """
        Detect YAML-specific references.
        
        Note: YAML anchors (*ref) and merge keys (<<) are typically
        resolved during parsing by the YAML parser. This method detects
        any that remain in the parsed data structure.
        """
        references = []
        
        if isinstance(data, dict):
            # Detect merge key (though usually resolved by parser)
            if '<<' in data:
                merge_value = data['<<']
                references.append({
                    'type': 'yaml_merge_ref',
                    'uri': str(merge_value),
                    'format': 'yaml',
                    'metadata': {'merge_key': True}
                })
            
            # Recursively check nested
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


__all__ = ['YAMLFormatStrategy']

