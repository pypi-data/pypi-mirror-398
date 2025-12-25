#!/usr/bin/env python3
"""
#exonware/xwdata/tests/1.unit/references_tests/test_resolver.py

Unit tests for ReferenceResolver.

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
from exonware.xwdata.config import XWDataConfig
from exonware.xwdata.errors import XWDataReferenceError, XWDataCircularReferenceError
from exonware.xwdata.data.strategies.json import JSONFormatStrategy


@pytest.mark.xwdata_unit
class TestReferenceResolver:
    """Test ReferenceResolver core functionality."""
    
    @pytest.mark.asyncio
    async def test_resolver_creation(self):
        """Test resolver can be created with default config."""
        resolver = ReferenceResolver()
        assert resolver is not None
        assert resolver._config is not None
    
    @pytest.mark.asyncio
    async def test_resolve_simple_file_reference(self, ref_test_files):
        """Test resolving simple file reference."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Data with reference
        data = {
            "name": "Main",
            "external": {"$ref": "external.json"}
        }
        
        # Resolve
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=ref_test_files['dir']
        )
        
        # Verify resolution
        assert resolved is not None
        assert resolved['name'] == "Main"
        assert 'external' in resolved
        assert resolved['external']['externalName'] == "External Document"
        assert resolved['external']['value'] == 42
    
    @pytest.mark.asyncio
    async def test_resolve_json_pointer(self, ref_test_files):
        """Test resolving JSON Pointer reference."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Data with JSON Pointer reference
        data = {
            "pet": {"$ref": "definitions.json#/definitions/Pet"}
        }
        
        # Resolve
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=ref_test_files['dir']
        )
        
        # Verify resolution
        assert resolved is not None
        assert 'pet' in resolved
        assert resolved['pet']['type'] == "object"
        assert 'properties' in resolved['pet']
        assert 'name' in resolved['pet']['properties']
    
    @pytest.mark.asyncio
    async def test_circular_reference_detection(self, circular_ref_files):
        """Test circular reference detection."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Load file with circular reference
        file_a_path = circular_ref_files['file_a']
        with open(file_a_path) as f:
            data = json.load(f)
        
        # Should detect circular reference
        with pytest.raises(XWDataCircularReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=circular_ref_files['dir']
            )
        
        # Verify error message
        assert "circular" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_missing_file_error(self, temp_ref_dir):
        """Test error handling for missing referenced file."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        data = {
            "ref": {"$ref": "nonexistent.json"}
        }
        
        # Should raise reference error
        with pytest.raises(XWDataReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=temp_ref_dir
            )
        
        # Verify helpful error message
        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "failed" in error_msg
    
    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, temp_ref_dir):
        """Test security: path traversal prevention."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Malicious path traversal attempt
        data = {
            "dangerous": {"$ref": "../../../etc/passwd"}
        }
        
        # Should raise security error
        with pytest.raises(XWDataReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=temp_ref_dir
            )
        
        # Error should indicate security/path issue
        error_msg = str(exc_info.value).lower()
        assert "path" in error_msg or "validation" in error_msg or "failed" in error_msg
    
    @pytest.mark.asyncio
    async def test_caching_works(self, ref_test_files):
        """Test that reference caching works."""
        config = XWDataConfig.default()
        config.reference.cache_resolved = True
        
        resolver = ReferenceResolver(config=config)
        strategy = JSONFormatStrategy()
        
        data = {
            "ref1": {"$ref": "external.json"},
            "ref2": {"$ref": "external.json"}  # Same reference
        }
        
        # Resolve
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=ref_test_files['dir']
        )
        
        # Verify both resolved to same data
        assert resolved['ref1'] == resolved['ref2']
        assert resolved['ref1']['externalName'] == "External Document"
    
    @pytest.mark.asyncio
    async def test_max_depth_prevention(self, temp_ref_dir):
        """Test max resolution depth prevents infinite loops."""
        # Create deeply nested references
        for i in range(15):
            data = {"ref": {"$ref": f"level{i+1}.json"}}
            file_path = temp_ref_dir / f"level{i}.json"
            file_path.write_text(json.dumps(data))
        
        # Final level with no reference
        final_data = {"value": "end"}
        (temp_ref_dir / "level15.json").write_text(json.dumps(final_data))
        
        config = XWDataConfig.default()
        config.reference.max_resolution_depth = 5  # Set low limit
        
        resolver = ReferenceResolver(config=config)
        strategy = JSONFormatStrategy()
        
        # Load first level
        with open(temp_ref_dir / "level0.json") as f:
            data = json.load(f)
        
        # Should hit max depth
        with pytest.raises(XWDataReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=temp_ref_dir
            )
        
        # Verify error about depth
        assert "depth" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_no_references_returns_unchanged(self):
        """Test data without references returns unchanged."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        data = {
            "name": "Test",
            "value": 123,
            "nested": {"key": "value"}
        }
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=None
        )
        
        # Should return same data
        assert resolved == data
    
    @pytest.mark.asyncio
    async def test_nested_references(self, temp_ref_dir):
        """Test resolving nested references (reference within resolved data)."""
        # Create level3.json (no refs)
        level3_data = {"value": "final", "level": 3}
        (temp_ref_dir / "level3.json").write_text(json.dumps(level3_data))
        
        # Create level2.json (refs level3)
        level2_data = {"level": 2, "next": {"$ref": "level3.json"}}
        (temp_ref_dir / "level2.json").write_text(json.dumps(level2_data))
        
        # Create level1.json (refs level2)
        level1_data = {"level": 1, "next": {"$ref": "level2.json"}}
        (temp_ref_dir / "level1.json").write_text(json.dumps(level1_data))
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Load level1
        with open(temp_ref_dir / "level1.json") as f:
            data = json.load(f)
        
        # Resolve all levels
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify complete resolution
        assert resolved['level'] == 1
        assert resolved['next']['level'] == 2
        assert resolved['next']['next']['level'] == 3
        assert resolved['next']['next']['value'] == "final"
    
    @pytest.mark.asyncio
    async def test_resolve_reference_direct(self, ref_test_files):
        """Test resolve_reference method directly."""
        resolver = ReferenceResolver()
        
        reference = {
            'uri': 'external.json',
            'type': 'file'
        }
        
        resolved = await resolver.resolve_reference(
            reference=reference,
            base_path=ref_test_files['dir']
        )
        
        assert resolved is not None
        assert resolved['externalName'] == "External Document"
    
    @pytest.mark.asyncio
    async def test_json_pointer_array_index(self, temp_ref_dir):
        """Test JSON Pointer with array indices."""
        # Create file with arrays
        array_data = {
            "items": [
                {"id": 1, "name": "First"},
                {"id": 2, "name": "Second"},
                {"id": 3, "name": "Third"}
            ]
        }
        (temp_ref_dir / "arrays.json").write_text(json.dumps(array_data))
        
        # Reference specific array item
        data = {
            "selected": {"$ref": "arrays.json#/items/1"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify correct item resolved
        assert resolved['selected']['id'] == 2
        assert resolved['selected']['name'] == "Second"
    
    @pytest.mark.asyncio
    async def test_json_pointer_special_chars(self, temp_ref_dir):
        """Test JSON Pointer with special characters (~, /)."""
        # Create file with special char keys
        special_data = {
            "a/b": {"value": "slash"},
            "c~d": {"value": "tilde"},
            "m~n": {"value": "tilde2"}
        }
        (temp_ref_dir / "special.json").write_text(json.dumps(special_data))
        
        # Reference with encoded special chars (~1 for /, ~0 for ~)
        data = {
            "slash": {"$ref": "special.json#/a~1b"},
            "tilde": {"$ref": "special.json#/c~0d"}
        }
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        resolved = await resolver.resolve(
            data=data,
            strategy=strategy,
            base_path=temp_ref_dir
        )
        
        # Verify special chars handled correctly
        assert resolved['slash']['value'] == "slash"
        assert resolved['tilde']['value'] == "tilde"


@pytest.mark.xwdata_unit
@pytest.mark.xwdata_security
class TestReferenceResolverSecurity:
    """Security tests for reference resolution."""
    
    @pytest.mark.asyncio
    async def test_disallowed_scheme_rejected(self, temp_ref_dir):
        """Test that disallowed URI schemes are rejected."""
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        # Try FTP (not in allowed schemes)
        data = {
            "bad": {"$ref": "ftp://example.com/data.json"}
        }
        
        with pytest.raises(XWDataReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=temp_ref_dir
            )
        
        error_msg = str(exc_info.value).lower()
        assert "scheme" in error_msg or "unsupported" in error_msg
    
    @pytest.mark.asyncio
    async def test_file_size_limit_enforced(self, temp_ref_dir):
        """Test that file size limits are enforced."""
        # Create large file (simulate > 10MB)
        large_data = {"data": "x" * (11 * 1024 * 1024)}  # 11MB
        large_file = temp_ref_dir / "large.json"
        large_file.write_text(json.dumps(large_data))
        
        resolver = ReferenceResolver()
        strategy = JSONFormatStrategy()
        
        data = {
            "large": {"$ref": "large.json"}
        }
        
        with pytest.raises(XWDataReferenceError) as exc_info:
            await resolver.resolve(
                data=data,
                strategy=strategy,
                base_path=temp_ref_dir
            )
        
        error_msg = str(exc_info.value).lower()
        assert "size" in error_msg or "limit" in error_msg

