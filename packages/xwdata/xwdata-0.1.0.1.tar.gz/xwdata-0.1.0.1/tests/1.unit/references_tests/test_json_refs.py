#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/references_tests/test_json_refs.py

JSON $ref specific tests.

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
from exonware.xwdata.errors import XWDataReferenceError


@pytest.mark.xwdata_unit
class TestJSONReferences:
    """Test JSON $ref specific functionality."""
    
    @pytest.mark.asyncio
    async def test_json_ref_to_definitions(self, temp_ref_dir):
        """Test OpenAPI-style $ref to #/definitions."""
        schema = {
            "definitions": {
                "User": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                }
            },
            "paths": {
                "/users": {
                    "get": {
                        "responses": {
                            "200": {
                                "schema": {"$ref": "#/definitions/User"}
                            }
                        }
                    }
                }
            }
        }
        
        # Save to file
        schema_file = temp_ref_dir / "api.json"
        schema_file.write_text(json.dumps(schema))
        
        # Test file that references the schema
        test_data = {
            "apiSpec": {"$ref": "api.json#/paths//users/get/responses/200/schema"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=test_data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Should resolve the nested $ref too
        assert 'apiSpec' in resolved
    
    @pytest.mark.asyncio
    async def test_multiple_refs_in_structure(self, temp_ref_dir):
        """Test multiple $refs in same data structure."""
        # Create referenced files
        user_def = {"type": "object", "properties": {"name": {"type": "string"}}}
        post_def = {"type": "object", "properties": {"title": {"type": "string"}}}
        
        (temp_ref_dir / "user.json").write_text(json.dumps(user_def))
        (temp_ref_dir / "post.json").write_text(json.dumps(post_def))
        
        # Data with multiple references
        data = {
            "schemas": {
                "user": {"$ref": "user.json"},
                "post": {"$ref": "post.json"}
            }
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify both resolved
        assert resolved['schemas']['user']['type'] == "object"
        assert 'name' in resolved['schemas']['user']['properties']
        assert resolved['schemas']['post']['type'] == "object"
        assert 'title' in resolved['schemas']['post']['properties']
    
    @pytest.mark.asyncio
    async def test_ref_in_array(self, temp_ref_dir):
        """Test $ref inside arrays."""
        # Create item definition
        item = {"id": 1, "name": "Item"}
        (temp_ref_dir / "item.json").write_text(json.dumps(item))
        
        # Array with references
        data = {
            "items": [
                {"$ref": "item.json"},
                {"id": 2, "name": "Inline"},
                {"$ref": "item.json"}
            ]
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify array items resolved
        assert len(resolved['items']) == 3
        assert resolved['items'][0]['id'] == 1
        assert resolved['items'][1]['id'] == 2
        assert resolved['items'][2]['id'] == 1
    
    @pytest.mark.asyncio
    async def test_deeply_nested_refs(self, temp_ref_dir):
        """Test $refs in deeply nested structures."""
        # Create nested data
        deep_value = {"value": "deep"}
        (temp_ref_dir / "deep.json").write_text(json.dumps(deep_value))
        
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "ref": {"$ref": "deep.json"}
                        }
                    }
                }
            }
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify deep resolution
        assert resolved['level1']['level2']['level3']['level4']['ref']['value'] == "deep"
    
    @pytest.mark.asyncio
    async def test_json_schema_composition(self, temp_ref_dir):
        """Test JSON Schema allOf with $refs."""
        base_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}
            }
        }
        
        extended_props = {
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        (temp_ref_dir / "base.json").write_text(json.dumps(base_schema))
        (temp_ref_dir / "extended.json").write_text(json.dumps(extended_props))
        
        # Schema using allOf with refs
        data = {
            "User": {
                "allOf": [
                    {"$ref": "base.json"},
                    {"$ref": "extended.json"}
                ]
            }
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify both schemas resolved
        assert len(resolved['User']['allOf']) == 2
        assert resolved['User']['allOf'][0]['type'] == "object"
        assert 'properties' in resolved['User']['allOf'][1]

