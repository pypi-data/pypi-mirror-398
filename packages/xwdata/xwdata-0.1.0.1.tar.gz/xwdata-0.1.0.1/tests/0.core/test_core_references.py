#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_references.py

Core tests for reference resolution - 80/20 rule.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 28-Oct-2025
"""

import pytest
import json
from pathlib import Path

from exonware.xwdata.data.references.resolver import ReferenceResolver
from exonware.xwdata.data.strategies.json import JSONFormatStrategy
from exonware.xwdata.errors import XWDataCircularReferenceError


@pytest.mark.xwdata_core
class TestCoreReferences:
    """Core reference resolution tests - fast, high-value."""
    
    @pytest.mark.asyncio
    async def test_basic_json_ref(self, tmp_path):
        """Test basic JSON $ref resolution."""
        # Create external file
        external_data = {"name": "External", "value": 42}
        external_file = tmp_path / "external.json"
        external_file.write_text(json.dumps(external_data))
        
        # Data with reference
        data = {
            "main": "data",
            "ref": {"$ref": "external.json"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=tmp_path
        )
        
        # Should resolve reference
        assert resolved['main'] == "data"
        assert resolved['ref']['name'] == "External"
        assert resolved['ref']['value'] == 42
    
    @pytest.mark.asyncio
    async def test_json_pointer(self, tmp_path):
        """Test JSON Pointer (#/path) resolution."""
        # Create file with nested structure
        file_data = {
            "definitions": {
                "item": {"type": "object", "name": "Item"}
            }
        }
        file_path = tmp_path / "defs.json"
        file_path.write_text(json.dumps(file_data))
        
        # Reference with JSON Pointer
        data = {
            "schema": {"$ref": "defs.json#/definitions/item"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=tmp_path
        )
        
        # Should resolve to specific path
        assert resolved['schema']['type'] == "object"
        assert resolved['schema']['name'] == "Item"
    
    @pytest.mark.asyncio
    async def test_circular_detection(self, tmp_path):
        """Test circular reference detection."""
        # Create circular references
        a_data = {"name": "A", "next": {"$ref": "b.json"}}
        b_data = {"name": "B", "next": {"$ref": "a.json"}}
        
        (tmp_path / "a.json").write_text(json.dumps(a_data))
        (tmp_path / "b.json").write_text(json.dumps(b_data))
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Load file A
        with open(tmp_path / "a.json") as f:
            data = json.load(f)
        
        # Should detect circular reference
        with pytest.raises(XWDataCircularReferenceError):
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=tmp_path
            )
    
    @pytest.mark.asyncio
    async def test_no_refs_unchanged(self):
        """Test data without references remains unchanged."""
        data = {"name": "Test", "value": 123}
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=None
        )
        
        assert resolved == data
    
    @pytest.mark.asyncio
    async def test_ref_caching(self, tmp_path):
        """Test reference caching for performance."""
        # Create referenced file
        ext_data = {"cached": True}
        (tmp_path / "cached.json").write_text(json.dumps(ext_data))
        
        # Multiple references to same file
        data = {
            "ref1": {"$ref": "cached.json"},
            "ref2": {"$ref": "cached.json"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=tmp_path
        )
        
        # Both should resolve to same data
        assert resolved['ref1'] == resolved['ref2']
        assert resolved['ref1']['cached'] == True

