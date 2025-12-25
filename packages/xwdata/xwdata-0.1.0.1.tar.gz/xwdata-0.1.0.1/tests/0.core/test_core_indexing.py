#!/usr/bin/env python3
"""
#exonware/xwdata/tests/0.core/test_core_indexing.py

Tests for XWData indexing support (int, slice, str).

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.0.1
Generation Date: 15-Dec-2025
"""

import pytest
from pathlib import Path
from exonware.xwdata import XWData


@pytest.mark.xwdata_core
class TestXWDataIndexing:
    """Test XWData indexing with int, slice, and str keys."""
    
    def test_integer_indexing_list(self):
        """Test integer indexing for list data."""
        data = XWData.from_native([{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}])
        
        # Integer indexing
        first = data[0]
        assert first == {"name": "Alice", "age": 30}
        
        second = data[1]
        assert second == {"name": "Bob", "age": 25}
        
        # Out of range
        with pytest.raises(IndexError):
            _ = data[2]
    
    def test_slice_indexing_list(self):
        """Test slice indexing for list data."""
        data = XWData.from_native([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        # Slice indexing
        first_three = data[0:3]
        assert first_three == [1, 2, 3]
        
        middle = data[2:5]
        assert middle == [3, 4, 5]
        
        all_items = data[:]
        assert all_items == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        last_three = data[-3:]
        assert last_three == [8, 9, 10]
    
    def test_string_key_indexing_dict(self):
        """Test string key indexing for dict data."""
        data = XWData.from_native({"name": "Alice", "age": 30, "city": "NYC"})
        
        # String key indexing
        assert data["name"] == "Alice"
        assert data["age"] == 30
        assert data["city"] == "NYC"
        
        # Missing key
        with pytest.raises(KeyError):
            _ = data["email"]
    
    def test_nested_path_indexing(self):
        """Test nested path indexing."""
        data = XWData.from_native({
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        })
        
        # Nested path
        assert data["users.0.name"] == "Alice"
        assert data["users.1.age"] == 25
        
        # Get list first, then index
        users = data["users"]
        assert users[0]["name"] == "Alice"
        assert users[1]["name"] == "Bob"
    
    def test_mixed_indexing(self):
        """Test mixing different indexing types."""
        data = XWData.from_native({
            "items": [
                {"id": 1, "value": "a"},
                {"id": 2, "value": "b"},
                {"id": 3, "value": "c"}
            ]
        })
        
        # Get list via string key
        items = data["items"]
        assert isinstance(items, list)
        
        # Then index with int
        first_item = items[0]
        assert first_item == {"id": 1, "value": "a"}
        
        # Slice the list
        first_two = items[0:2]
        assert first_two == [{"id": 1, "value": "a"}, {"id": 2, "value": "b"}]
    
    def test_indexing_from_file(self, tmp_path):
        """Test indexing after loading from file."""
        # Create JSON file
        json_file = tmp_path / "data.json"
        json_file.write_text('{"items": [1, 2, 3, 4, 5]}')
        
        # Load file
        data = XWData(str(json_file))
        
        # Index the loaded data
        items = data["items"]
        assert items == [1, 2, 3, 4, 5]
        
        # Integer index
        assert items[0] == 1
        assert items[2] == 3
        
        # Slice
        assert items[1:4] == [2, 3, 4]
    
    def test_indexing_error_cases(self):
        """Test error cases for indexing."""
        # Try to index dict with int
        data = XWData.from_native({"name": "Alice"})
        with pytest.raises((TypeError, KeyError)):
            _ = data[0]
        
        # Try to slice dict
        with pytest.raises(TypeError):
            _ = data[0:2]
        
        # Try to index list with string (not a path)
        data = XWData.from_native([1, 2, 3])
        with pytest.raises((KeyError, TypeError)):
            _ = data["not_a_path"]


@pytest.mark.xwdata_core
class TestXWDataIndexingWithXWNode:
    """Test that XWData properly delegates to XWNode for indexing."""
    
    def test_delegates_to_xwnode_for_int(self):
        """Test that integer indexing uses XWNode when available."""
        data = XWData.from_native([10, 20, 30, 40, 50])
        
        # Should work via XWNode delegation
        assert data[0] == 10
        assert data[2] == 30
        assert data[-1] == 50
    
    def test_delegates_to_xwnode_for_slice(self):
        """Test that slice indexing uses XWNode when available."""
        data = XWData.from_native([10, 20, 30, 40, 50])
        
        # Should work via XWNode delegation
        assert data[0:3] == [10, 20, 30]
        assert data[2:] == [30, 40, 50]
        assert data[:2] == [10, 20]
    
    def test_delegates_to_xwnode_for_string(self):
        """Test that string indexing uses XWNode when available."""
        data = XWData.from_native({"name": "Alice", "age": 30})
        
        # Should work via XWNode delegation
        assert data["name"] == "Alice"
        assert data["age"] == 30

