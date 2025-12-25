#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_load_save.py

Core tests for load/save operations.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1.3
Generation Date: 26-Oct-2025
"""

import pytest
from pathlib import Path


@pytest.mark.xwdata_core
class TestCoreLoadSave:
    """Core load/save functionality tests."""
    
    @pytest.mark.asyncio
    async def test_create_from_dict(self, simple_dict_data):
        """Test creating XWData from dictionary."""
        from exonware.xwdata import XWData
        
        # Use from_native in async context
        data = XWData.from_native(simple_dict_data)
        assert data is not None
        
        # Verify data
        name = await data.get('name')
        assert name == 'Alice'
    
    @pytest.mark.asyncio
    async def test_to_native(self, simple_dict_data):
        """Test converting to native Python data."""
        from exonware.xwdata import XWData
        
        # Use from_native in async context
        data = XWData.from_native(simple_dict_data)
        native = data.to_native()
        
        assert native == simple_dict_data
        assert isinstance(native, dict)
    
    @pytest.mark.asyncio
    async def test_save_and_load_json(self, simple_dict_data, tmp_path):
        """Test save and load roundtrip with JSON."""
        from exonware.xwdata import XWData
        
        # Create data using from_native
        data = XWData.from_native(simple_dict_data)
        
        # Save to JSON
        json_file = tmp_path / "test.json"
        await data.save(json_file)
        
        assert json_file.exists()
        
        # Load back
        loaded = await XWData.load(json_file)
        loaded_native = loaded.to_native()
        
        assert loaded_native == simple_dict_data


@pytest.mark.xwdata_core
class TestCoreAsync:
    """Core async operations tests."""
    
    @pytest.mark.asyncio
    async def test_async_get(self):
        """Test async get operation."""
        from exonware.xwdata import XWData
        
        # Use from_native in async context
        data = XWData.from_native({'key': 'value'})
        value = await data.get('key')
        
        assert value == 'value'
    
    @pytest.mark.asyncio
    async def test_async_set_cow(self):
        """Test async set with copy-on-write."""
        from exonware.xwdata import XWData
        
        # Use from_native in async context
        data1 = XWData.from_native({'key': 'value1'})
        data2 = await data1.set('key', 'value2')
        
        # Original unchanged (COW)
        val1 = await data1.get('key')
        val2 = await data2.get('key')
        
        assert val1 == 'value1'
        assert val2 == 'value2'
        assert data1 is not data2

